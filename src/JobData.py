# run on /PATH/TO/STEAM/GAMES/OCTOPATH TRAVELER/Octopath_Traveler/Content/Character/Database
import random

## MUST TEST!!!
# What skills does a PC know if their first skill cost is nonzero but another is zero?
# What skills does a PC know if all of their skills are nonzero?

random.seed(42)

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
        self.unknown = self.read(offsets['unknown'], stride['unknown'], size['unknown'], 9)
        self.support = self.read(offsets['support'], stride['support'], size['support'], 4)
        self.skills = self.read(offsets['skills'], stride['skills'], size['skills'], 8)
        self.costs = self.read(offsets['costs'], stride['costs'], size['costs'], 8)

    def read(self, offset, stride, size, num):
        lst = []
        address = self.base + offset
        for i in range(num):
            b = data[address:address+size]
            lst.append(int.from_bytes(b, byteorder='little', signed=False))
            address += stride
        return lst

    def write(self, lst, offset, stride, size):
        address = self.base + offset
        for i, b in enumerate(lst):
            d = b.to_bytes(size, byteorder='little', signed=False)
            data[address:address+size] = d
            address += stride

    def patch(self):
        self.weapons = [1]*len(self.weapons)
        self.write(self.weapons, offsets['weapons'], stride['weapons'], size['weapons'])
        self.write(self.unknown, offsets['unknown'], stride['unknown'], size['unknown'])
        self.write(self.support, offsets['support'], stride['support'], size['support'])
        self.write(self.skills, offsets['skills'], stride['skills'], size['skills'])
        # Sort costs before writing
        # self.costs = sorted(self.costs)
        self.costs = [0]*len(self.costs)
        self.write(self.costs, offsets['costs'], stride['costs'], size['costs'])




filename = 'JobData.uexp'
with open(filename, 'rb') as file:
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

print('VANILLA')
for name, job in jobs.items():
    print('')
    print(name)
    print(list(map(hex, job.weapons)))
    print(list(map(hex, job.support)))
    print(list(map(hex, job.skills)))
    print(list(map(hex, job.costs)))


# Shuffle weapons
for job in jobs.values():
    random.shuffle(job.weapons)

# Shuffle support
support = []
for job in jobs.values():
    support += job.support
random.shuffle(support)
for i, job in enumerate(jobs.values()):
    job.support = support[i*4:(i+1)*4]

# Shuffle skills
skills = []
for job in jobs.values():
    skills += job.skills
random.shuffle(skills)
for i, job in enumerate(jobs.values()):
    job.skills = skills[i*8:(i+1)*8]

# Shuffle costs
# costs = []
# for job in jobs.values():
#     costs += job.costs
# random.shuffle(costs)
# for i, job in enumerate(jobs.values()):
#     job.costs = costs[i*8:(i+1)*8]

for job in jobs.values():
    job.patch()

filename = 'JobData.uexp'
with open(filename, 'wb') as file:
    file.write(data)

print('Randomized')
for name, job in jobs.items():
    print('')
    print(name)
    print(list(map(hex, job.weapons)))
    print(list(map(hex, job.support)))
    print(list(map(hex, job.skills)))
    print(list(map(hex, job.costs)))
