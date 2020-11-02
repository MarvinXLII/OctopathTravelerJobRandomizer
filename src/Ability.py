import random
import ROM
import hjson
import os
from Utilities import get_filename
import sys



class ABILITY:
    def __init__(self, data, obj, jobname):
        self.data = data
        self.jobname = jobname
        
        self.offsets = {
            'depend': obj['depend'],
            'restrict': obj['restrict'],
            'cost': obj['cost'],
            'ratio': obj['ratio'],
        }

        self.canChangeRatio = obj['scale']
        self.weapon = obj['weapon']

        self.depend = ROM.read(self.data, self.offsets['depend'], 0, 0, 1, 1)
        self.restrict = self.read(self.offsets['restrict'], 2)
        self.cost = self.read(self.offsets['cost'], 1)
        self.ratio = self.read(self.offsets['ratio'], 2)
        self.size = len(self.cost)

    def randomCosts(self):
        change = round(0.5 + self.cost[0] * random.random() * 0.3)
        change *= 1 if random.random() > 0.5 else -1
        for i in range(self.size):
            self.cost[i] += change
        
    def randomRatio(self):
        value = random.random() * 0.3
        sign = 1 if random.random() > 0.5 else -1
        changes = []
        for ratio in self.ratio:
            changes.append( sign * round(0.5 + ratio * value) )
        for i in range(self.size):
            self.ratio[i] += self.canChangeRatio[i] * changes[i]

    def read(self, offsets, size):
        lst = []
        for offset in offsets:
            lst.append(ROM.read(self.data, offset, 0, 1, size, 1))
        return lst

    def write(self, lst, offsets, size):
        for value, offset in zip(lst, offsets):
            ROM.write(self.data, value, offset, 0, 1, size)

    def patch(self):
        self.write(self.restrict, self.offsets['restrict'], 2)
        self.write(self.cost, self.offsets['cost'], 1)
        self.write(self.ratio, self.offsets['ratio'], 2)


def shuffleData(filename, settings, outdir):
    seed = settings['seed']
    random.seed(seed)

    with open(filename, 'rb') as file:
        data = bytearray(file.read())

    with open(get_filename('data/ability.json'), 'r') as file:
        abilityJSON = hjson.load(file)

    # Build objects
    abilities = {}
    for jobname, job in abilityJSON.items():
        for name, skill in job.items():
            abilities[name] = ABILITY(data, skill, jobname)

    if settings['skills-sp-costs']:
        random.seed(seed)
        print('Rescaling SP Costs')
        for ability in abilities.values():
            ability.randomCosts()

    if settings['skills-power']:
        random.seed(seed)
        print('Rescaling skill power')
        for ability in abilities.values():
            ability.randomRatio()

    #############
    # PRINT LOG #
    #############

    logfile = f'{outdir}/spoiler_skills.log'
    if os.path.exists(logfile): os.remove(logfile)
    with open(logfile, 'w') as file:
        file.write('========\n')
        file.write(' Skills \n')
        file.write('========\n')
        file.write('\n\n')

        def printData(skill):
            for bp in range(abilities[skill].size):
                if bp == 0:
                    line = ' '*5 + skill.ljust(35, ' ')
                else:
                    line = ' '*5 + f"{skill} ({bp} BP)".ljust(35, ' ')
                line += f"{abilities[skill].cost[bp]}".rjust(3, ' ')
                if abilities[skill].canChangeRatio[bp]:
                    line += f"{abilities[skill].ratio[bp]}%".rjust(14, ' ')
                else:
                    line += f"----".rjust(14, ' ')
                file.write(line)
                file.write('\n')
            file.write('\n')

        jobname = ''
        for i, (key, ability) in enumerate(abilities.items()):
            if ability.jobname != jobname:
                jobname = ability.jobname
                file.write('\n\n')
                file.write(f"{jobname}\n")
                file.write('-'*len(jobname)+'\n\n')
                file.write(' '*41 + 'SP'.ljust(5, ' ') + 'Power Scale'.ljust(18) + '\n\n')
            printData(key)

    return abilities
