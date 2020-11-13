import hjson
import binascii
import sys
import shutil

class UASSET:
    def __init__(self, filename):
        self.filename = filename.split('/')[-1]
        with open(filename, 'rb') as file:
            self.data = bytearray(file.read())
        
        self.loadTable()
        self.mappingToName = {}
        self.mappingToIndex = {}
        for i, name in enumerate(self.entries.keys()):
            self.mappingToName[i] = name
            self.mappingToIndex[name] = i

    def loadTable(self):
        self.header = self.data[:0xc1]
        data = self.data[0xc1:]
        self.entries = {}
        numEntries = int.from_bytes(self.header[0x75:0x75+2], byteorder='little')
        while numEntries > 0:
            size = int.from_bytes(data[0:4], byteorder='little')
            entry = data[:size+8]
            name = ''.join(map(chr, entry[4:4+size-1]))
            self.entries[name] = entry
            data = data[size+8:]
            numEntries -= 1
        self.footer = data

    def entryExists(self, name):
        return name in self.mappingToIndex

    def addToHeader(self, address, valueToAdd):
        value = int.from_bytes(self.header[address:address+4], byteorder='little')
        value += valueToAdd
        self.header[address:address+4] = value.to_bytes(4, byteorder='little')
        
    def addToFooter(self, address, valueToAdd):
        value = int.from_bytes(self.footer[address:address+8], byteorder='little')
        value += valueToAdd
        self.footer[address:address+8] = value.to_bytes(8, byteorder='little')
        
    def addEntry(self, data):
        size = int.from_bytes(data[:4], byteorder='little')
        name = ''.join(map(chr, data[4:4+size-1]))
        self.entries[name] = data
        ## UPDATE HEADER
        length = len(data)
        self.addToHeader(0x18, length)
        self.addToHeader(0x29, 1)
        self.addToHeader(0x3d, length)
        self.addToHeader(0x45, length)
        self.addToHeader(0x49, length)
        self.addToHeader(0x75, 1)
        self.addToHeader(0xa5, length)
        self.addToHeader(0xbd, length)
        ## UPDATE FOOTER
        address = len(self.footer) - 0x58
        self.addToFooter(address, length)
        ## UPDATE MAPPING
        entryIndex = len(self.entries.keys()) - 1
        self.mappingToName[entryIndex] = name
        self.mappingToIndex[name] = entryIndex
        
    def buildTable(self):
        self.data = list(self.header)
        for entry in self.entries.values():
            self.data += entry
        self.data += self.footer

    def printList(self):
        for i, name in self.mappingToName.items():
            index = str(binascii.hexlify(i.to_bytes(2, byteorder='little')))[2:-1]
            print(index, name)


class UEXP:
    def __init__(self, filename, uasset):
        self.filename = filename.split('/')[-1]
        with open(filename, 'rb') as file:
            self.data = bytearray(file.read())
        
        self.uasset = uasset
        self.noneValue = self.getValue('None')
        self.loadTable()

    def getValue(self, name):
        if name in self.uasset.mappingToIndex:
            return self.uasset.mappingToIndex[name]
        # PRIMARILY FOR "ITM_1??"
        checkName = '_'.join(name.split('_')[:-1])
        if checkName not in self.uasset.mappingToIndex:
            return -1
        value = int(name.split('_')[-1]) + 1
        value <<= 32
        value += self.uasset.mappingToIndex[checkName]
        return value

    def getName(self, value):
        name = self.uasset.mappingToName[value & 0xFFFFFFFF]
        value >>= 32
        if value == 0: return name
        return f"{name}_{value-1}"

    def changeValue(self, slot, key, value):
        entry = self.entries[slot]
        address = entry[key]['offset']
        size = entry[key]['size']
        entry['data'][address:address+size] = value.to_bytes(size, byteorder='little', signed=True)

    def changeAllValues(self, key, name):
        for slot in self.entries.keys():
            self.changeValue(slot, key, name)
        
    def readData(self, size):
        value = int.from_bytes(self.data[self.address:self.address+size], byteorder='little')
        self.address += size
        return value

    def loadTable(self):
        self.address = 0x29
        numEntries = self.readData(4)
        self.header = self.data[:self.address]
        self.entries = {}
        while numEntries > 0:
            # Store base address for any offset calculations in an entry
            base = self.address
            # Read key
            value = self.readData(8)
            key = self.getName(value)
            self.entries[key] = {}
            # Read next value until None (end of entry)
            # MAYBE START FUNCTION CALLING HERE?????
            value = self.readData(8)
            while value != self.noneValue:
                # Read keys within the object
                name = self.getName(value) # EG: ObjectType, IsMoney, Reset, Text
                self.entries[key][name] = {}
                # Read property of the key's value
                nextValueType = self.readData(8)
                typeName = self.getName(nextValueType)
                self.entries[key][name]['type'] = typeName
                if typeName == 'ByteProperty':
                    size = self.readData(8)
                    self.entries[key][name]['size'] = size
                    self.readData(8) # Always "None"
                    self.address += 1 # Offset for value
                    self.entries[key][name]['offset'] = self.address - base
                    self.entries[key][name]['value'] = self.readData(size)          ## WHAT IF MORE THAN SIZE=1? WOULD ARRAY OF BYTES MAKE MORE SENSE???
                    self.entries[key][name]['name'] = self.entries[key][name]['value']  # Might ne necessary for 'EnumProperty'. Included here only for completeness.
                elif typeName == 'BoolProperty':
                    self.address += 8 # Is this always 0? Presumably an array of bools rather than nonzero?
                    self.entries[key][name]['offset'] = self.address - base
                    self.entries[key][name]['value'] = True if self.readData(1) else False
                    self.entries[key][name]['name'] = self.entries[key][name]['value'] # Just for completeness
                    self.address += 1
                elif typeName == 'IntProperty':
                    size = self.readData(8)
                    self.entries[key][name]['size'] = size
                    self.address += 1
                    self.entries[key][name]['offset'] = self.address - base
                    self.entries[key][name]['value'] = self.readData(size)
                    self.entries[key][name]['name'] = self.entries[key][name]['value'] # Just for completeness
                elif typeName == 'NameProperty':
                    size = self.readData(8)
                    self.entries[key][name]['size'] = size
                    self.address += 1 # Offset for value
                    self.entries[key][name]['offset'] = self.address - base
                    value = self.readData(size)
                    self.entries[key][name]['value'] = value
                    self.entries[key][name]['name'] = self.getName(value)
                elif typeName == 'EnumProperty':
                    size = self.readData(8)
                    self.entries[key][name]['size'] = size
                    enumTypeValue = self.readData(8)               # I see no need to store this.
                    enumTypeName = self.getName(enumTypeValue)
                    self.address += 1 # Offset for value
                    self.entries[key][name]['offset'] = self.address - base
                    enumTypeValue = self.readData(size)
                    enumTypeName = self.getName(enumTypeValue)
                    self.entries[key][name]['value'] = enumTypeValue
                    self.entries[key][name]['name'] = self.getName(enumTypeValue)   # Is storing this necessary???
                elif typeName == 'TextProperty':
                    size = self.readData(8)
                    self.address += 1
                    self.entries[key][name]['offset'] = self.address - base
                    self.entries[key][name]['value'] = self.data[self.address:self.address+size]
                    self.address += size
                elif typeName == 'ArrayProperty':
                    size = self.readData(8)
                    self.entries[key][name]['size'] = size
                    arrayTypeValue = self.readData(8)
                    self.entries[key][name]['ArrayType'] = self.getName(arrayTypeValue)
                    self.address += 1
                    self.entries[key][name]['offset'] = self.address - base
                    self.entries[key][name]['value'] = self.data[self.address:self.address + size] # Write a separate function for doing something with this data?
                    self.address += size
                else:
                    print(f'{typeName} not yet included!')
                    sys.exit()
                value = self.readData(8)
            self.entries[key]['data'] = self.data[base:self.address]
            numEntries -= 1
        self.footer = self.data[self.address:]


    def buildTable(self):
        self.data = list(self.header)
        for entry in self.entries.values():
            self.data += entry['data']
        self.size = len(self.data)
        self.data += self.footer
        

class DATA:
    def __init__(self, path, filename):
        self.filename = f"{path}/{filename}"
        self.uasset = UASSET(f"{self.filename}.uasset")
        self.uexp = UEXP(f"{self.filename}.uexp", self.uasset)

    def entryExists(self, name):
        return self.uasset.entryExists(name)
        
    def addEntry(self, entry):
        self.uasset.addEntry(entry)

    def changeValue(self, slot, key, value):
        self.uexp.changeValue(slot, key, value)

    def changeName(self, slot, key, name):
        value = self.uexp.getValue(name)
        self.uexp.changeValue(slot, key, value)
        
    # def changeAllValues(self, key, name):
    #     self.uexp.changeAllValues(key, name)

    def update(self):
        # Build uexp first -- need total size for uasset
        self.uexp.buildTable()
        ## Update uasset footer to account for size changes in uexp
        address = len(self.uasset.footer) - 0x60
        self.uasset.footer[address:address+8] = self.uexp.size.to_bytes(8, byteorder='little')
        # Build uasset
        self.uasset.buildTable()

    def dump(self):
        with open(f"{self.filename}.uasset", 'wb') as file:
            file.write(bytearray(self.uasset.data))
        with open(f"{self.filename}.uexp", 'wb') as file:
            file.write(bytearray(self.uexp.data))

    def dumpJSON(self, path):
        entries = self.uexp.entries.copy()
        for key, value in entries.items():
            del value['data']
        with open(f"{self.filename}.json", 'w') as file:
            hjson.dump(self.uexp.entries, file)


class TEXTDATA(DATA):
    def __init__(self, path, filename):
        super().__init__(path, filename)

    def changeValue(self, slot, string):
        data = self.uexp.entries[slot]['data']
        # Get offsets and sizes
        base = self.uexp.entries[slot]['Text']['offset'] - 9
        size = int.from_bytes(data[base:base+8], byteorder='little')
        keySizeOffset = base + 18
        keySize = int.from_bytes(data[keySizeOffset:keySizeOffset+4], byteorder='little')
        stringSizeOffset = keySizeOffset + 4 + keySize
        stringSize = int.from_bytes(data[stringSizeOffset:stringSizeOffset+4], byteorder='little')
        stringOffset = stringSizeOffset + 4
        endOffset = stringOffset + stringSize
        # New string
        newString = bytearray(map(ord, string)) + bytearray([0])
        newStringSize = len(newString)
        # Update sizes
        change = newStringSize - stringSize
        data[base:base+8] = (size+change).to_bytes(8, byteorder='little')
        data[stringSizeOffset:stringSizeOffset+4] = newStringSize.to_bytes(4, byteorder='little')
        # Insert string
        self.uexp.entries[slot]['data'] = data[:stringOffset] + newString + data[endOffset:]


class TALKDATA(DATA):
    def __init__(self, path, filename):
        super().__init__(path, filename)

    def changeText(self, slot, stringList):
        data = self.uexp.entries[slot]['data']
        # Get offsets and sizes
        arraySizeOffset = self.uexp.entries[slot]['Text']['offset']
        arraySize = int.from_bytes(data[arraySizeOffset:arraySizeOffset+4], byteorder='little')
        base = arraySizeOffset - 17
        totalSize = int.from_bytes(data[base:base+8], byteorder='little')
        offset = arraySizeOffset + 4
        oldArraySize = 0
        num = arraySize
        while num > 0:
            size = int.from_bytes(data[offset:offset+4], byteorder='little')
            offset += 4 + size
            oldArraySize += 4 + size
            num -= 1
        endOffset = offset
        # New strings
        newLength = len(stringList)
        array = newLength.to_bytes(4, byteorder='little')
        newArraySize = 4
        for string in stringList:
            x = bytearray(map(ord, string)) + bytearray([0])
            size = len(x)
            newArraySize += size
            array += size.to_bytes(4, byteorder='little')
            array += x
        # Update total size
        newTotalSize = totalSize + newArraySize - oldArraySize
        data[base:base+8] = newTotalSize.to_bytes(8, byteorder='little')
        # Insert new string
        self.uexp.entries[slot]['data'] = data[:arraySizeOffset] + array + data[endOffset:]

    def changeReset(self, slot, boolValue):
        offset = self.uexp.entries[slot]['Reset']['offset']
        self.uexp.entries[slot]['data'][offset+4] = boolValue
