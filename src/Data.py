import hjson
import binascii
import sys
import shutil
import os
import random

class FILE:
    def __init__(self, data):
        self.data = data
        self.addr = 0

    def readInt(self, size=4):
        value = int.from_bytes(self.data[self.addr:self.addr+size], byteorder='little', signed=True)
        self.addr += size
        return value

    def readString(self, size):
        string = self.data[self.addr:self.addr+size-1].decode()
        self.addr += size
        return string

    def getInt(self, value, size=4):
        return value.to_bytes(size, byteorder='little', signed=True)

    def getString(self, string):
        return string.encode() + b'\x00'

    def patchInt(self, value, addr, size=4):
        valueBytes = self.getInt(value, size=size)
        self.data[addr:addr+size] = valueBytes

    def patchString(self, string, addr):
        stringBytes = self.getString(string)
        size = len(stringBytes)
        self.data[addr:addr+size] = stringBytes


class UASSET(FILE):
    def __init__(self, data):
        super().__init__(data)
        self.load()
        
    def load(self):
        self.entries = {}
        self.idxToName = {}
        self.nameToIdx = {}
        
        self.addr = 0x75
        count = self.readInt(size=4)
        self.addr = 0xbd
        addrFtr2 = self.readInt(size=4)
        # Store header
        self.header = self.data[:0xc1]
        # Load names
        self.addr = 0xc1
        for i in range(count):
            base = self.addr
            size = self.readInt()
            name = self.readString(size)
            key = self.readInt()
            self.nameToIdx[name] = i
            self.idxToName[i] = name
            self.entries[name] = self.data[base:self.addr]
        # Store footers (not sure what they're used for)
        self.footer1 = self.data[self.addr:addrFtr2]
        self.footer2 = self.data[addrFtr2:]

    def build(self):
        self.data = bytearray(self.header)
        count = len(self.idxToName)
        for entry in self.entries.values():
            self.data += entry
        self.data += self.footer1 + self.footer2

    def addToHeader(self, addr, valueToAdd):
        value = int.from_bytes(self.header[addr:addr+4], byteorder='little')
        value += valueToAdd
        self.header[addr:addr+4] = value.to_bytes(4, byteorder='little')
        
    def addToFooter1(self, addr, valueToAdd):
        value = int.from_bytes(self.footer1[addr:addr+8], byteorder='little')
        value += valueToAdd
        self.footer1[addr:addr+8] = value.to_bytes(8, byteorder='little')

    def addEntry(self, entry):
        # Update entry
        name = entry[4:-5].decode()
        if name in self.entries:
            return
        self.entries[name] = entry
        count = len(self.idxToName)
        self.idxToName[count] = name
        self.nameToIdx[name] = count
        # Update header
        length = len(entry)
        self.addToHeader(0x18, length)
        self.addToHeader(0x29, 1)
        self.addToHeader(0x3d, length)
        self.addToHeader(0x45, length)
        self.addToHeader(0x49, length)
        self.addToHeader(0x75, 1)
        self.addToHeader(0xa5, length)
        self.addToHeader(0xbd, length)
        # Update footer
        addr = len(self.footer1) - 0x4c
        self.addToFooter1(addr, length)

    def getName(self, index):
        name = self.idxToName[index & 0xFFFFFFFF]
        index >>= 32
        if index:
            return f"{name}_{index-1}"
        return name    
        
    def getIndex(self, name):
        if name in self.nameToIdx:
            return self.nameToIdx[name]
        nameBase = '_'.join(name.split('_')[:-1])
        if nameBase not in self.nameToIdx:
            sys.exit(f"{nameBase} does not exist in this uasset")
        value = int(name.split('_')[-1]) + 1
        value <<= 32
        value += self.nameToIdx[nameBase]
        return value

    def getEntry(self, name):
        if name in self.entries:
            return self.entries[name]
        # Get name base
        index = self.getIndex(name)
        name = self.idxToName[index & 0xFFFFFFFF]
        # Return entry for the name base
        return self.entries[name]


# NB: This is written specifically for the files used.
class DATA:
    def __init__(self, rom, fileName):
        self.rom = rom
        self.fileName = fileName
        print(f'Loading data from {fileName}')
        # Load data
        self.uasset = UASSET(self.rom.extractFile(f"{self.fileName}.uasset"))
        self.uexp = FILE(self.rom.extractFile(f"{self.fileName}.uexp"))
        # Organize/"parse" uexp data
        self.loadTable()

    def loadTable(self):
        self.uexp.addr = 0x29
        count = self.uexp.readInt()
        self.header = self.uexp.data[:self.uexp.addr]
        self.table = {}
        for _ in range(count):
            # Store address at the start of each row if needed 
            addr = self.uexp.addr
            # Get name of row
            index = self.uexp.readInt(size=8)
            name = self.uasset.getName(index)
            self.table[name] = {}
            # Load entry of table
            while True:
                # Store address at the start of the entry
                base = self.uexp.addr
                # Load the key name
                index = self.uexp.readInt(size=8)
                key = self.uasset.getName(index)
                if key == 'None':
                    break
                # Type of value for the key
                index = self.uexp.readInt(size=8)
                dataType = self.uasset.getName(index)
                # Store the data given the dataType
                if dataType == 'ByteProperty':
                    size = self.uexp.readInt(size=8)
                    self.uexp.addr = base + 0x21 + size
                    # self.uexp.addr = base + 0x22
                elif dataType == 'NameProperty':
                    self.uexp.addr = base + 0x21
                elif dataType == 'BoolProperty':
                    self.uexp.addr = base + 0x1a
                elif dataType == 'IntProperty':
                    self.uexp.addr = base + 0x1d
                elif dataType == 'ObjectProperty':
                    self.uexp.addr = base + 0x1d
                elif dataType == 'TextProperty':
                    size = self.uexp.readInt(size=8)
                    self.uexp.addr += size + 1
                elif dataType == 'EnumProperty':
                    self.uexp.addr = base + 0x29
                elif dataType == 'StructProperty':
                    size = self.uexp.readInt(size=8)
                    self.uexp.addr += size + 0x19
                elif dataType == 'ArrayProperty':
                    self.uexp.addr = base + 0x18
                    index = self.uexp.readInt(size=8)
                    arrayType = self.uasset.getName(index)
                    if arrayType == 'BoolProperty':
                        assert self.uexp.readInt(size=1) == 0
                        arrayLen = self.uexp.readInt(size=4)
                        self.uexp.addr += arrayLen
                    elif arrayType == 'ByteProperty':
                        assert self.uexp.readInt(size=1) == 0
                        arrayLen = self.uexp.readInt(size=4)
                        self.uexp.addr += arrayLen * 8
                    elif arrayType == 'IntProperty':
                        assert self.uexp.readInt(size=1) == 0
                        arrayLen = self.uexp.readInt(size=4)
                        self.uexp.addr += arrayLen * 4
                    elif arrayType == 'NameProperty':
                        assert self.uexp.readInt(size=1) == 0
                        arrayLen = self.uexp.readInt(size=4)
                        self.uexp.addr += arrayLen * 8
                    elif arrayType == 'StrProperty':
                        assert self.uexp.readInt(size=1) == 0
                        arrayLen = self.uexp.readInt(size=4)
                        for _ in range(arrayLen):
                            strSize = self.uexp.readInt(size=4)
                            if strSize < 0:
                                strSize = -strSize * 2
                            self.uexp.addr += strSize
                    elif arrayType == 'StructProperty':
                        self.uexp.addr = base + 0x35
                        arraySize = self.uexp.readInt(size=4)
                        self.uexp.addr = base + 0x56 + arraySize
                    else:
                        sys.exit(f"{arrayType} not yet included in arrays!")
                else:
                    sys.exit(f"{dataType} not yet included!")
                # Store chunk of data in the table
                self.table[name][key] = self.uexp.data[base:self.uexp.addr]
        self.footer = self.uexp.data[self.uexp.addr:]

    def readOffset(self, data, offset, size=1):
        return int.from_bytes(data[offset:offset+size], byteorder='little')

    def readArray(self, name, key):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'ArrayProperty'
        typeId = self.readOffset(data, 24, size=8)
        dataType = self.uasset.getName(typeId)
        if dataType == 'IntProperty':
            size = 4
        elif dataType == 'NameProperty':
            size = 8
        else:
            sys.exit(f"{dataType} not yet included!")
        return [self.readOffset(data, offset, size=size) for offset in range(37, len(data), size)]

    def patchArray(self, name, key, arr):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'ArrayProperty'
        typeId = self.readOffset(data, 24, size=8)
        dataType = self.uasset.getName(typeId)
        if dataType == 'IntProperty':
            size = 4
        elif dataType == 'NameProperty':
            size = 8
        else:
            sys.exit(f"{dataType} not yet included!")
        for i, offset in enumerate(range(37, len(data), size)):
            data[offset:offset+size] = arr[i].to_bytes(size, byteorder='little')

    def readInt(self, name, key):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'IntProperty'
        return self.readOffset(data, 25, size=4)

    def patchInt(self, name, key, value):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'IntProperty'
        assert value < 0x7FFFFFFF
        data[25:] = value.to_bytes(4, byteorder='little', signed=True)

    def readName(self, name, key):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'NameProperty'
        value = self.readOffset(data, 25, size=8)
        return self.uasset.getName(value)

    def patchName(self, name, key, string):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'NameProperty'
        value = self.uasset.getIndex(string)
        data[25:] = value.to_bytes(8, byteorder='little')

    def readBool(self, name, key):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'BoolProperty'
        return self.readOffset(data, 24, size=1) > 0

    def patchBool(self, name, key, value):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'BoolProperty'
        data[24] = value

    def readByte(self, name, key):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'ByteProperty', f"{self.uasset.getName(index)} rather than ByteProperty"
        size = self.readOffset(data, 0x10, size=8)
        if size == 1:
            return data[-1]
        elif size == 8:
            return self.readOffset(data, 0x21, size=8)

    def patchByte(self, name, key, value):
        data = self.table[name][key]
        index = self.readOffset(data, 8, size=8)
        assert self.uasset.getName(index) == 'ByteProperty'
        size = self.readOffset(data, 16, size=8)
        if size == 1:
            data[-1] = value
        elif size == 8:
            data[-8:] = value.to_bytes(8, byteorder='little')
        
    def buildTable(self):
        self.uexp.data = bytearray(self.header)
        noneBytes = self.uexp.getInt(self.uasset.getIndex('None'), size=8)
        for name in self.table:
            index = self.uasset.getIndex(name)
            self.uexp.data += self.uexp.getInt(index, size=8)
            for key in self.table[name]:
                self.uexp.data += self.table[name][key]
            self.uexp.data += noneBytes
        self.uexp.data += self.footer

    def update(self):
        # Build uexp first -- need total size for uasset
        self.buildTable()
        ## Update uasset footer to account for size changes in uexp
        address = len(self.uasset.footer1) - 0x54
        length = len(self.uexp.data) - 4
        self.uasset.footer1[address:address+8] = length.to_bytes(8, byteorder='little')
        # Build uasset
        self.uasset.build()
        # Patch ROM
        self.rom.patchFile(self.uasset.data, f"{self.fileName}.uasset")
        self.rom.patchFile(self.uexp.data, f"{self.fileName}.uexp")

        # ## TEMPORARY STUFF JUST FOR CHECKING
        # dir = os.path.dirname(self.rom.getFullPath(f"{self.fileName}.uasset"))
        # baseUasset = os.path.basename(f"{self.fileName}.uasset")
        # baseUexp = os.path.basename(f"{self.fileName}.uexp")
        # if not os.path.isdir(dir):
        #     os.makedirs(dir)
        # with open(os.path.join(dir, baseUasset), 'wb') as file:
        #     file.write(self.uasset.data)
        # with open(os.path.join(dir, baseUexp), 'wb') as file:
        #     file.write(self.uexp.data)



class SHOPS(DATA):
    def __init__(self, rom):
        super().__init__(rom, 'PurchaseItemTable')

    def perfectKeyItemThievery(self):
        self.patchInt('DesertS_SHOP_FC_01_1', 'ProperSteal', -15) # Aristocrat's Mask
        self.patchInt('DesertS_SHOP_FC_02_1', 'ProperSteal', -15) # Aristocrat's Mask
        self.patchInt('DesertS_SHOP_FC_03_1', 'ProperSteal', -15) # Aristocrat's Mask
        self.patchInt('DesertS_SHOP_FC_10_1', 'ProperSteal', -15) # Black Market Inventory
        self.patchInt('DesertS_SHOP_FC_11_1', 'ProperSteal', -15) # Bottle of Wine
        self.patchInt('PlainM_SHOP_FC_06_1', 'ProperSteal', -15)  # Oasis Water
        self.patchInt('PlainM_SHOP_FC_11_1', 'ProperSteal', -15)  # Crystal Ore
        self.patchInt('PlainM_SHOP_FC_17_1', 'ProperSteal', -15)  # Wyvern Scale
        self.patchInt('SnowM_SHOP_FC_01_1', 'ProperSteal', -15)   # Brigand's Garb
        self.patchInt('SnowM_SHOP_FC_02_1', 'ProperSteal', -15)   # Brigand Leader's Garb


class GAMETEXT(DATA):
    def __init__(self, rom):
        super().__init__(rom, 'GameTextEN')

    def getText(self, name):
        data = self.table[name]['Text']
        return data[0x4b:-1].decode()

    def patchText(self, name, text):
        # Fix apostrophe
        if chr(8217) in text:
            text = text.replace(chr(8217), chr(39))
        # Patch text
        data = self.table[name]['Text']
        textArray = text.encode() + bytearray([0])
        data[0x47:0x4b] = len(textArray).to_bytes(4, byteorder='little')
        data[0x4b:] = textArray

class TALKDATA(DATA):
    def __init__(self, rom):
        super().__init__(rom, 'TalkData_EN')

    def getText(self, name):
        data = self.table[name]['Text']
        return data[0x29:-1].decode()

    def patchText(self, name, text):
        data = self.table[name]['Text']
        textArray = text.encode() + bytearray([0])
        size = len(textArray) + 8
        data[0x10:0x18] = size.to_bytes(8, byteorder='little')
        data[0x25:0x29] = len(textArray).to_bytes(4, byteorder='little')
        data[0x29:] = textArray

class ITEMS(DATA):
    def __init__(self, rom, text):
        super().__init__(rom, 'ItemDB')
        self.text = text

    def getName(self, name):
        itemName = self.readName(name, 'ItemNameID_118_78CF4DCD438E1C10ADEE2D951C83C0BE')
        return self.text.getText(itemName)

    def getBuyPrice(self, name):
        return self.readInt(name, 'BuyPrice_123_321D5A2A48620022767D3BA718CCA37D')


class OBJECTS(DATA):
    def __init__(self, rom):
        super().__init__(rom, 'ObjectData')

    def noThiefChests(self):
        for name in self.table:
            objType = self.readByte(name, 'ObjectType')
            if objType == 3:
                self.patchByte(name, 'ObjectType', 1)
    

class STATS(DATA):
    def __init__(self, rom, path):
        super().__init__(rom, path)

    def readStats(self, key, parameter):
        data = self.table[key][parameter]
        base = 0x31 + 0x19
        stride = 0x1d
        return {
            'HP':   int.from_bytes(data[base+stride*0 :base+stride*0 +4], byteorder='little'),
            'MP':   int.from_bytes(data[base+stride*1 :base+stride*1 +4], byteorder='little'),
            'BP':   int.from_bytes(data[base+stride*2 :base+stride*2 +4], byteorder='little'),
            'SP':   int.from_bytes(data[base+stride*3 :base+stride*3 +4], byteorder='little'),
            'ATK':  int.from_bytes(data[base+stride*4 :base+stride*4 +4], byteorder='little'),
            'DEF':  int.from_bytes(data[base+stride*5 :base+stride*5 +4], byteorder='little'),
            'MATK': int.from_bytes(data[base+stride*6 :base+stride*6 +4], byteorder='little'),
            'MDEF': int.from_bytes(data[base+stride*7 :base+stride*7 +4], byteorder='little'),
            'ACC':  int.from_bytes(data[base+stride*8 :base+stride*8 +4], byteorder='little'),
            'EVA':  int.from_bytes(data[base+stride*9 :base+stride*9 +4], byteorder='little'),
            'CON':  int.from_bytes(data[base+stride*10:base+stride*10+4], byteorder='little'),
            'AGI':  int.from_bytes(data[base+stride*11:base+stride*11+4], byteorder='little'),
        }

    def patchStats(self, key, parameter, stats):
        data = self.table[key][parameter]
        base = 0x31 + 0x19
        stride = 0x1d
        for i, stat in enumerate(stats.values()):
            addr = base + stride*i
            data[addr:addr+4] = stat.to_bytes(4, byteorder='little')


class PC(STATS):
    def __init__(self, rom, items):
        super().__init__(rom, 'PlayableCharacterDB')
        self.items = items

    def startWithSpurningRibbon(self):
        # Add Spurning Ribbon to uasset
        spurRib = self.items.uasset.entries['ITM_AC_041']
        self.uasset.addEntry(spurRib)
        # Add Spurning Ribbon to each PC's backpack
        spurRibIdx = self.uasset.getIndex('ITM_AC_041')
        labelKey = 'FirstBackpackItemLabel_177_20B342894C76B5718269B1ABB6CA89B2'
        countKey = 'FirstBackpackItemCnt_180_F5B228D34F07181C75FCB5A19499A681'
        for i in range(1, 9):
            j = str(i)
            arrLabels = self.readArray(j, labelKey)
            arrCounts = self.readArray(j, countKey)
            k = arrCounts.index(0)
            arrLabels[k] = spurRibIdx
            arrCounts[k] = 1
            self.patchArray(j, labelKey, arrLabels)
            self.patchArray(j, countKey, arrCounts)
        # Change sell price to 0
        self.items.patchInt('ITM_AC_041', 'SellPrice_120_96A9EEEA44B3AF566241D4B1BA68F95C', 0)

    def readStats(self, key):
        return super().readStats(key, 'ParameterRevision_157_2E7BA813425EC911FA5A8AA5D18AF9A8')

    def patchStats(self, key, stats):
        super().patchStats(key, 'ParameterRevision_157_2E7BA813425EC911FA5A8AA5D18AF9A8', stats)


class JOBDATA(STATS):
    def __init__(self, rom, abilityData, talkData):
        super().__init__(rom, 'Database/JobData')
        self.abilityData = abilityData
        self.talkData = talkData
        self.orbText = {
            'Thief': 'CLD_2J0000',
            'Dancer': 'DED_2J0000',
            'Hunter': 'FOD_2J0000',
            'Sorcerer': 'FOD_3J0000',
            'Warrior': 'MOD_2J0000',
            'Runelord': 'MOD_3J0000',
            'Scholar': 'PLD_2J0000',
            'Starseer': 'PLD_3J0000',
            'Apothecary': 'RID_2J0000',
            'Warmaster': 'RID_3J0000',
            'Merchant': 'SED_2J0000',
            'Cleric': 'SND_2J0000',
        }

    def readSupportArray(self, key):
        data = self.table[key]['JobSupportAbility_42_641BDABF417D5189F1230CBD6276F10E']
        size = int.from_bytes(data[0x35:0x3d], byteorder='little')
        none = self.uasset.getIndex('None').to_bytes(8, byteorder='little')
        array = data[-size:].split(none)
        name = []
        for i in range(4):
            x = int.from_bytes(array[i][0x19:0x21], byteorder='little')
            name.append( self.uasset.getName(x) )
        return name

    def patchSupportArray(self, key, name, params=None):
        if not params:
            params = [4, 5, 6, 7]
        # Setup data
        data = self.table[key]['JobSupportAbility_42_641BDABF417D5189F1230CBD6276F10E']
        size = int.from_bytes(data[0x35:0x3d], byteorder='little')
        none = self.uasset.getIndex('None').to_bytes(8, byteorder='little')
        array = data[-size:].split(none)
        # Patch data
        for i in range(4):
            nameIndex = self.uasset.getIndex(name[i])
            array[i][0x19:0x21] = nameIndex.to_bytes(8, byteorder='little')
            array[i][0x3a:0x3e] = params[i].to_bytes(4, byteorder='little')
        data[-size:] = none.join(array)

    def readSupportNames(self, key):
        names = self.readSupportArray(key)
        text = []
        for name in names:
            text.append( self.abilityData.getDisplay(name) )
        return text

    def supportNameQOL(self, key, job):
        names = self.readSupportNames(key)
        text = [f'You unlocked {job} as a secondary job!\nThe passive skills thee shall learn are\n']
        text += names
        text = '\n'.join(text)
        textKey = self.orbText[job]
        self.talkData.patchText(f"TX_OBD_{textKey}_0010", text)
        self.talkData.patchText(f"TX_OBN_{textKey}_0020", ', '.join(names[:2]))
        self.talkData.patchText(f"TX_OBN_{textKey}_0030", ', '.join(names[2:]))

    def readSupportCosts(self, key):
        return self.readArray(key, 'JPCost_41_39D417E148D407A63AC22FA2F9F2FA9A')

    def patchSupportCosts(self, key, costs):
        self.patchArray(key, 'JPCost_41_39D417E148D407A63AC22FA2F9F2FA9A', costs)

    def readStats(self, key):
        return super().readStats(key, 'ParameterRevision_9_5F8998A541B5EAF310E2C9A623913B9A')

    def patchStats(self, key, stats):
        super().patchStats(key, 'ParameterRevision_9_5F8998A541B5EAF310E2C9A623913B9A', stats)


class ABILITYSETS(DATA):
    def __init__(self, rom):
        super().__init__(rom, 'AbilitySetData')
        self.menuIcon = {
            'Physical': self.uasset.getIndex('EABILITY_ICON_TYPE::NewEnumerator1'),
            'Magic': self.uasset.getIndex('EABILITY_ICON_TYPE::NewEnumerator2'),
            'Heal': self.uasset.getIndex('EABILITY_ICON_TYPE::NewEnumerator3'),
            'Status': self.uasset.getIndex('EABILITY_ICON_TYPE::NewEnumerator4'), # ALLY STATUS EFFECTS (including runes)
            'Enemy': self.uasset.getIndex('EABILITY_ICON_TYPE::NewEnumerator5'), # ENEMY STATUS EFFECTS
        }

    def getAbilityNames(self, key):
        return [
            self.readName(key, 'NoBoost_9_5F3694D44FCF934172D38CA963CBDE00'),
            self.readName(key, 'BoostLv1_20_6927B43443FB3CE47121F39DA2C15C22'),
            self.readName(key, 'BoostLv2_21_3FE6D59245093E75F972BF9CA26404E7'),
            self.readName(key, 'BoostLv3_22_456F3637454862D5F56855AF92BD93CD'),
        ]

    def patchAbilityNames(self, key, names):
        assert len(names) == 4
        self.patchName(key, 'NoBoost_9_5F3694D44FCF934172D38CA963CBDE00', names[0])
        self.patchName(key, 'BoostLv1_20_6927B43443FB3CE47121F39DA2C15C22', names[1])
        self.patchName(key, 'BoostLv2_21_3FE6D59245093E75F972BF9CA26404E7', names[2])
        self.patchName(key, 'BoostLv3_22_456F3637454862D5F56855AF92BD93CD', names[3])

    def patchMenuIcon(self, key, icon):
        self.patchByte(key, 'MenuIconType_26_AB552CEC45AFB2EAEBA942AF66BD2DF0', self.menuIcon[icon])

# INCLUDE GAMETEXT??
class ABILITYDATA(DATA):
    def __init__(self, rom, gameText):
        super().__init__(rom, 'Database/AbilityData')
        self.gameText = gameText
        self.weaponTypes = {
            'sword': self.uasset.getIndex('EWEAPON_CATEGORY::NewEnumerator0'),
            'polearm': self.uasset.getIndex('EWEAPON_CATEGORY::NewEnumerator1'),
            'dagger': self.uasset.getIndex('EWEAPON_CATEGORY::NewEnumerator2'),
            'axe': self.uasset.getIndex('EWEAPON_CATEGORY::NewEnumerator3'),
            'bow': self.uasset.getIndex('EWEAPON_CATEGORY::NewEnumerator4'),
            'staff': self.uasset.getIndex('EWEAPON_CATEGORY::NewEnumerator5'),
        }
        self.typeToWeapon = {v:k for k,v in self.weaponTypes.items()}
        self.costSpIndex = self.uasset.getIndex('EABILITY_COST_TYPE::NewEnumerator1')

    def scaleVetsCost(self, scale):
        display = self.getDisplay('BT_ABI_471')
        if display == 'Veteran Soldier':
            cost = self.readInt('BT_ABI_471', 'CostValue_122_F172DCF14B88805221987480B8CE3E0A')
            cost *= scale
            self.patchInt('BT_ABI_471', 'CostValue_122_F172DCF14B88805221987480B8CE3E0A', cost)
            self.patchInt('BT_ABI_472', 'CostValue_122_F172DCF14B88805221987480B8CE3E0A', cost)
            self.patchInt('BT_ABI_473', 'CostValue_122_F172DCF14B88805221987480B8CE3E0A', cost)
            self.patchInt('BT_ABI_474', 'CostValue_122_F172DCF14B88805221987480B8CE3E0A', cost)
        
    def getWeapon(self, key):
        if self.readBool(key, 'DependWeapon_142_EAFB8A4C423075211DFA71943E77D7E1'):
            return self.typeToWeapon[self.readByte(key, 'RestrictWeapon_149_6B9AD27C4CCDCAD2BFA058B6FCAD4141')]
        return False
        
    def patchWeapon(self, key, weapon):
        self.patchByte(key, 'RestrictWeapon_149_6B9AD27C4CCDCAD2BFA058B6FCAD4141', self.weaponTypes[weapon])

    def getSP(self, key):
        return self.readInt(key, 'CostValue_122_F172DCF14B88805221987480B8CE3E0A')
        
    def patchSP(self, key, cost):
        self.patchInt(key, 'CostValue_122_F172DCF14B88805221987480B8CE3E0A', cost)
        self.patchByte(key, 'CostType_135_2A40421442DD635630B730BADB6816CA', self.costSpIndex)

    def getRatio(self, key):
        return self.readInt(key, 'AbilityRatio_151_D3DF37E443ADA8AB346895979350AB0B')
        
    def patchRatio(self, key, ratio):
        self.patchInt(key, 'AbilityRatio_151_D3DF37E443ADA8AB346895979350AB0B', ratio)

    def getDetail(self, key):
        detailName = self.readName(key, 'Detail_4_53AE223B402C375F484BDDBC10501FA3')
        return self.gameText.getText(detailName)
        
    def patchDetail(self, key, detail):
        detailName = self.readName(key, 'Detail_4_53AE223B402C375F484BDDBC10501FA3')
        self.gameText.patchText(detailName, detail)

    def getDetailName(self, key):
        return self.readName(key, 'Detail_4_53AE223B402C375F484BDDBC10501FA3')

    def patchDetailName(self, key, name):
        self.patchName(key, 'Detail_4_53AE223B402C375F484BDDBC10501FA3', name)

    def getDisplayName(self, key):
        return self.readName(key, 'DisplayName_2_2B3FEB134F597EA30A348FA0C363502D')

    def getDisplay(self, key):
        displayName = self.getDisplayName(key)
        return self.gameText.getText(displayName)
        
    def patchPhysicalDetail(self, key, oldWeapon, newWeapon):
        # No changes needed
        if oldWeapon == newWeapon:
            return
        detail = self.getDetail(key)
        if oldWeapon not in detail:
            return

        # Setup string to find and replaced
        if 'a ' in oldWeapon in detail:
            oldWeapon = 'a '+oldWeapon
            if newWeapon == 'axe':
                newWeapon = 'an '+newWeapon
            else:
                newWeapon = 'a '+newWeapon
        elif 'an axe' in detail:
            newWeapon = 'a '+newWeapon
            oldWeapon = 'an axe'

        # Update and patch detail
        detail = detail.replace(oldWeapon, newWeapon)
        self.patchDetail(key, detail)
