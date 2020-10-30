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
        # 'seed': 10436062, #random.randint(0, 1e8),
        'seed': random.randint(0, 1e8),
        'skills': True,                      # Shuffles skills
        'skills-one-divine': True,           # - One Divine Skill per Job
        'skills-separate': True,             # - Keeps skills of Base and Advanced jobs separate
        'costs': True,                       # Random JP costs of skills
        'support': True,                     # Shuffles support skills
        'support-EM': True,                  # - Ensures Evasive Maneuvers is in the first slot
        'stats': True,                       # Shuffles Job bonus stats
        'items': True,                       # Shuffles hidden items and chests
        'items-option': 'items-all',         # - shuffled together
        # 'items-option': 'items-separate',  # - shuffled separately
        'no-thief-chests': True,             # Purple chests turn to brown chests
        'output': os.getcwd(),
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
