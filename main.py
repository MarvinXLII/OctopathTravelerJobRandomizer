import subprocess
import os
import shutil
import sys
sys.path.append('src')
import JobData

# Build paths for generating patch
def setup():
    try:
        shutil.rmtree("./Octopath_Traveler")
    except:
        pass
    shutil.copytree("./data/Octopath_Traveler", "Octopath_Traveler")

def generatePatch():
    cwd = os.getcwd()

    database = "./Octopath_Traveler/Content/Character/Database/"
    datafile = "JobData.uexp"

    paks = './Octopath_Traveler/Content/Paks/'
    unrealPak = "./UnrealPak.exe"
    target = "../../../Octopath_Traveler/Content/Character/Database/"
    patch = "JobData_P.pak"

    # Generate the patch
    os.chdir(paks)
    command = [unrealPak, patch, "-Create={}".format(target), "-compress"]
    subprocess.call(command)
    shutil.copy2(patch, cwd)
    os.chdir(cwd)

def cleanup():
    shutil.rmtree("./Engine")
    shutil.rmtree("./Octopath_Traveler")


def randomize():

    # Setup
    file = "./Octopath_Traveler/Content/Character/Database/JobData.uexp"
    JobData.shuffleData(file)

    
if __name__ == '__main__':
    setup()
    randomize()
    generatePatch()
    cleanup()
