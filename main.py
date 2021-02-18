import os
import random
import hjson
import shutil
import sys
sys.path.append('src')
from ROM import ROM
from World import WORLD
from gui import randomize

def main(settings):
    # Load ROM
    rom = ROM(settings['rom'])

    # Randomize & dump pak
    randomize(rom, settings)

if __name__=='__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python main.py settings.json')
    with open(sys.argv[1], 'r') as file:
        settings = hjson.load(file)
    assert os.path.isdir(settings['rom']), "'rom' must lead to Octopath_Traveler-WindowsNoEditor.pak"
    fileName = os.path.join(settings['rom'], 'Octopath_Traveler-WindowsNoEditor.pak')
    assert os.path.isfile(fileName), 'Octopath_Traveler-WindowsNoEditor.pak does not exist'
    main(settings)
