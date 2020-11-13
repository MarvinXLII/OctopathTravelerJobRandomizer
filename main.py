import os
import random
import hjson
import sys
sys.path.append('src')
from gui import randomize
from release import RELEASE

def main(settings):
    try:
        randomize(settings)
    except:
        print('Randomizer failed!')

if __name__ == '__main__':

    settings = {
        'release': RELEASE,
        # 'seed': random.randint(0, 1e8),
        # 'seed': 31528019,
        'seed': 42,
        'skills': True,
        'skills-one-divine': False,
        'skills-separate': False,
        'skills-weapons': True,
        'skills-sp-costs': True,
        'skills-jp-costs': True,
        'skills-power': True,
        'scale-vets-cost': True, 
        'scale-vets-cost-option': 2, 
        # 'scale-vets-cost-option': 4, 
        'support': True,
        'support-separate': True,
        'support-EM': True,
        'support-spoil': True,
        'stats': True,
        # 'stats-option': 'random',
        'stats-option': 'fairly',
        'items': True,
        'items-chests': False,
        'items-hidden': False,
        'items-npc': False,
        'items-separately': False,
        # 'items-option': 'items-separate',
        'perfect-thievery': True,
        'no-thief-chests': True,
        'spurning-ribbon': True,
        'output': '',
    }

    if len(sys.argv) > 2:
        print('Usage: python main.py <settings.json>')
    elif len(sys.argv) == 2:
        if not os.path.isfile(sys.argv[1]):
            print(f"{sys.argv[1]} does not exist!")
        else:
            with open(sys.argv[1], 'r') as file:
                loadedSettings = hjson.load(file)
            # Check settings
            if set(loadedSettings.keys()) != set(settings.keys()):
                print('Error in settings file. Perhaps an incompatible release or it was modified')
            else:
                if loadedSettings['release'] != RELEASE:
                    print(f'WARNING: Loaded settings are from an older version {release}')
                main(loadedSettings)
    else:
        main(settings)
