# run on /PATH/TO/STEAM/GAMES/OCTOPATH TRAVELER/Octopath_Traveler/Content/Character/Database
import random
import ROM
import hjson
import os
import sys
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
}

stride = {
    'weapons': 1,
    'unknown': 1, # 9, set all to 0
    'skills': 0x46,
    'support': 0x46,
    'costs': 4,
}

size = {
    'weapons': 1,
    'unknown': 1,
    'skills': 2,
    'support': 8, # vary at different locations for some reason, just 2 for Merchant and Thief, then offset of 5 for the rest!?
    'costs': 2,
}

class JOBS:
    def __init__(self, base, data):
        self.base = base
        self.data = data
        self.weapons = self.read(offsets['weapons'], stride['weapons'], size['weapons'], 6)
        # self.unknown = self.read(offsets['unknown'], stride['unknown'], size['unknown'], 9)
        self.support = self.read(offsets['support'], stride['support'], size['support'], 4)
        self.skills = self.read(offsets['skills'], stride['skills'], size['skills'], 8)
        self.costs = self.read(offsets['costs'], stride['costs'], size['costs'], 8)
        self.weaponDict = {'Sword':0, 'Spear':1, 'Dagger':2, 'Axe':3, 'Bow':4, 'Staff':5}

    def skillCheck(self, weapon):
        if weapon == '': return True
        if weapon == 'All': return sum(self.weapons) == 6
        return self.weapons[self.weaponDict[weapon]]

    def skillSlotAvailable(self, maxNum=8):
        return len(self.skills) < maxNum
    
    def listWeapons(self):
        lst = []
        for weapon in ['Sword', 'Spear', 'Dagger', 'Axe', 'Bow', 'Staff']:
            if self.skillCheck(weapon):
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


def shuffleSkills(jobs, skillsJSON, skillNameToValue):
    # Setup
    for job in jobs.values(): job.skills = []
    for skill in skillsJSON.values(): skill['Given'] = False
    skillsJSON['Winnehilds Battle Cry']['Given'] = True
    jobs['Warmaster'].skills.append(skillNameToValue['Winnehilds Battle Cry'])

    def skillSlotRemaining(maxCount):
        check = []
        for job in jobs.values():
            check.append(job.skillSlotAvailable(maxCount))
        return any(check)

    priority = 1
    jobNames = list(jobs.keys())
    maxSkills = {1: 3, 2: 8, 3: 8, 4: 8}
    while priority < 5:
        # Generate list of unplaced skills
        lst = [name for name, skill in skillsJSON.items() if skill['Priority'] <= priority and not skill['Given']]
        random.shuffle(lst)

        while lst:
            skill = lst.pop()
            skillReq = skillsJSON[skill]['Weapon']
            random.shuffle(jobNames)
            for key in jobNames:
                if jobs[key].skillSlotAvailable(maxSkills[priority]) and jobs[key].skillCheck(skillReq):
                    jobs[key].skills.append(skillNameToValue[skill])
                    skillsJSON[skill]['Given'] = True
                    break

            # Break if no slots are left
            if not skillSlotRemaining(maxSkills[priority]):
                break

        priority += 1

    # Assert all skills have been placed
    check = [skill['Given'] for skill in skillsJSON.values()]
    if not all(check): return False

    # Ensure this skill is last, not first!
    skill = jobs['Warmaster'].skills.pop(0)
    jobs['Warmaster'].skills.append(skill)
    return True


def shuffleData(filename, settings):
    
    seed = settings['seed']
    random.seed(seed)

    with open(get_filename(filename), 'rb') as file:
        data = bytearray(file.read())

    jobs = {
        'Merchant': JOBS(0x26, data),
        'Thief': JOBS(0x7ce, data),
        'Warrior': JOBS(0xf76, data),
        'Hunter': JOBS(0x171e, data),
        'Cleric': JOBS(0x1ec6, data),
        'Dancer': JOBS(0x266e, data),
        'Scholar': JOBS(0x2e16, data),
        'Apothecary': JOBS(0x35be, data),
        'Warmaster': JOBS(0x3d66, data),
        'Sorcerer': JOBS(0x450e, data),
        'Starseer': JOBS(0x4cb6, data),
        'Runelord': JOBS(0x545e, data),
    }

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
    for key, job in jobs.items():
        for name, value in zip(j2supp[key], job.support):
            supportValueToName[value] = name

    ########################
    # SETUP VANILLA SKILLS #
    ########################
    
    with open(get_filename('data/skills.json'), 'r') as file:
        skillsJSON = hjson.load(file)

    # Map job to support skill list
    j2s = {j:[] for j in jobs.keys()}
    wskls = {'': [], 'All': [], 'Sword': [], 'Axe': [], 'Spear': [], 'Dagger': [], 'Staff': [], 'Bow': []}
    for ki, si in skillsJSON.items():
        j2s[si['Job']].append(ki)
        wskls[si['Weapon']].append(ki)
    # Map value to support skill
    skillNameToValue = {}
    skillValueToName = {}
    for key, job in jobs.items():
        for name, value in zip(j2s[key], job.skills):
            skillNameToValue[name] = value
            skillValueToName[value] = name

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
        while not shuffleSkills(jobs, skillsJSON, skillNameToValue):
            pass
    
    # Shuffle costs
    if settings['costs']:
        print('Shuffling costs')
        random.seed(seed)
        costs = []
        for job in jobs.values():
            costs += job.costs[2:]
        random.shuffle(costs)
        for i, job in enumerate(jobs.values()):
            job.costs[2:] = costs[i*6:(i+1)*6]

    # Shuffle support
    if settings['support']:
        print('Shuffling support skills')
        random.seed(seed)
        support = []
        for job in jobs.values():
            support += job.support
        random.shuffle(support)
        for i, job in enumerate(jobs.values()):
            job.support = support[i*4:(i+1)*4]

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

    logfile = f'rando_{seed}.log'
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
        file.write('\n\n\n')

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


        file.write('=======\n')
        file.write(' Costs \n')
        file.write('=======\n')
        file.write('\n\n')

        for key, job in jobs.items():
            string = key.ljust(14, ' ')
            string += ''.join(map(lambda x: str(x).ljust(5, ' '), job.costs))
            file.write(string+'\n')
        file.write('\n\n')
