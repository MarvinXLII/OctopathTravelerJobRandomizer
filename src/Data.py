import hjson

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

    def print(self):
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
        self.header = self.data[:0x2d]
        self.entries = {}
        self.address = 0x2d
        while self.address < len(self.data)-5:
            base = self.address
            value = self.readData(8)
            key = self.getName(value)
            self.entries[key] = {}
            value = self.readData(8)
            while value != self.noneValue:
                name = self.getName(value)
                self.entries[key][name] = {}
                nextValueType = self.readData(8)
                typeName = self.getName(nextValueType)
                self.entries[key][name]['type'] = nextValueType
                nextValueSize = self.readData(8)
                ## PROPERTIES ARE LIKEY INCOMPLETE
                if typeName == 'ByteProperty':
                    tmp = self.readData(8)
                    assert tmp == self.noneValue, "Error in ByteProperty"
                    ## WHY AM I NOT STORING ANY VALUES HERE??????
                    ## I'M PRETTY SURE I NEED TO STORE SOMETHING!
                if typeName == 'BoolProperty':
                    self.entries[key][name]['size'] = 2
                    assert nextValueSize == 0, "Error in BoolProperty"
                    self.entries[key][name]['offset'] = self.address - base
                    nextValue = self.readData(2)
                    self.entries[key][name]['value'] = nextValue
                else:
                    self.entries[key][name]['size'] = nextValueSize
                    self.address += 1
                    self.entries[key][name]['offset'] = self.address - base
                    nextValue = self.readData(nextValueSize)
                    self.entries[key][name]['value'] = nextValue
                value = self.readData(8)
            self.entries[key]['data'] = self.data[base:self.address]
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

    def dump(self, path):
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
        offset = self.uexp.entries[slot]['Text']['offset']
        # Skip key
        keySize = data[offset+9]
        offset += 9 + 4 + keySize
        # String sizes
        newString = bytearray(map(ord, string)) + bytearray([0])
        newStringSize = len(newString)
        oldStringSize = int.from_bytes(data[offset:offset+4], byteorder='little')
        data[offset:offset+4] = newStringSize.to_bytes(4, byteorder='little')
        offset += 4
        # Overwrite old string with new string
        self.uexp.entries[slot]['data'] = data[:offset] + newString + data[offset+oldStringSize:]
        # Update new size of key + string
        offset = self.uexp.entries[slot]['Text']['offset'] - 9
        oldSize = int.from_bytes(data[offset:offset+4], byteorder='little')
        newSize = oldSize + newStringSize - oldStringSize
        self.uexp.entries[slot]['data'][offset:offset+4] = newSize.to_bytes(4, byteorder='little')
