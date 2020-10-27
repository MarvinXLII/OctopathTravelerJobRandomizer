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
        self.objResLabels = self.read('ObjResLabels')    # NEEDED FOR FUTURE ORB SHUFFLE???
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

    # Do some checks just in case
    def _check(self):
        if self.case == 'Hidden':
            assert self.objType == 4, 'Hidden item has wrong type!'
            if self.isMoney:
                assert self.haveItemCnt > 1, "Hidden item has wrong count of money!"
                assert self.haveItemLabel == 370, "Hidden item has wrong count of money!"
            else:
                assert self.haveItemCnt == 1, "Hidden item has wrong count of money!"
                assert self.haveItemLabel != 370, "Hidden item has wrong count of money!"
            # assert self.haveItemCnt == 1 if self.isMoney == 0, 'Hidden item has conflicting settings!'
            # assert self.haveItemLabel == 370 if (self.isMoney == 1 and self.haveItemCnt > 1), 'Hidden item has conflicting settings!'
            # assert self.haveItemLabel > 0 and self.isMoney == 0 and self.haveItemCnt == 1, 'Hidden item has conflicting settings!'
            # assert self.haveItemLabel == 0 and self.isMoney == 1 and self.haveItemCnt > 1, 'Hidden item has conflicting settings!'
        elif self.case == 'Orb':
            assert self.objType == 0, 'Orb has wrong type!'
            assert self.haveItemLabel == 370, 'Orb has wrong item label'
            assert self.haveItemCnt == 0, 'Orb has wrong item count'
            assert self.isMoney == 0, 'Orb is set as money!'
        elif self.case == 'Treasure':
            assert self.objType != 0, 'Treasure has wrong type!'
            assert self.objType != 4, 'Treasure has wrong type!'
            # assert self.haveItemLabel > 0 and self.isMoney == 0 and self.haveItemCnt == 1, 'Treasure has conflicting settings!'
            # assert self.haveItemLabel == 0 and self.isMoney == 1 and self.haveItemCnt > 1, 'Treasure has conflicting settings!'

    def patch(self):
        # self._check()
        self.write('ObjType', self.objType)
        self.write('ObjResLabels', self.objResLabels)
        self.write('IsMoney', self.isMoney)
        self.write('HaveItemCnt', self.haveItemCnt)
        self.write('HaveItemLabel', self.haveItemLabel)


# Reset "objType" of all chests
def noThiefChests(items):
    for item in items:
        if item.case != 'Treasure': continue
        item.objType = 1
        # item.objType = 2
        # item.objType = 3 # Locked chest

def shuffleAll(items):
    # Generate lists
    candidates = []
    for item in items:
        if item.case == 'Orb': continue
        candidates.append([item.isMoney, item.haveItemCnt, item.haveItemLabel])
    # Shuffle candidates
    random.shuffle(candidates)
    # Place candidates
    slots = filter(lambda x: x.case != 'Orb', items)
    for candidate, slot in zip(candidates, slots):
        slot.isMoney = candidate[0]
        slot.haveItemCnt = candidate[1]
        slot.haveItemLabel = candidate[2]

def shuffleSubset(case):
    candidates = []
    for item in items:
        if item.case != case: continue
        candidates.append(list([item.isMoney, item.haveItemCnt, item.haveItemLabel]))
    random.shuffle(candidates)
    # Place candidates
    slots = filter(lambda x: x.case == case, items)
    for candidate, slot in zip(candidates, slots):
        slot.isMoney = candidate[0]
        slot.haveItemCnt = candidate[1]
        slot.haveItemLabel = candidate[2]

def shuffleItems(filename, settings):

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
    if settings['items'] != '':
        if settings['items'] == 'items-all':
            shuffleAll(items)
        elif settings['items'] == 'items-separate':
            shuffleSubset('Hidden')
            shuffleSubset('Treasures')

    ##################
    # PATCH AND DUMP #
    ##################

    for item in items:
        item.patch()

    with open(get_filename(filename), 'wb') as file:
        file.write(data)
