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

        # self.key = self.read('key')
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
            self.case = 'Treasure'

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
        if item.case != 'Treasure': continue
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

    with open(get_filename(filename), 'rb') as file:
        data = bytearray(file.read())

    items = []
    size = 13*16+15
    address = 0x2d
    i = 0
    # while address < 0x30e6e:
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

    seed = settings['seed']

    # Shuffle items
    random.seed(seed)
    if settings['items']:
        if settings['items-option'] == 'items-all':
            shuffleAll(items)
        elif settings['items-option'] == 'items-separate':
            shuffleSubset(items, 'Hidden')
            shuffleSubset(items, 'Treasure')

    ##################
    # PATCH AND DUMP #
    ##################

    for item in items:
        item.patch()

    with open(get_filename(filename), 'wb') as file:
        file.write(data)
