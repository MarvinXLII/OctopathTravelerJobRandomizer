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
        'skills-one-divine': False,
        'skills-separate': False,
        'skills-weapons': True,
        'skills-sp-costs': True,
        'skills-jp-costs': True,
        'skills-power': True,
        'support': True,
        'support-separate': True,
        'support-EM': True,
        'stats': True,
        # 'stats-option': 'random',
        'stats-option': 'fairly',
        'items': True,
        'items-option': 'items-all',
        # 'items-option': 'items-separate',
        'no-thief-chests': True,
        'output': '',
    }

    setup()
    randomize(settings)
    # cleanup()

# Build paths for generating patch
def setup():
    try: shutil.rmtree("./Octopath_Traveler")
    except: pass
    try: shutil.rmtree("./Engine")
    except: pass
    # shutil.unpack_archive("./data/data.tar.bz2", ".", "bztar")

def cleanup():
    shutil.rmtree("./Engine")
    shutil.rmtree("./Octopath_Traveler")


if __name__ == '__main__':
    main()
