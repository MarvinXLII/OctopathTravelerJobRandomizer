from ROM import ROM
# from Data import DATA, TEXTDATA, TALKDATA
from Data import DATA, PC, SHOPS, GAMETEXT, TALKDATA, ITEMS, ABILITYSETS, ABILITYDATA, OBJECTS, JOBDATA
from Treasures import TREASURES
from Abilities import ABILITIES
from Jobs import JOBS
import os
import shutil
import random
import hjson

class WORLD:
    def __init__(self, rom, settings):
        self.settings = settings
        self.rom = rom
        
        # Output directory
        self.outPath = f"seed_{settings['seed']}"
        if os.path.isdir(self.outPath):
            shutil.rmtree(self.outPath)
        os.makedirs(self.outPath)
        
        # Decompress various files needed; makes data accessible
        self.gameText = GAMETEXT(self.rom)
        self.talkData = TALKDATA(self.rom)
        self.objectData = OBJECTS(self.rom)
        self.itemData = ITEMS(self.rom, self.gameText)
        self.pcData = PC(self.rom, self.itemData)
        self.shopData = SHOPS(self.rom)
        self.abilityData = ABILITYDATA(self.rom, self.gameText)
        self.abilitySetData = ABILITYSETS(self.rom)
        self.jobData = JOBDATA(self.rom, self.abilityData, self.talkData)

        # Objects for shuffling things
        self.treasures = TREASURES(self.objectData, self.shopData, self.itemData, self.settings)
        self.abilities = ABILITIES(self.abilitySetData, self.abilityData, self.settings)
        self.jobs = JOBS(self.jobData, self.pcData, self.settings)

        # ALWAYS MODIFY TITLE SCREEN
        self.gameText.patchText('TITLE_START_BUTTON', 'RANDOMIZER')

    def failed(self):
        print(f'Randomizer failed! Removing directory {self.outPath}.')
        shutil.rmtree(self.outPath)
        
    def qualityOfLife(self):
        if self.settings['spurning-ribbon']:
            self.pcData.startWithSpurningRibbon()

        if self.settings['perfect-thievery']:
            self.shopData.perfectKeyItemThievery()  # RUNS BUT NOT TESTED!!!

        if self.settings['no-thief-chests']:
            self.objectData.noThiefChests()

        if self.settings['scale-vets-cost']:
            scale = int(self.settings['scale-vets-cost-option'])
            self.abilityData.scaleVetsCost(scale)

        if self.settings['support-EM']:
            self.jobs.getEMEarly()

        if self.settings['support-spoil']:
            self.jobs.spoilSupportSkills()

    def randomize(self):

        if self.settings['items']:
            random.seed(self.settings['seed'])
            self.treasures.shuffle()
            
        ## JOBDATA STUFF
        if self.settings['support']:
            random.seed(self.settings['seed'])
            self.jobs.shuffleSupportAbilities()
        if self.settings['skills-jp-costs']:
            random.seed(self.settings['seed'])
            self.jobs.randomSupportCosts()
        if self.settings['stats']:
            random.seed(self.settings['seed'])
            self.jobs.shuffleStats()

        ## ABILITY STUFF
        if self.settings['skills']:
            random.seed(self.settings['seed'])
            self.abilities.shuffleJobAbilities()
            if self.settings['skills-capture']:
                self.abilities.randomCaptureSkills()
        if self.settings['skills-sp-costs']:
            random.seed(self.settings['seed'])
            self.abilities.randomSP()
        if self.settings['skills-power']:
            random.seed(self.settings['seed'])
            self.abilities.randomRatio()

    def spoilerLog(self):
        self.treasures.printLog(self.outPath)
        self.abilities.printLog(self.outPath)
        self.jobs.printLog(self.outPath)
        
    def dump(self):
        # Rebuilds data
        self.talkData.update()
        self.jobData.update()
        self.gameText.update()
        self.itemData.update()
        self.pcData.update()
        self.objectData.update()
        self.shopData.update()
        self.abilityData.update()
        self.abilitySetData.update()
        # Print spoiler logs
        self.spoilerLog()
        # Dumps pak
        outFile = os.path.join(self.outPath, 'rando_P.pak')
        self.rom.buildPak(outFile)
        if self.settings['copy-pak']:
            srcFile = outFile
            dstFile = os.path.join(self.settings['rom'], 'rando_P.pak')
            shutil.copy(srcFile, dstFile)
        # Dump settings
        outFile = os.path.join(self.outPath, 'settings.json')
        with open(outFile, 'w') as file:
            hjson.dump(self.settings, file)
