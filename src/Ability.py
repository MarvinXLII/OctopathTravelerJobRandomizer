import random
import ROM
import hjson
import os
from Utilities import get_filename
import sys



class ABILITY:
    def __init__(self, data, obj):
        self.data = data
        
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

    def randomCosts(self):
        change = round(0.5 + self.cost[0] * random.random() * 0.3)
        change *= 1 if random.random() > 0.5 else -1
        for i in range(4):
            self.cost[i] += change
        
    def randomRatio(self):
        change = []
        for ratio in self.ratio:
            value = round(0.5 + ratio * random.random() * 0.3)
            value *= 1 if random.random() > 0.5 else -1
            change.append(value)
        for i in range(4):
            self.ratio[i] += self.canChangeRatio[i] * change[i]

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
    for job in abilityJSON.values():
        for name, skill in job.items():
            abilities[name] = ABILITY(data, skill)

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

    for ability in abilities.values():
        ability.patch()

    with open(filename, 'wb') as file:
        file.write(data)
        
    return abilities
