import hjson
import binascii
import sys
import shutil
import os
import random
from Utilities import get_filename

class TREASURES:
    def __init__(self, objects, shops, items, settings):
        self.objects = objects
        self.shops = shops
        self.items = items

        # Settings for treasure shuffling
        self.shuffleChests = settings['items-chests']
        self.shuffleHidden = settings['items-hidden']
        self.shuffleNPC = settings['items-npc']
        self.keepSeparate = settings['items-separately']
        self.separateChests = self.keepSeparate and settings['items-separate-chests']
        self.separateHidden = self.keepSeparate and settings['items-separate-hidden']
        self.separateNPC = self.keepSeparate and settings['items-separate-npc']

        # Load files for filtering and print logs
        with open(get_filename('json/hidden.json'),'r') as file:
            self.dataHidden = hjson.load(file)
        with open(get_filename('json/chests.json'),'r') as file:
            self.dataChests = hjson.load(file)
        with open(get_filename('json/shops.json'),'r') as file:
            self.dataShops = hjson.load(file)
        
        # For shuffling and printing
        self.chests = {}
        self.hidden = {}
        self.npc = {}
        self.slots = {}

        # Load chests and hidden treasure data
        for name in self.objects.table:
            objType = self.objects.readByte(name, 'ObjectType')
            if objType: # Skip orbs
                data = {
                    'IsMoney': self.objects.readBool(name, 'IsMoney'),
                    'HaveItemLabel': self.objects.readName(name, 'HaveItemLabel'),
                    'HaveItemCnt': self.objects.readInt(name, 'HaveItemCnt'),
                }
                if not data['IsMoney']:
                    data['Price'] = self.items.getBuyPrice(data['HaveItemLabel'])
                if objType == 4:
                    self.hidden[name] = data
                else:
                    self.chests[name] = data

        # Load shop data
        for name in self.shops.table:
            status = self.shops.readInt(name, 'ArrivalStatus')
            if status: # npc shops only
                data = {
                    'IsMoney': False,
                    'HaveItemLabel': self.shops.readName(name, 'ItemLabel'),
                    'HaveItemCnt': 1,
                    'Price': self.shops.readInt(name, 'FCPrice'),
                }
                self.npc[name] = data

    def updateObjects(self):
        for name in self.objects.table:
            if name in self.slots:
                # Update uasset if needed
                asset = self.items.uasset.getEntry(self.slots[name]['HaveItemLabel'])
                self.objects.uasset.addEntry(asset)
                # Patch uexp
                self.objects.patchName(name, 'HaveItemLabel', self.slots[name]['HaveItemLabel'])
                self.objects.patchBool(name, 'IsMoney', self.slots[name]['IsMoney'])
                self.objects.patchInt(name, 'HaveItemCnt', self.slots[name]['HaveItemCnt'])

    def updateShops(self):
        for name in self.shops.table:
            if name in self.slots:
                # Update uasset if needed
                asset = self.items.uasset.getEntry(self.slots[name]['HaveItemLabel'])
                self.shops.uasset.addEntry(asset)
                # Update prices
                if self.slots[name]['Price'] > 20:
                    price = random.uniform(0.5, 1.1) * self.slots[name]['Price']
                    self.slots[name]['Price'] = round(price / 10) * 10
                # Patch uexp
                self.shops.patchInt(name, 'FCPrice', self.slots[name]['Price'])
                self.shops.patchName(name, 'ItemLabel', self.slots[name]['HaveItemLabel'])

    def _shuffle(self, slots):
        # Fisher-Yates
        keys = list(slots.keys())
        for i in range(len(keys)):
            j = random.randrange(i, len(keys))
            # ensure NPC slots don't get money!
            if keys[i] in self.npc:
                while slots[keys[j]]['IsMoney']:
                    j = random.randrange(i, len(keys))
            # Swap
            ki = keys[i]
            kj = keys[j]
            slots[ki], slots[kj] = slots[kj], slots[ki]
        # Store results
        self.slots.update(slots)

    def shuffle(self):

        def getChests():
            return {key:value for key, value in self.chests.items() if self.dataChests[key]['Shuffle']}
        
        def getHidden():
            return {key:value for key, value in self.hidden.items() if self.dataHidden[key]['Shuffle']}
        
        def getNPC():
            return {key:value for key, value in self.npc.items() if self.dataShops[key]['Shuffle']}

        # Shuffle treasures
        # NB: ensure NPC slots are first in the mixedSlots dict to ensure
        # enough suitable items remain. No money "items" can be put in their slots!
        mixedSlots = {}
        if self.shuffleNPC:
            slots = getNPC()
            if self.separateNPC:
                self._shuffle(slots)
            else:
                mixedSlots.update(slots)
        if self.shuffleChests:
            slots = getChests()
            if self.separateChests:
                self._shuffle(slots)
            else:
                mixedSlots.update(slots)
        if self.shuffleHidden:
            slots = getHidden()
            if self.separateHidden:
                self._shuffle(slots)
            else:
                mixedSlots.update(slots)

        # Shuffle whatever is to be mixed
        self._shuffle(mixedSlots)

        ## NOW UPDATE EVERYTHING IN THE TABLES
        self.updateObjects()
        self.updateShops()

    def printLog(self, path):

        def getString(d):
            if d['IsMoney']:
                return f"{d['HaveItemCnt']} Leaves"
            name = self.items.getName(d['HaveItemLabel'])
            return name

        def printouts(data, treasures):
            regions = [
                'Cliftlands', 'Sunlands', 'Woodlands', 'Highlands',
                'Flatlands', 'Riverlands', 'Coastlands', 'Frostlands',
            ]
            for region in regions:
                print('')
                print('')
                print(region)
                print('-'*len(region))
                print('')
                print('')
                
                location = None
                for key in data:
                    if data[key]['Region'] != region:
                        continue

                    if location != data[key]['Location']:
                        location = data[key]['Location']
                        print('')

                    string = ' '*5 + location.ljust(30) + ' '*5
                    if 'NPC' in data[key]:
                        string += data[key]['NPC'].ljust(25)

                    string += getString(treasures[key]).rjust(30)
                    if key in self.slots:
                        string += ' <-- '
                        string += getString(self.slots[key]).ljust(30)

                    print(string)
        
        fileName = os.path.join(path, 'spoiler_treasures_hidden_items.log')
        with open(fileName, 'w') as sys.stdout:
            print('==============')
            print(' HIDDEN ITEMS ')
            print('==============')
            print('')
            print('')
            printouts(self.dataHidden, self.hidden)

        fileName = os.path.join(path, 'spoiler_treasures_chests.log')
        with open(fileName, 'w') as sys.stdout:
            print('========')
            print(' CHESTS ')
            print('========')
            print('')
            print('')
            printouts(self.dataChests, self.chests)

        fileName = os.path.join(path, 'spoiler_treasures_npc_items.log')
        with open(fileName, 'w') as sys.stdout:
            print('===========')
            print(' NPC ITEMS ')
            print('===========')
            print('')
            print('')
            printouts(self.dataShops, self.npc)

        sys.stdout = sys.__stdout__
