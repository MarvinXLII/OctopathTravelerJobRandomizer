class TEXT:
    def __init__(self, uexp, uasset):
        self.uexp = uexp
        self.uasset = uasset
        self.totalChange = 0
        self.totalOffset = 0x16
        self.lengthOffset = self.totalOffset + 0x37
        self.stringOffset = self.lengthOffset + 0x4

    def splitUEXP(self):
        idx = 0x2f
        self.lst = [self.uexp[:idx]]
        while idx + 0x42 < len(self.uexp):
            i = idx
            # Get size of entry
            i += self.totalOffset
            size = self.read(self.uexp, i, 2)
            i += size + 0x13
            self.lst.append(self.uexp[idx:i])
            idx = i
        self.lst.append(self.uexp[idx:])

    def printAllText(self):
        for li in self.lst[1:-1]:
            if li[0x16] == 5:
                print('')
            else:
                size = li[self.lengthOffset]
                print(li[self.stringOffset:self.stringOffset+size])

    def findStringIndex(self, string):
        string = string.encode('ascii')
        for i, li in enumerate(self.lst):
            if string in li: return i
        return -1

    def read(self, data, offset, size):
        return int.from_bytes(data[offset:offset+size], 'little')

    def write(self, data, value, offset, size):
        while size > 0:
            data[offset] = value & 0xff
            value >>= 8
            offset += 1
            size -= 1

    def changeString(self, idx, targetSubstring, newSubstring):
        target = targetSubstring.encode('ascii')
        if target not in self.lst[idx]: return
        new = newSubstring.encode('ascii')
        self.lst[idx] = self.lst[idx].replace(target, new)
        change = len(newSubstring) - len(targetSubstring)
        # Update string length
        self.lst[idx][self.lengthOffset] += change
        # Update block length (hash + string)
        size = change + self.read(self.lst[idx], self.totalOffset, 2)
        self.write(self.lst[idx], size, self.totalOffset, 2)
        # Update length change in uasset
        total = change + self.read(self.uasset, 0x53e4a, 3)
        self.write(self.uasset, total, 0x53e4a, 3)
                
    def mergeUEXP(self):
        self.uexp = b''.join(self.lst)


def updateText(abilities):

    path = './Octopath_Traveler/Content/GameText/Database'
    with open(f"{path}/GameTextEN.uexp", 'rb') as file:
        uexp = bytearray(file.read())
    with open(f"{path}/GameTextEN.uasset", 'rb') as file:
        uasset = bytearray(file.read())    

    # Load all sections somehow
    text = TEXT(uexp, uasset)
    text.splitUEXP()

    # Title screen
    text.changeString(9395, "PRESS ANY BUTTON", "RANDOMIZER")

    def genTargetString(skill):
        string = f"{abilities[skill].weapon}".lower()
        if string[0] == 'a':
            return f"an {string}"
        else:
            return f"a {string}"
    
    # WEAPON SWAPS -- Thief
    string = genTargetString('HP Thief')
    for i in range(4):
        text.changeString(1109+i, "a dagger", string)

    string = genTargetString('Steal SP')
    for i in range(4):
        text.changeString(1121+i, "a dagger", string)

    string = genTargetString('Aebers Reckoning')
    text.changeString(1132, "a dagger", string)

    # WEAPON SWAPS -- Warrior
    string = genTargetString('Level Slash')
    for i in range(4):
        text.changeString(1137+i, "a sword", string)

    string = genTargetString('Spearhead')
    for i in range(4):
        text.changeString(1145+i, "a polearm", string)

    string = genTargetString('Cross Strike')
    for i in range(4):
        text.changeString(1153+i, "a sword", string)

    string = genTargetString('Thousand Spears')
    for i in range(4):
        text.changeString(1161+i, "a polearm", string)

    string = f"{abilities['Brands Thunder'].weapon}".lower()
    text.changeString(1168, "sword", string)

    # WEAPON SWAPS -- Hunter
    string = genTargetString('Rain of Arrows')
    for i in range(4):
        text.changeString(1173+i, "a bow", string)

    string = genTargetString('True Strike')
    for i in range(4):
        text.changeString(1177+i, "a bow", string)

    string = genTargetString('Mercy Strike')
    for i in range(4):
        text.changeString(1189+i, "a bow", string)

    string = genTargetString('Arrowstorm')
    for i in range(4):
        text.changeString(1193+i, "a bow", string)

    string = f"{abilities['Draefendis Rage'].weapon}".lower()
    text.changeString(1204, "bow", string)

    # WEAPON SWAPS -- Apothecary
    string = genTargetString('Amputation')
    for i in range(4):
        text.changeString(1325+i, "an axe", string)

    string = genTargetString('Last Stand')
    for i in range(4):
        text.changeString(1341+i, "an axe", string)

    # WEAPON SWAPS -- Warmaster
    string = f"{abilities['Guardian Liondog'].weapon}".lower()
    for i in range(4):
        text.changeString(1353+i, "sword", string)

    string = genTargetString('Tiger Rage')
    for i in range(4):
        text.changeString(1357+i, "an axe", string)

    string = genTargetString('Qilins Horn')
    for i in range(4):
        text.changeString(1361+i, "a polearm", string)

    string = genTargetString('Yatagarasu')
    for i in range(4):
        text.changeString(1365+i, "a dagger", string)

    string = genTargetString('Fox Spirit')
    for i in range(4):
        text.changeString(1369+i, "a staff", string)

    string = genTargetString('Phoenix Storm')
    for i in range(4):
        text.changeString(1373+i, "a bow", string)

    # WEAPON SWAPS -- Sorcerer
    string = f"{abilities['Elemental Break'].weapon}".lower()
    text.changeString(1413, "staff", string)

    text.mergeUEXP()
    with open(f"{path}/GameTextEN.uexp", 'wb') as file:
        file.write(text.uexp)
    with open(f"{path}/GameTextEN.uasset", 'wb') as file:
        file.write(text.uasset)
