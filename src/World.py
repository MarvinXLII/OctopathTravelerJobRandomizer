from Data import UASSET
from Data import UEXP
from Data import DATA
from Data import TEXTDATA
from Data import TALKDATA
import hjson
from Utilities import get_filename
import random
import os

class WORLD:
    def __init__(self, path, jobs):
        self.path = path
        self.jobs = jobs
        
        ## Load all the data I need
        self.objectData = DATA(f"{path}/Octopath_Traveler/Content/Object/Database", "ObjectData")
        self.purchaseData = DATA(f"{path}/Octopath_Traveler/Content/Shop/Database", "PurchaseItemTable")
        self.itemAsset = UASSET(f"{path}/Octopath_Traveler/Content/Item/Database/ItemDB.uasset")
        self.talkData = TALKDATA(f"{path}/Octopath_Traveler/Content/Talk/Database", "TalkData_EN")
        # self.textData = TEXTDATA(f"{path}/Octopath_Traveler/Content/GameText/Database", "GameTextEN")

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

        if settings['support-spoil']:
            self.spoilPassiveSkills()


    def dump(self):
        # Update the uasset/uexp files
        self.purchaseData.update()
        self.objectData.update()
        self.talkData.update()
        # Dump the data
        self.purchaseData.dump()
        self.objectData.dump()
        self.talkData.dump()


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
            for candidate, value in self.hidden.items():
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
        self.purchaseData.changeValue('DesertS_SHOP_FC_01_1', 'ProperSteal', -15) # Aristocrat's Mask
        self.purchaseData.changeValue('DesertS_SHOP_FC_02_1', 'ProperSteal', -15) # Aristocrat's Mask
        self.purchaseData.changeValue('DesertS_SHOP_FC_03_1', 'ProperSteal', -15) # Attendants's Mask
        self.purchaseData.changeValue('DesertS_SHOP_FC_10_1', 'ProperSteal', -15) # Black Market Inventory
        self.purchaseData.changeValue('DesertS_SHOP_FC_11_1', 'ProperSteal', -15) # Bottle of Wine
        self.purchaseData.changeValue('PlainM_SHOP_FC_06_1', 'ProperSteal', -15)  # Oasis Water
        self.purchaseData.changeValue('PlainM_SHOP_FC_11_1', 'ProperSteal', -15)  # Crystal Ore
        self.purchaseData.changeValue('PlainM_SHOP_FC_17_1', 'ProperSteal', -15)  # Wyvern Scale
        self.purchaseData.changeValue('SnowM_SHOP_FC_01_1', 'ProperSteal', -15)   # Brigand's Garb
        self.purchaseData.changeValue('SnowM_SHOP_FC_02_1', 'ProperSteal', -15)   # Brigand Leader's Garb


    def noThiefChests(self):
        for slot in self.chests.keys():
            if self.objectData.uexp.entries[slot]['ObjectType']['value'] == 3:
                self.objectData.changeValue(slot, 'ObjectType', 1)


    def spoilPassiveSkills(self):
        text1 = {
            'Thief': 'TX_OBD_CLD_2J0000_0010',
            'Dancer': 'TX_OBD_DED_2J0000_0010',
            'Hunter': 'TX_OBD_FOD_2J0000_0010',
            'Sorcerer': 'TX_OBD_FOD_3J0000_0010',
            'Warrior': 'TX_OBD_MOD_2J0000_0010',
            'Runelord': 'TX_OBD_MOD_3J0000_0010',
            'Scholar': 'TX_OBD_PLD_2J0000_0010',
            'Starseer': 'TX_OBD_PLD_3J0000_0010',
            'Apothecary': 'TX_OBD_RID_2J0000_0010',
            'Warmaster': 'TX_OBD_RID_3J0000_0010',
            'Merchant': 'TX_OBD_SED_2J0000_0010',
            'Cleric': 'TX_OBD_SND_2J0000_0010',
        }

        text2 = {
            'Thief': 'TX_OBN_CLD_2J0000_0020',
            'Dancer': 'TX_OBN_DED_2J0000_0020',
            'Hunter': 'TX_OBN_FOD_2J0000_0020',
            'Sorcerer': 'TX_OBN_FOD_3J0000_0020',
            'Warrior': 'TX_OBN_MOD_2J0000_0020',
            'Runelord': 'TX_OBN_MOD_3J0000_0020',
            'Scholar': 'TX_OBN_PLD_2J0000_0020',
            'Starseer': 'TX_OBN_PLD_3J0000_0020',
            'Apothecary': 'TX_OBN_RID_2J0000_0020',
            'Warmaster': 'TX_OBN_RID_3J0000_0020',
            'Merchant': 'TX_OBN_SED_2J0000_0020',
            'Cleric': 'TX_OBN_SND_2J0000_0020',
        }

        text3 = {
            'Thief': 'TX_OBN_CLD_2J0000_0030',
            'Dancer': 'TX_OBN_DED_2J0000_0030',
            'Hunter': 'TX_OBN_FOD_2J0000_0030',
            'Sorcerer': 'TX_OBN_FOD_3J0000_0030',
            'Warrior': 'TX_OBN_MOD_2J0000_0030',
            'Runelord': 'TX_OBN_MOD_3J0000_0030',
            'Scholar': 'TX_OBN_PLD_2J0000_0030',
            'Starseer': 'TX_OBN_PLD_3J0000_0030',
            'Apothecary': 'TX_OBN_RID_2J0000_0030',
            'Warmaster': 'TX_OBN_RID_3J0000_0030',
            'Merchant': 'TX_OBN_SED_2J0000_0030',
            'Cleric': 'TX_OBN_SND_2J0000_0030',
        }

        for key, job in self.jobs.items():
            # Collecting the orb
            strings = [f'You unlocked {key} as a secondary job!\nThe passive skills thee shall learn are\n']
            strings += job.supportSkillNames
            string = '\n'.join(strings)
            self.talkData.changeText(text1[key], [string])
            # After collecting the orb
            # Line 1
            string = ', '.join(job.supportSkillNames[:2])
            self.talkData.changeText(text2[key], [string])
            # Line 2
            string = ', '.join(job.supportSkillNames[2:])
            self.talkData.changeText(text3[key], [string])


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
                        
