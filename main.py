import subprocess
import os
import shutil
import random
import sys
sys.path.append('src')
import JobData
from gui import randomize

def main():
    settings = {
        'seed': random.randint(0, 1e8),
        'skills': True,
        'costs': True,
        'support': True,
        'support-EM': True,
        'stats': True,

        'items': True,
        'items-option': 'items-all',
        # 'items-option': 'items-separate',

        'no-thief-chests': True,
    }

    setup()
    randomize(settings)
    cleanup()

# Build paths for generating patch
def setup():
    try:
        shutil.rmtree("./Octopath_Traveler")
    except:
        pass
    shutil.copytree("./data/Octopath_Traveler", "Octopath_Traveler")

def cleanup():
    shutil.rmtree("./Engine")
    shutil.rmtree("./Octopath_Traveler")


if __name__ == '__main__':
    main()
