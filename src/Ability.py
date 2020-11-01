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
        self.cost = [cost+change for cost in self.cost]
        
    def randomRatio(self):
        change = round(0.5 + self.ratio[0] * random.random() * 0.3)
        # change = round(0.5 + self.ratio[0] * 1 * 0.3)
        change *= 1 if random.random() > 0.5 else -1
        # change *= 1 if random.random() > 0.0 else -1
        self.ratio = [cost+change*canChange for cost, canChange in zip(self.ratio, self.canChangeRatio)]
        
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

def shuffleWeapons(abilities):
    
    abilitiesWithWeapons = list(filter(lambda x: x.weapon != '', abilities.values()))
    weapons = []
    weaponToRestrict = {}
    for ability in abilitiesWithWeapons:
        weapons.append(ability.weapon)
        weaponToRestrict[ability.weapon] = list(ability.restrict)

    # Remap weapons (e.g. Bow -> Staff, making Staff attacks more frequent)
    types = sorted(list(set(weapons)))
    newtype = list(types)
    random.shuffle(newtype)
    remap = { a:b for a, b in zip(types, newtype) }

    # Shuffle
    random.shuffle(weapons)
    for weapon, ability in zip(weapons, abilitiesWithWeapons):
        ability.weapon = remap[weapon]
        ability.restrict = weaponToRestrict[ability.weapon]


def shuffleData(filename, settings, outdir):
    seed = settings['seed']
    random.seed(seed)

    with open(get_filename(filename), 'rb') as file:
        data = bytearray(file.read())

    with open(get_filename('data/ability.json'), 'r') as file:
        abilityJSON = hjson.load(file)

    # Build objects
    abilities = {}
    for job in abilityJSON.values():
        for name, skill in job.items():
            abilities[name] = ABILITY(data, skill)

    if settings['skills-weapons']:
        random.seed(seed)
        shuffleWeapons(abilities)

    if settings['skills-sp-costs']:
        random.seed(seed)
        for ability in abilities.values():
            ability.randomCosts()

    if settings['skills-power']:
        random.seed(seed)
        for ability in abilities.values():
            ability.randomRatio()

    for ability in abilities.values():
        ability.patch()

    with open(get_filename(filename), 'wb') as file:
        file.write(data)
        
    return abilities
