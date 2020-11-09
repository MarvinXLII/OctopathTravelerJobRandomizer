from Data import UASSET
from Data import UEXP
from Data import DATA
from Data import TEXTDATA
import hjson
from Utilities import get_filename
import random
import os

class WORLD:
    def __init__(self, path):
        self.path = path
        
        ## Load all the data I need
        self.objectData = DATA(f"{path}/Octopath_Traveler/Content/Object/Database", "ObjectData")
        self.purchaseData = DATA(f"{path}/Octopath_Traveler/Content/Shop/Database", "PurchaseItemTable")
        self.itemAsset = UASSET(f"{path}/Octopath_Traveler/Content/Item/Database/ItemDB.uasset")

        with open(get_filename('data/items.json'), 'r') as file:
            self.items = hjson.load(file)

        with open(get_filename('data/purchase.json'), 'r') as file:
            self.purchase = hjson.load(file)

        with open(get_filename('data/hidden.json'), 'r') as file:
            self.hidden = hjson.load(file)

        with open(get_filename('data/chests.json'), 'r') as file:
            self.chests = hjson.load(file)

        # Item placed at each slot
        self.shuffled = {}


    def randomize(self, settings):
        if settings['items']:
            self.shuffleItems(settings)

    def miscellaneous(self, settings):
        if settings['perfect-thievery']:
            self.perfectThievery()

        if settings['no-thief-chests']:
            self.noThiefChests()
        
    def dump(self):
        # Update the uasset/uexp files
        self.purchaseData.update()
        self.objectData.update()
        # Dump the data
        self.purchaseData.dump(self.path)
        self.objectData.dump(self.path)


    def print(self, outdir):
        self.printHidden(outdir)
        self.printChests(outdir)
        self.printNPCItems(outdir)


    def shuffleItems(self, settings):
        random.seed(settings['seed'])

        # Map slot to new items
        self.shuffled = {}

        #############################
        ## Chests and Hidden items ##
        #############################

        def listObjectItems(objects):
            slots = []; items = []; money = []
            for candidate, value in objects:
                slots.append(candidate)
                item = {
                    'Item': value['Item'],
                    'IsMoney': self.objectData.uexp.entries[candidate]['IsMoney']['value'],
                    'HaveItemCnt': self.objectData.uexp.entries[candidate]['HaveItemCnt']['value'],
                }
                if value['Item'] != 'None':
                    scale = random.uniform(0.6, 1.1)
                    item['Price'] = round(scale * self.items[value['Item']]['Buy'])
                    items.append(item)
                else:
                    money.append(item)
            return slots, items, money

        objectsChests = []
        slotsChests = []; itemsChests = []; moneyChests = []
        if settings['items-chests']:
            for candidate, value in self.chests.items():
                objectsChests.append((candidate, value))
            slotsChests, itemsChests, moneyChests = listObjectItems(objectsChests)

        objectsHidden = []
        slotsHidden = []; itemsHidden = []; moneyHidden = []
        if settings['items-hidden']:
            for candidate, value in self.chests.items():
                objectsHidden.append((candidate, value))
            slotsHidden, itemsHidden, moneyHidden = listObjectItems(objectsHidden)

        ###############
        ## NPC ITEMS ##
        ###############

        slotsNPC = []; itemsNPC = []
        if settings['items-npc']:
            for candidate, value in self.purchase.items():
                if not value['Shuffle']: continue
                slotsNPC.append(candidate)
                itemsNPC.append({
                    'Item': value['Item'],
                    'IsMoney': False,
                    'HaveItemCnt': 1,
                    'Price': self.purchaseData.uexp.entries[candidate]['FCPrice']['value'],
                })
            
        ################
        ## FILL SLOTS ##
        ################
            
        def fillSlots(slots, lst):
            random.shuffle(slots)
            for item in lst:
                s = slots.pop()
                self.shuffled[s] = item

        if settings['items-separately']:
            fillSlots(slotsChests, itemsChests + moneyChests)
            fillSlots(slotsHidden, itemsHidden + moneyHidden)
            fillSlots(slotsNPC, itemsNPC)            
        else:
            # Money first
            slots = slotsChests + slotsHidden
            money = moneyChests + moneyHidden
            fillSlots(slots, money)
            # Everything else
            slots += slotsNPC
            items = itemsChests + itemsHidden + itemsNPC
            fillSlots(slots, items)

        #################
        ## UPDATE DATA ##
        #################
        
        # Fill slots for purchased items from NPC
        for candidate, value in self.purchase.items():
            if not value['Shuffle']: continue
            if not candidate in self.shuffled: continue
            item = self.shuffled[candidate]
            if item['Item'] in self.itemAsset.entries: # i.e. skip "ITM_1??"
                if not self.purchaseData.entryExists(item['Item']):
                    self.purchaseData.addEntry(self.itemAsset.entries[item['Item']])     ## Adds to uasset
            self.purchaseData.changeName(candidate, 'ItemLabel', item['Item'])
            self.purchaseData.changeValue(candidate, 'FCPrice', item['Price'])

        # Fill slots for chests and hidden items
        for candidate, value in objectsChests + objectsHidden:
            if not value['Shuffle']: continue
            if not candidate in self.shuffled: continue
            item = self.shuffled[candidate]
            if item['Item'] in self.itemAsset.entries: # i.e. skip "ITM_1??"
                if not self.objectData.entryExists(item['Item']):
                    self.objectData.addEntry(self.itemAsset.entries[item['Item']])     ## Adds to uasset
            self.objectData.changeName(candidate, 'HaveItemLabel', item['Item'])
            self.objectData.changeValue(candidate, 'IsMoney', item['IsMoney'])
            self.objectData.changeValue(candidate, 'HaveItemCnt', item['HaveItemCnt'])
            

    def perfectThievery(self):
        for slot in self.purchase.keys():
            self.purchaseData.changeValue(slot, 'ProperSteal', -15)


    def noThiefChests(self):
        for slot in self.chests.keys():
            self.objectData.changeValue(slot, 'ObjectType', 1)


    def printHidden(self, outdir):
        
        logfile = f"{outdir}/spoiler_hidden_items.log"
        if os.path.exists(logfile): os.remove(logflag)
        with open(logfile, 'w') as file:
            file.write('==============\n')
            file.write(' HIDDEN ITEMS \n')
            file.write('==============\n')
            file.write('\n\n')
            
            region = ''
            location = ''
            for key, item in self.hidden.items():
                npc = item['NPC']
                vanillaItem = item['Name']
                if key in self.shuffled:
                    if self.shuffled[key]['IsMoney']:
                        count = self.shuffled[key]['HaveItemCnt']
                        swappedItem = f"{count} leaves"
                    else:
                        swappedItem = self.items[self.shuffled[key]['Item']]['Item']
                else:
                    swappedItem = vanillaItem

                if region != item['Region']:
                    file.write('\n\n')
                    region = item['Region']
                    file.write(region+'\n')
                    file.write('-'*len(region))
                    file.write('\n\n')

                if location != item['Location']:
                    file.write('\n')
                    location = item['Location']
                string = ' '*5 + location.ljust(30) + ' '*5
                string += vanillaItem.rjust(30)
                string += ' <-- '
                string += swappedItem.ljust(30)
                string += ' '*5 + npc
                file.write(string+'\n')


    def printChests(self, outdir):
        
        logfile = f"{outdir}/spoiler_chests_items.log"
        if os.path.exists(logfile): os.remove(logflag)
        with open(logfile, 'w') as file:
            file.write('=============\n')
            file.write(' CHESTS ITEMS \n')
            file.write('=============\n')
            file.write('\n\n')

            region = ''
            location = ''
            for key, item in self.chests.items():
                vanillaItem = item['Name']
                if key in self.shuffled:
                    if self.shuffled[key]['IsMoney']:
                        count = self.shuffled[key]['HaveItemCnt']
                        swappedItem = f"{count} leaves"
                    else:
                        swappedItem = self.items[self.shuffled[key]['Item']]['Item']
                else:
                    swappedItem = vanillaItem
                    
                if region != item['Region']:
                    file.write('\n\n')
                    region = item['Region']
                    file.write(region+'\n')
                    file.write('-'*len(region))
                    file.write('\n\n')

                if location != item['Location']:
                    file.write('\n')
                    location = item['Location']
                string = ' '*5 + location.ljust(30) + ' '*5
                string += vanillaItem.rjust(30)
                string += ' <-- '
                string += swappedItem.ljust(30)
                file.write(string+'\n')


    def printNPCItems(self, outdir):
        ## FIRST: reorder everything by region, then location
        regions = {}
        for slot, item in self.purchase.items():
            if item['Region'] == '':
                region = 'UNKNOWN'
            else:
                region = item['Region']
            if region not in regions:
                regions[region] = {}
            if item['Location'] == '':
                location = 'UNKNOWN'
            else:
                location = item['Location']
            if item['Location'] not in regions[region]:
                regions[region][location] = {}
            label = '_'.join(slot.split('_')[:-1])
            if label not in regions[region][location]:
                regions[region][location][label] = []
            regions[region][location][label].append((slot, item))
            
        
        logfile = f"{outdir}/spoiler_npc_items.log"
        if os.path.exists(logfile): os.remove(logflag)
        with open(logfile, 'w') as file:
            file.write('===========\n')
            file.write(' NPC ITEMS \n')
            file.write('===========\n')
            file.write('\n\n')
            for region, locations in regions.items():
                file.write('\n\n')
                file.write('-'*(len(region)+4)+'\n')
                file.write('| '+region+' |\n')
                file.write('-'*(len(region)+4)+'\n')
                for location, npcs in locations.items():
                    file.write('\n\n')
                    file.write(' '*3 + location +'\n')
                    file.write(' '*3 + '-'*len(location) +'\n')
                    file.write('\n')
                    for inventory in npcs.values():
                        npc = inventory[0][1]['NPC']
                        file.write(' '*10 + npc + '\n')
                        for slot, item in inventory:
                            vanillaItem = item['Name']
                            if slot in self.shuffled:
                                swappedItem = self.items[self.shuffled[slot]['Item']]['Item']
                            else:
                                swappedItem = vanillaItem
                            string  = vanillaItem.rjust(50)
                            string += ' <-- '
                            string += swappedItem.ljust(30)
                            file.write(string+'\n')
                        file.write('\n')
                    file.write('\n')
                        
