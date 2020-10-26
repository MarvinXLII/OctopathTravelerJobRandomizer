import subprocess
import os

# Experiment: Is it okay to inclue only uexp
os.chdir("./Octopath_Traveler/Content/Paks")
command = ["./UnrealPak.exe", "RandomizedBosses_P.pak", "-Create=../../../Octopath_Traveler/Content/Character/Database/", "-compress"]
subprocess.call(command)
