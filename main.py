import subprocess
import os
import shutil

def randomize():
    # Setup
    database = "./Octopath_Traveler/Content/Character/Database/"
    paks = "./Octopath_Traveler/Content/Paks/"
    datafile = "JobData.uexp"
    exefile = "UnrealPak.exe"
    os.makedirs(database)
    os.makedirs(paks)
    shutil.copy2("data/{}".format(datafile), database+'/{}'.format(datafile))
    shutil.copy2("bin/{}".format(exefile), paks+'/{}'.format(exefile))
    os.chdir(paks)

    unrealPak = "./UnrealPak.exe"
    target = "../../../Octopath_Traveler/Content/Character/Database/"
    patch = "JobData_P.pak"
    outputDir = "../../.."
    
    command = [unrealPak, patch, "-Create={}".format(target), "-compress"]
    subprocess.call(command)

    shutil.copy2(patch, outputDir)
    os.chdir(outputDir)
    shutil.rmtree("./Engine")
    shutil.rmtree("./Octopath_Traveler")

    # Cleanup -- remove temporary directories

    
if __name__ == '__main__':
    randomize()
