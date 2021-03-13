import os
import random
import hjson
import shutil
import glob
import sys
sys.path.append('src')
from ROM import ROM
from World import WORLD
from gui import randomize

def main(settings, pak):
    # Load ROM
    rom = ROM(pak)

    # Randomize & dump pak
    settings['system'] = 'Steam'
    randomize(rom, settings)

def mainSwitch(settings, fileNames):
    # Load ROM
    fileNames.sort(reverse=True)
    mainPak = fileNames.pop()
    rom = ROM(mainPak, patches=fileNames)

    # Randomize & dump pak
    settings['system'] = 'Switch'
    randomize(rom, settings)
    
    
if __name__=='__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: python main.py settings.json')
    with open(sys.argv[1], 'r') as file:
        settings = hjson.load(file)

    fileNames = glob.glob(settings['rom'] + '/**/*.pak', recursive=True)
    steamFiles = list(filter(lambda x: os.path.basename(x) == 'Octopath_Traveler-WindowsNoEditor.pak', fileNames))
    switchFiles = list(filter(lambda x: os.path.basename(x) == 'Kingship-Switch.pak', fileNames))
    switchFiles += list(filter(lambda x: os.path.basename(x) == 'Kingship-Switch_0_P.pak', fileNames))
    
    if steamFiles:
        main(settings, steamFiles[0])

    if switchFiles:
        mainSwitch(settings, switchFiles)
