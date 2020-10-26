import sys
import os

# Required for pyinstaller
def get_filename(relative_path):
    if os.path.exists(relative_path):
        filename = relative_path
    else:
        base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        filename = os.path.join(base_path, relative_path)
    return filename

    
