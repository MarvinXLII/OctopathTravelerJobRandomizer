import random
import os
import sys

class JOBS:
    def __init__(self, jobData, pcData, settings):
        self.jobData = jobData
        self.pcData = pcData

        self.keyWithEM = 'ePROFESSOR'

        self.separateAdvanced = settings['support-separate']
        self.emFirst = settings['support-EM']
        self.shuffleStatsData = settings['stats']
        self.statsFairly = settings['stats-fairly']
        self.randomSuppCosts = settings['skills-jp-costs']
        self.baseCostsForAdv = settings['skills-jp-costs-adv']

        self.statsJOB = {} # Stats from job orbs
        self.statsPC = {}  # Default stats for PCs
        for i, jobKey in enumerate(self.jobData.table):
            jobStats = self.jobData.readStats(jobKey)
            self.statsJOB[jobKey] = self.jobData.readStats(jobKey)
            if i < 8:
                key = str(i+1)
                pcStats = self.pcData.readStats(key)
                self.statsPC[key] = pcStats

        self.jobName = {
            'eFENCER': 'Warrior',
            'eMERCHANT': 'Merchant',
            'ePROFESSOR': 'Scholar',
            'eDANCER': 'Dancer',
            'eHUNTER': 'Hunter',
            'eTHIEF': 'Thief',
            'ePRIEST': 'Cleric',
            'eALCHEMIST': 'Apothecary',
            'eWEAPON_MASTER': 'Warmaster',
            'eWIZARD': 'Sorcerer',
            'eASTRONOMY': 'Starseer',
            'eRUNE_MASTER': 'Runelord',
        }

    def spoilSupportSkills(self):
        for key, job in self.jobName.items():
            self.jobData.supportNameQOL(key, job)

    def randomSupportCosts(self):
        def baseCosts():
            return [
                0,
                0,
                random.randint(  1,   5) * 10, #   10 -   50
                random.randint(  6,  14) * 10, #   60 -  140
                random.randint( 40,  60) * 10, #  400 -  600
                random.randint( 80, 120) * 10, #  800 - 1200
                random.randint(240, 360) * 10, # 2400 - 3600
                random.randint(400, 600) * 10, # 4000 - 6000
            ]

        def advCosts():
            return [
                0,
                random.randint(160, 240) * 10, # 1600 - 2400
                random.randint(160, 240) * 10, # 1600 - 2400
                random.randint(160, 240) * 10, # 1600 - 2400
                random.randint(160, 240) * 10, # 1600 - 2400
                random.randint(160, 240) * 10, # 1600 - 2400
                random.randint(160, 240) * 10, # 1600 - 2400
                random.randint(400, 600) * 10, # 4000 - 6000
            ]

        jobKeys = list(self.jobData.table.keys())
        if self.randomSuppCosts:
            for key in jobKeys[:8]:
                self.jobData.patchSupportCosts(key, baseCosts())
            if self.baseCostsForAdv:
                for key in jobKeys[8:]:
                    self.jobData.patchSupportCosts(key, baseCosts())
            else:
                for key in jobKeys[8:]:
                    self.jobData.patchSupportCosts(key, advCosts())
        else:
            if self.baseCostsForAdv:
                costs = [0, 0, 30, 100, 500, 1000, 3000, 5000]
                for key in jobKeys[8:]:
                    self.jobData.patchSupportCosts(key, costs)


    def shuffleSupportAbilities(self):
        support = []
        for jobKey in self.jobData.table:
            support += self.jobData.readSupportArray(jobKey)

        if self.separateAdvanced:
            base = support[:32]
            adv = support[32:]
            random.shuffle(base)
            random.shuffle(adv)
            support = base + adv
        else:
            random.shuffle(support)

        for i, jobKey in enumerate(self.jobData.table):
            names = support[i*4:(i+1)*4]
            self.jobData.patchSupportArray(jobKey, names)

    def getEMEarly(self):
        emName = 'BT_ABI_249'
        for jobKey in self.jobData.table:
            support = self.jobData.readSupportArray(jobKey)
            if emName in support:
                self.keyWithEM = jobKey
                break

        # Make EM the first support skill
        idx = support.index(emName)
        support = support[idx%4:] + support[:idx%4]
        # Patch -- 3 skills needed
        self.jobData.patchSupportArray(self.keyWithEM, support, params=[3, 5, 6, 7])

        # Cost 1 JP for the third skill
        costs = self.jobData.readSupportCosts(self.keyWithEM)
        costs[2] = 1
        self.jobData.patchSupportCosts(self.keyWithEM, costs)

    def shuffleStats(self):

        def fyAll(stats, keys):
            for i,ki in enumerate(keys):
                kj = random.choice(keys[i:])
                stats[ki], stats[kj] = stats[kj], stats[ki]

        def fyStat(stats, keys):
            for statKey in stats[keys[0]].keys():
                for i,ki in enumerate(keys):
                    kj = random.choice(keys[i:])
                    stats[ki][statKey], stats[kj][statKey] = stats[kj][statKey], stats[ki][statKey]
                
        jobKeys = list(self.jobData.table.keys())
        if self.statsFairly:
            fyAll(self.statsJOB, jobKeys[:8]) # Base jobs
            fyAll(self.statsJOB, jobKeys[8:]) # Advanced jobs
            fyAll(self.statsPC, [str(i) for i in range(1,9)])
        else:
            fyStat(self.statsJOB, jobKeys)
            fyStat(self.statsPC, [str(i) for i in range(1,9)])
            
        # Patch stats -- job orbs
        for jobKey, stats in self.statsJOB.items():
            self.jobData.patchStats(jobKey, stats)
        # Patch stats -- pc defaults
        for jobKey, stats in self.statsPC.items():
            self.pcData.patchStats(jobKey, stats)

    def printLog(self, path):

        if self.emFirst:
            fileName = os.path.join(path, 'spoiler_job_with_EM.log')
            with open(fileName, 'w') as sys.stdout:
                print(self.jobName[self.keyWithEM])

        fileName = os.path.join(path, 'spoiler_job_support_skills.log')
        with open(fileName, 'w') as sys.stdout:
            print('================')
            print(' Support Skills ')
            print('================')
            print('')
            print('')
            for jobKey in self.jobData.table:
                print(' ',self.jobName[jobKey])
                supportNames = self.jobData.readSupportNames(jobKey)
                for name in supportNames:
                    print('    ',name)
                print('')

        def printStatNames():
            names = list(self.statsPC['1'].keys())
            names.remove('MP')
            names.remove('BP')
            strings = [name.rjust(5, ' ') for name in names]
            print(' '*18, *strings)
            print('')
            
        fileName = os.path.join(path, 'spoiler_job_stats.log')
        jobNameList = list(self.jobName.values())
        with open(fileName, 'w') as sys.stdout:
            print('============')
            print(' Base Stats ')
            print('============')
            print('')
            print('')
            printStatNames()
            for i, job in enumerate(jobNameList[:8]):
                key = str(i+1)
                values = [f"{vi}%".rjust(5, ' ') for vi in self.statsPC[key].values()]
                values = values[:2] + values[4:] # Remove "SP" and BP
                print('   ', job.ljust(14, ' '), *values)
            print('')
            print('')
            print('')
            print('=================')
            print(' Subclass Boosts ')
            print('=================')
            print('')
            print('')
            printStatNames()
            for key, job in self.jobName.items():
                values = [f"{vi-100}%".rjust(5, ' ') for vi in self.statsJOB[key].values()]
                values = values[:2] + values[4:] # Remove "SP" and BP
                print('   ', job.ljust(14, ' '), *values)

        fileName = os.path.join(path, 'spoiler_job_sp_costs.log')
        with open(fileName, 'w') as sys.stdout:
            print('==========')
            print(' SP Costs ')
            print('==========')
            print('')
            print('')
            for key, job in self.jobName.items():
                values = [f"{c}".rjust(6, ' ') for c in self.jobData.readSupportCosts(key)]
                print(job.ljust(14, ' '), *values)

        sys.stdout = sys.__stdout__
