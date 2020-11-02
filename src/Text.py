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
            # size = int.from_bytes(self.uexp[i:i+2], 'little')
            size = self.read(self.uexp, i, 2)
            if size == 5: ## IS THIS NEEDED?????
                i += 0x18
            else:
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
            if string in li:
                print(i)
                return i
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
        self.lst[idx][self.lengthOffset] += change
        size = change + self.read(self.lst[idx], self.totalOffset, 2)
        self.write(self.lst[idx], size, self.totalOffset, 2)
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
    
    # WEAPON REMAPPING -- Thief
    # idx = text.findStringIndex("Attack a single foe twice with a dagger, and steal HP equivalent to half of the damage dealt.")
    string = genTargetString('HP Thief')
    for i in range(4):
        text.changeString(1109+i, "a dagger", string)

    # idx = text.findStringIndex("Attack a single foe twice with a dagger, and steal SP equivalent to 5% of damage dealt.")
    string = genTargetString('Steal SP')
    for i in range(4):
        text.changeString(1121+i, "a dagger", string)

    # idx = text.findStringIndex("[Divine Skill] Attack all foes with a dagger, dealing damage proportional to your speed.")
    string = genTargetString('Aebers Reckoning')
    text.changeString(1132, "a dagger", string)

    # # WEAPON REMAPPING -- Warrior
    # idx = text.findStringIndex("Attack all foes with a sword.")
    string = genTargetString('Level Slash')
    for i in range(4):
        text.changeString(1137+i, "a sword", string)

    # idx = text.findStringIndex("Attack a single foe with a polearm, and act earlier on your next turn.")
    string = genTargetString('Spearhead')
    for i in range(4):
        text.changeString(1145+i, "a polearm", string)

    # idx = text.findStringIndex("Unleash a sword attack on a single foe.")
    string = genTargetString('Cross Strike')
    for i in range(4):
        text.changeString(1153+i, "a sword", string)

    # idx = text.findStringIndex("Attack random foes with a polearm 5 to 10 times.")
    string = genTargetString('Thousand Spears')
    for i in range(4):
        text.changeString(1161+i, "a polearm", string)

    # idx = text.findStringIndex("[Divine Skill] Unleash a tremendously powerful sword attack on a single foe.")
    string = f"{abilities['Brands Thunder'].weapon}".lower()
    text.changeString(1168, "sword", string)

    # WEAPON REMAPPING -- Hunter
    # idx = text.findStringIndex("Attack random foes 5 to 8 times with a bow.")
    string = genTargetString('Rain of Arrows')
    for i in range(4):
        text.changeString(1173+i, "a bow", string)

    # idx = text.findStringIndex("Deal critical damage with a bow to a single foe.")
    string = genTargetString('True Strike')
    for i in range(4):
        text.changeString(1177+i, "a bow", string)

    # idx = text.findStringIndex("Attack a single foe with a bow. Otherwise lethal attacks will instead leave the target with 1 HP.")
    string = genTargetString('Mercy Strike')
    for i in range(4):
        text.changeString(1189+i, "a bow", string)

    # idx = text.findStringIndex("Attack all foes 5 to 8 times with a bow.")
    string = genTargetString('Arrowstorm')
    for i in range(4):
        text.changeString(1193+i, "a bow", string)

    # idx = text.findStringIndex("[Divine Skill] Unleash a highly powerful bow attack on all foes.")
    string = f"{abilities['Draefendis Rage'].weapon}".lower()
    text.changeString(1204, "bow", string)

    # WEAPON REMAPPING -- Apothecary
    # idx = text.findStringIndex("Unleash an axe attack on a single foe.")
    string = genTargetString('Amputation')
    for i in range(4):
        text.changeString(1325+i, "an axe", string)

    # idx = text.findStringIndex("Attack all foes with an axe, dealing damage inversely proportional to your current HP.")
    string = genTargetString('Last Stand')
    for i in range(4):
        text.changeString(1341+i, "an axe", string)

    # WEAPON REMAPPING -- Warmaster
    # idx = text.findStringIndex("Unleash 5 to 10 sword attacks against random foes.")
    string = f"{abilities['Guardian Liondog'].weapon}".lower()
    for i in range(4):
        text.changeString(1353+i, "sword", string)

    # idx = text.findStringIndex("Unleash an axe attack on all foes.")
    string = genTargetString('Tiger Rage')
    for i in range(4):
        text.changeString(1357+i, "an axe", string)

    # idx = text.findStringIndex("Unleash a polearm attack on a single foe.")
    string = genTargetString('Qilins Horn')
    for i in range(4):
        text.changeString(1361+i, "a polearm", string)

    # idx = text.findStringIndex("Unleash a dagger attack on all foes.")
    string = genTargetString('Yatagarasu')
    for i in range(4):
        text.changeString(1365+i, "a dagger", string)

    # idx = text.findStringIndex("Unleash a staff attack on all foes.")
    string = genTargetString('Fox Spirit')
    for i in range(4):
        text.changeString(1369+i, "a staff", string)

    # idx = text.findStringIndex("Unleash a bow attack on a single foe.")
    string = genTargetString('Phoenix Storm')
    for i in range(4):
        text.changeString(1373+i, "a bow", string)

    # WEAPON REMAPPING -- Sorcerer
    # idx = text.findStringIndex("Unleash a powerful staff attack on a single foe that also reduces the target's elemental defense for 2 turns.")
    string = f"{abilities['Elemental Break'].weapon}".lower()
    text.changeString(1413, "staff", string)

    text.mergeUEXP()
    with open(f"{path}/GameTextEN.uexp", 'wb') as file:
        file.write(text.uexp)
    with open(f"{path}/GameTextEN.uasset", 'wb') as file:
        file.write(text.uasset)
