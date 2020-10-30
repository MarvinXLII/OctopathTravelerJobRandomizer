# run on /PATH/TO/STEAM/GAMES/OCTOPATH TRAVELER/Octopath_Traveler/Content/Character/Database
import random
import ROM
import hjson
import os
from Utilities import get_filename


#############################
# DATA TABLE STUFF FOR JOBS #
#############################

offsets = {
    'weapons': 0x10f,
    'unknown': 0x115, # 9, set all to 0
    'skills': 0x3dd,
    'support': 0x663,
    'costs': 0x787,
    'stats': 0x1e1,
}

stride = {
    'weapons': 1,
    'unknown': 1, # 9, set all to 0
    'skills': 0x46,
    'support': 0x46,
    'costs': 4,
    'stats': 0x1d,
}

size = {
    'weapons': 1,
    'unknown': 1,
    'skills': 2,
    'support': 8, # vary at different locations for some reason, just 2 for Merchant and Thief, then offset of 5 for the rest!?
    'costs': 2,
    'stats': 1,
}

class JOBS:
    def __init__(self, base, data, pc=None):
        self.base = base
        self.data = data
        self.pc = pc
        self.weapons = self.read(offsets['weapons'], stride['weapons'], size['weapons'], 6)
        self.weaponDict = {'Sword':0, 'Spear':1, 'Dagger':2, 'Axe':3, 'Bow':4, 'Staff':5}
        # self.unknown = self.read(offsets['unknown'], stride['unknown'], size['unknown'], 9)
        self.support = self.read(offsets['support'], stride['support'], size['support'], 4)
        self.skills = self.read(offsets['skills'], stride['skills'], size['skills'], 8)
        self.costs = self.read(offsets['costs'], stride['costs'], size['costs'], 8)
        self.stats = self.read(offsets['stats'], stride['stats'], size['stats'], 12)
        # HP, MP, BP, SP, ATK, DEF, MATK, MDEF, ACC, EVA, CON, AGI

    def weaponCheck(self, weapon):
        if weapon == '': return True
        if weapon == 'All': return True
        return self.weapons[self.weaponDict[weapon]]

    def skillSlotAvailable(self, maxNum=8):
        return len(self.skills) < maxNum
    
    def listWeapons(self):
        lst = []
        for weapon in ['Sword', 'Spear', 'Dagger', 'Axe', 'Bow', 'Staff']:
            if self.weaponCheck(weapon):
                lst.append(weapon)
        return lst
    
    def read(self, offset, stride, size, num):
        return ROM.read(self.data, self.base, offset, stride, size, num)

    def write(self, lst, offset, stride, size):
        ROM.write(self.data, lst, self.base, offset, stride, size)

    def patch(self):
        self.write(self.weapons, offsets['weapons'], stride['weapons'], size['weapons'])
        # self.write(self.unknown, offsets['unknown'], stride['unknown'], size['unknown'])
        self.write(self.support, offsets['support'], stride['support'], size['support'])
        self.write(self.skills, offsets['skills'], stride['skills'], size['skills'])
        self.costs = sorted(self.costs) # Ensure sorted before written
        self.write(self.costs, offsets['costs'], stride['costs'], size['costs'])
        self.write(self.stats, offsets['stats'], stride['stats'], size['stats'])


class Skills:
    def __init__(self, jobs, skillJSON):
        self.jobs = jobs
        self.skillJSON = skillJSON

        self.skills = []
        for job in self.jobs.values():
            self.skills += job.skills

        self.placed = {}
        for skill in self.skills:
            self.placed[skill] = False

    def filterPlaced(self, skills):
        skillset = []
        for skill in skills:
            if not self.placed[skill]:
                skillset.append(skill)
        return skillset

    def filterPriority(self, skills, priority):
        skillset = []
        for skill in skills:
            if self.skillJSON[skill]['Priority'] <= priority:
                skillset.append(skill)
        return skillset

    def filterDivineSkills(self, skills):
        skillset = []
        for skill in skills:
            if self.skillJSON[skill]['Divine']:
                skillset.append(skill)
        return skillset

    def filterAdvancedJobSkill(self, skills):
        skillset = []
        for skill in skills:
            if self.skillJSON[skill]['Advanced']:
                skillset.append(skill)
        return skillset

    def filterBaseJobSkill(self, skills):
        skillset = []
        for skill in skills:
            if not self.skillJSON[skill]['Advanced']:
                skillset.append(skill)
        return skillset

    def placeSkills(self, skills, jobs, minidx=0, maxidx=8):
        random.shuffle(skills)
        random.shuffle(jobs)
        for i in range(minidx, maxidx):
            for job in jobs:
                if job.skills[i] > 0:
                    continue
                for skill in skills:
                    if self.placed[skill]: continue
                    weapon = self.skillJSON[skill]['Weapon']
                    if job.weaponCheck(weapon):
                        job.skills[i] = skill
                        self.placed[skill] = True
                        break


    def shuffleSkills(self, oneDivineSkillPerJob, keepAdvancedJobsSeparate):

        jobs = [job for job in self.jobs.values()]
        while True:
            # Reset
            for skill in self.skills:
                self.placed[skill] = False
            for job in self.jobs.values():
                job.skills = [0]*8

            if oneDivineSkillPerJob:
                # Place 1 divine skill per job
                divine = self.filterDivineSkills(self.skills)
                if keepAdvancedJobsSeparate:
                    base = self.filterBaseJobSkill(divine)
                    advanced = self.filterAdvancedJobSkill(divine)
                    self.placeSkills(base, jobs[:8], minidx=7)
                    self.placeSkills(advanced, jobs[8:], minidx=7)
                else:
                    self.placeSkills(divine, jobs, minidx=7)
                # Ensure all 12 were placed
                if sum(self.placed.values()) < 12:
                    continue

            if keepAdvancedJobsSeparate:
                # Finish all advanced jobs
                skillset = self.filterPlaced(self.skills)
                skillset = self.filterAdvancedJobSkill(skillset)
                self.placeSkills(skillset, jobs[8:])
                totalPlaced = sum(self.placed.values()) - 8*oneDivineSkillPerJob
                if totalPlaced != 32: continue

            # All the rest...
            skillset = self.filterPlaced(self.skills)
            skillset = self.filterPriority(skillset, 1)
            self.placeSkills(skillset, jobs, maxidx=2)

            skillset = self.filterPlaced(self.skills)
            skillset = self.filterPriority(skillset, 2)
            self.placeSkills(skillset, jobs)

            skillset = self.filterPlaced(self.skills)
            skillset = self.filterPriority(skillset, 3)
            self.placeSkills(skillset, jobs)

            skillset = self.filterPlaced(self.skills)
            skillset = self.filterPriority(skillset, 4)
            self.placeSkills(skillset, jobs)

            # Assert all are placed
            if all(list(self.placed.values())):
                break



def shuffleStats(jobs):
    # Make lists to shuffle
    stats = [[] for _ in range(12)]
    for job in jobs.values():
        for i in range(12):
            s = job.stats.pop(0)
            stats[i].append(s)

    # Shuffle each list of stats
    list(map(lambda x: random.shuffle(x), stats))

    # Overwrite job stats
    for job in jobs.values():
        for i in range(12):
            s = stats[i].pop()
            job.stats.append(s)


def randomCosts():
    costs = [
        0,
        0,
        random.randint(  1,   5) * 10, #   10 -   50
        random.randint(  6,  14) * 10, #   60 -  140
        random.randint( 40,  60) * 10, #  400 -  600
        random.randint( 80, 120) * 10, #  800 - 1200
        random.randint(240, 360) * 10, # 2400 - 3600
        random.randint(400, 600) * 10, # 4000 - 6000
    ]
    return costs

def shuffleData(filename, settings, outdir):
    
    seed = settings['seed']
    random.seed(seed)

    with open(get_filename(filename), 'rb') as file:
        data = bytearray(file.read())

    jobs = {
        'Merchant': JOBS(0x26, data, 'Tressa'),
        'Thief': JOBS(0x7ce, data, 'Therion'),
        'Warrior': JOBS(0xf76, data, 'Olberic'),
        'Hunter': JOBS(0x171e, data, "H'aanit"),
        'Cleric': JOBS(0x1ec6, data, 'Ophilia'),
        'Dancer': JOBS(0x266e, data, 'Primrose'),
        'Scholar': JOBS(0x2e16, data, 'Cyrus'),
        'Apothecary': JOBS(0x35be, data, 'Alfyn'),
        'Warmaster': JOBS(0x3d66, data),
        'Sorcerer': JOBS(0x450e, data),
        'Starseer': JOBS(0x4cb6, data),
        'Runelord': JOBS(0x545e, data),
    }
    # for name, job in jobs.items():
    #     job.name = name

    ################################
    # SETUP VANILLA SUPPORT SKILLS #
    ################################
    
    with open(get_filename('data/support.json'), 'r') as file:
        support = hjson.load(file)

    # Map job to support skill list
    j2supp = {j:[] for j in jobs.keys()}
    for ki, si in support.items():
        j2supp[si['Job']].append(ki)
    # Map value to support skill
    supportValueToName = {}
    supportNameToValue = {}
    for key, job in jobs.items():
        for name, value in zip(j2supp[key], job.support):
            supportValueToName[value] = name
            supportNameToValue[name] = value

    ########################
    # SETUP VANILLA SKILLS #
    ########################
    
    with open(get_filename('data/skills.json'), 'r') as file:
        skillsJSON = hjson.load(file)

    # Map job to support skill list
    j2s = {j:[] for j in jobs.keys()}
    for ki, si in skillsJSON.items():
        j2s[si['Job']].append(ki)
    # Map value to support skill
    skillNameToValue = {}
    skillValueToName = {}
    skillsDict = {}
    for key, job in jobs.items():
        for name, value in zip(j2s[key], job.skills):
            skillNameToValue[name] = value
            skillValueToName[value] = name
            skillsDict[value] = skillsJSON[name]

    ###################
    # RANODMIZE STUFF #
    ###################

    ## KEEP FOR LATER ##################
    # Shuffle weapons
    # for job in jobs.values():
    #     random.shuffle(job.weapons)
    ####################################
    
    # Shuffle skils
    if settings['skills']:
        print('Shuffling skills')
        random.seed(seed)
        skills = Skills(jobs, skillsDict)
        skills.shuffleSkills(settings['skills-one-divine'], settings['skills-separate'])
        # while not shuffleSkills(jobs, skillsJSON, skillNameToValue):
        #     pass
    
    # Random costs
    if settings['costs']:
        print('Randomizing costs')
        random.seed(seed)
        for job in jobs.values():
            job.costs = randomCosts()

    # Shuffle support
    if settings['support']:
        print('Shuffling support skills')
        random.seed(seed)
        support = []
        for job in jobs.values():
            support += job.support
        random.shuffle(support)
        if settings['support-EM']:
            # Make first support skill
            i = support.index(supportNameToValue['Evasive Maneuvers'])
            jobID = random.randint(0, 7)
            j = jobID * 4
            support[i], support[j] = support[j], support[i]
            # Document PC with EM
            name = list(jobs.values())[jobID].pc
            logfile = f'{outdir}/PC_with_EM.log'
            if os.path.exists(logfile): os.remove(logfile)
            with open(logfile, 'w') as file:
                file.write(f"{name} starts with Evasive Maneuvers")
        # Assign supports
        for i, job in enumerate(jobs.values()):
            job.support = support[i*4:(i+1)*4]

    # Shuffle stats
    if settings['stats']:
        random.seed(seed)
        shuffleStats(jobs)

    ##################
    # PATCH AND DUMP #
    ##################

    for job in jobs.values():
        job.patch()

    with open(get_filename(filename), 'wb') as file:
        file.write(data)

    #############
    # PRINT LOG #
    #############

    logfile = f'{outdir}/rando.log'
    if os.path.exists(logfile): os.remove(logfile)
    with open(logfile, 'w') as file:
        file.write('================\n')
        file.write(' Support Skills \n')
        file.write('================\n')
        file.write('\n\n')

        # Loop over jobs
        for key, job in jobs.items():
            file.write(key+'\n')
            for s in job.support:
                file.write(' '*8+supportValueToName[s]+'\n')
            file.write('\n')
        file.write('\n\n')

        file.write('========\n')
        file.write(' Skills \n')
        file.write('========\n')
        file.write('\n\n')

        # Loop over jobs
        for key, job in jobs.items():
            file.write(key+'     ('+', '.join(job.listWeapons())+')'+'\n')
            for s in job.skills:
                name = skillValueToName[s]
                file.write(' '*8+name.ljust(26, ' ')+skillsJSON[name]['Weapon']+'\n')
            file.write('\n')
        file.write('\n\n')

        file.write('=============\n')
        file.write(' Skill Costs \n')
        file.write('=============\n')
        file.write('\n\n')

        for key, job in jobs.items():
            string = key.ljust(14, ' ')
            string += ''.join(map(lambda x: str(x).rjust(6, ' '), job.costs))
            file.write(string+'\n')
        file.write('\n\n')

        file.write('==================\n')
        file.write(' Stat Bonuses (%) \n')
        file.write('==================\n')
        file.write('\n\n')

        # stats = ['HP', 'MP', 'BP', 'SP', 'ATK', 'DEF', 'MATK', 'MDEF', 'ACC', 'EVA', 'CON', 'AGI']
        stats = ['HP', 'SP', 'ATK', 'DEF', 'MATK', 'MDEF', 'ACC', 'EVA', 'CON', 'AGI']
        stats = list(map(lambda x: x.ljust(6, ' '), stats))
        stats = ''.join(stats)

        file.write(' '*14 + stats + '\n') 
        for key, job in jobs.items():
            stats = list(job.stats)
            stats = stats[0:2] + stats[4:]
            string = key.ljust(12, ' ')
            string += ''.join(map(lambda x: (str(x-100)).rjust(6, ' '), stats))
            file.write(string+'\n')
        file.write('\n\n')
