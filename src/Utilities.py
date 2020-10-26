import sys
import os
import random
from copy import copy
from math import ceil

# Load hack using either python or pyinstaller
def get_filename(relative_path):
    if os.path.isfile(relative_path):
        filename = relative_path
    else:
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(base_path, relative_path)
    return filename
