import random
import ROM
import hjson
import os
from Utilities import get_filename

## Load offset
filename = get_filename('./data/ObjData_offsets.json')
with open(filename, 'r') as file:
    offsets = hjson.load(file)

class ITEMS:
    def __init__(self, base, data):
        self.base = base
        self.data = data

        self.key = self.read('keys')
        self.objType = self.read('ObjType')
        self.objResLabel = self.read('ObjResLabel')    # NEEDED FOR FUTURE ORB SHUFFLE???
        self.isMoney = self.read('IsMoney')
        self.haveItemCnt = self.read('HaveItemCnt')
        self.haveItemLabel = self.read('HaveItemLabel')

        if self.objType == 0:
            self.case = 'Orb'
        elif self.objType == 4:
            self.case = 'Hidden'
        else:
            self.case = 'Chest'

    def read(self, label):
        offset = offsets[label]['offset']
        size = offsets[label]['size']
        return ROM.read(self.data, self.base, offset, 1, size, 1)

    def write(self, label, lst):
        offset = offsets[label]['offset']
        size = offsets[label]['size']
        return ROM.write(self.data, lst, self.base, offset, 1, size)

    def patch(self):
        self.write('ObjType', self.objType)
        self.write('ObjResLabel', self.objResLabel)
        self.write('IsMoney', self.isMoney)
        self.write('HaveItemCnt', self.haveItemCnt)
        self.write('HaveItemLabel', self.haveItemLabel)


def noThiefChests(items):
    for item in items:
        if item.case != 'Chest': continue
        if item.objType != 3: continue
        item.objType = 1

def shuffleAll(items):
    candidates = []
    for item in items:
        if item.case == 'Orb': continue
        candidates.append([item.isMoney, item.haveItemCnt, item.haveItemLabel])
    random.shuffle(candidates)
    slots = filter(lambda x: x.case != 'Orb', items)
    for candidate, slot in zip(candidates, slots):
        slot.isMoney = candidate[0]
        slot.haveItemCnt = candidate[1]
        slot.haveItemLabel = candidate[2]

def shuffleSubset(items, case):
    candidates = []
    for item in items:
        if item.case != case: continue
        candidates.append(list([item.isMoney, item.haveItemCnt, item.haveItemLabel]))
    random.shuffle(candidates)
    slots = filter(lambda x: x.case == case, items)
    for candidate, slot in zip(candidates, slots):
        slot.isMoney = candidate[0]
        slot.haveItemCnt = candidate[1]
        slot.haveItemLabel = candidate[2]

def shuffleItems(filename, settings, outdir):

    with open(filename, 'rb') as file:
        data = bytearray(file.read())

    items = []
    size = 13*16+15
    address = 0x2d
    while address < 0x30e60:
        items.append( ITEMS(address, data) )
        address += size

    ############
    # SETTINGS #
    ############

    # No thief chests
    if settings['no-thief-chests']:
        noThiefChests(items)

    ###################
    # RANODMIZE STUFF #
    ###################


    # Shuffle items
    if settings['items']:
        seed = settings['seed']
        random.seed(seed)
        if settings['items-option'] == 'items-all':
            shuffleAll(items)
        elif settings['items-option'] == 'items-separate':
            shuffleSubset(items, 'Hidden')
            shuffleSubset(items, 'Chest')

    ##################
    # PATCH AND DUMP #
    ##################

    for item in items:
        item.patch()

    with open(filename, 'wb') as file:
        file.write(data)

    #############
    # PRINT LOG #
    #############

    with open(get_filename('data/ObjData.json'),'r') as file:
        objdata = hjson.load(file)

    with open(get_filename('data/items.json'),'r') as file:
        nameItems = hjson.load(file)

    hidden = objdata['hidden']
    chests = objdata['chest']
    
    logfile = f'{outdir}/spoiler_items.log'
    if os.path.exists(logfile): os.remove(logfile)
    with open(logfile, 'w') as file:
        file.write('==============\n')
        file.write(' HIDDEN ITEMS \n')
        file.write('==============\n')
        file.write('\n\n')

        hiddenItems = filter(lambda x: x.case == 'Hidden', items)
        chestItems = filter(lambda x: x.case == 'Chest', items)
        
        region = ''
        place = ''
        for item in hiddenItems:
            key = str(item.key)
            if region != hidden[key]['region']:
                file.write('\n\n')
                region = hidden[key]['region']
                file.write(region+'\n')
                file.write('-'*len(region))
                file.write('\n\n')

            if place != hidden[key]['place']:
                file.write('\n')
                place = hidden[key]['place']
            string = ' '*5 + hidden[key]['place'].ljust(30) + ' '*5
            string += hidden[key]['item'].rjust(30)
            string += ' <-- '
            if item.isMoney:
                string += f"{item.haveItemCnt} leaves".ljust(30)
            else:
                string += nameItems[str(item.haveItemLabel)]['item'].ljust(30)
            string += ' '*5 + f"({hidden[key]['npc']})"
            file.write(string+'\n')
        
        file.write('\n\n\n\n')
        file.write('========\n')
        file.write(' CHESTS \n')
        file.write('========\n')
        file.write('\n\n')


        region = ''
        area = ''
        for item in chestItems:
            key = str(item.key)
            if region != chests[key]['region']:
                file.write('\n\n')
                region = chests[key]['region']
                file.write(region+'\n')
                file.write('-'*len(region))
                file.write('\n\n')

            if area != chests[key]['area']:
                file.write('\n')
                area = chests[key]['area']
            string = ' '*5 + chests[key]['area'].ljust(35)
            string += chests[key]['item'].rjust(30)
            string += ' <-- '
            if item.isMoney:
                string += f"{item.haveItemCnt} leaves".ljust(30)
            else:
                string += nameItems[str(item.haveItemLabel)]['item'].ljust(30)
            file.write(string+'\n')
