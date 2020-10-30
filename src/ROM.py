import os
import shutil
import subprocess
from Utilities import get_filename



def read(data, base, offset, stride, size, num):
    lst = []
    address = base + offset
    for i in range(num):
        b = data[address:address+size]
        lst.append(int.from_bytes(b, byteorder='little', signed=False))
        address += stride

    if num == 1:
        return lst[0]
    return lst

def write(data, lst, base, offset, stride, size):
    if not isinstance(lst, list):
        lst = [lst]
    address = base + offset
    for i, b in enumerate(lst):
        d = b.to_bytes(size, byteorder='little', signed=False)
        data[address:address+size] = d
        address += stride

def patch(filename, target, outdir):
    paks = './Octopath_Traveler/Content/Paks/'
    unrealPak = "./UnrealPak.exe"
    cwd = os.getcwd()
    os.chdir(get_filename(paks))
    command = [unrealPak, filename, f"-Create={target}", "-compress"]
    subprocess.call(command)
    shutil.copy2(filename, outdir)
    os.chdir(cwd)

