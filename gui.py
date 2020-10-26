import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import hjson
import random
import os
import shutil
import subprocess
import sys
sys.path.append('src')
from Utilities import get_filename
import JobData

# from Rom import LocalRom
# import zlib


MAIN_TITLE = "Octopath Traveler Randomizer v 0.0.1a"

# Source: https://www.daniweb.com/programming/software-development/code/484591/a-tooltip-class-for-tkinter
class CreateToolTip(object):
    '''
    create a tooltip for a given widget
    '''
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.close)

    def enter(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                      background='white', relief='solid', borderwidth=1,
                      wraplength=200,
                      font=("times", "12", "normal"),
                      padx=4, pady=6,
        )
        label.pack(ipadx=1)

    def close(self, event=None):
        if self.tw:
            self.tw.destroy()


class GuiApplication:
    def __init__(self, settingsFile=''):
        self.master = tk.Tk()
        self.master.geometry('250x280')
        self.master.title(MAIN_TITLE)
        self.initialize_gui(settingsFile)
        self.initialize_settings()
        self.master.mainloop()


    def initialize_gui(self, settingsFile=''):

        self.settings = {}
        self.warnings = []
        self.togglers = []

        with open(get_filename('./data/parameters.json'), 'r') as file:
            fields = hjson.loads(file.read())

        lf = tk.LabelFrame(self.master, text='')
        lf.grid(row=0, columnspan=2, sticky='nsew', padx=5, pady=5, ipadx=5, ipady=5)

        self.settings['seed'] = tk.IntVar()
        self.randomSeed()
        tk.Label(lf, text='Seed:').grid(row=0, column=0, sticky='w', padx=40)
        box = tk.Spinbox(lf, from_=0, to=1e8, width=9, textvariable=self.settings['seed'])
        box.grid(row=0, column=0, sticky='e', padx=40)
        
        seedBtn = tk.Button(lf, text='Random Seed', command=self.randomSeed)
        seedBtn.grid(row=1, column=0, columnspan=1, sticky='we', padx=30, ipadx=30)

        randomizeBtn = tk.Button(lf, text='Randomize', command=self.randomize)
        randomizeBtn.grid(row=2, column=0, columnspan=1, sticky='we', padx=30, ipadx=30)

        # Tabs setup
        tabControl = ttk.Notebook(self.master)
        tabNames = list(fields.keys())
        tabs = {name: ttk.Frame(tabControl) for name in tabNames}
        for name, tab in tabs.items():
            tabControl.add(tab, text=name)
        tabControl.grid(row=1, column=0, columnspan=20, sticky='news')
        # tabControl.pack(expand=1, fill='both')

        # Tab label
        labelfonts = ('Helvetica', 14, 'bold')
        for name, tab in tabs.items():
            labelDict = fields[name]
            for i, (key, value) in enumerate(labelDict.items()):
                # Setup LabelFrame
                lf = tk.LabelFrame(tab, text=key, font=labelfonts)
                lf.grid(row=i//4, column=i%4, padx=10, pady=5, ipadx=30, ipady=5, sticky='news')
                # Loop over buttons
                # -- maybe do this in a separate function that returns the button?
                # -- then apply its grid here
                row = 0
                for vj in value:
                    name = vj['name']

                    if vj['type'] == 'checkbutton':
                        self.settings[name] = tk.BooleanVar()
                        button = ttk.Checkbutton(lf, text=vj['label'], variable=self.settings[name])
                        button.grid(row=row, padx=10, sticky='we')
                        self.buildToolTip(button, vj)
                        row += 1

                    elif vj['type'] == 'spinbox':
                        text = f"{vj['label']}:".ljust(20, ' ')
                        ttk.Label(lf, text=text).grid(row=row, column=0, padx=10, sticky='w')
                        spinbox = vj['spinbox']
                        self.settings[name] = tk.IntVar()
                        self.settings[name].set(spinbox['default'])
                        box = tk.Spinbox(lf, from_=spinbox['min'], to=spinbox['max'], width=3, textvariable=self.settings[name], state='readonly')
                        box.grid(row=row, column=2, padx=10, sticky='we')
                        self.buildToolTip(box, vj)
                        row += 1

                    elif vj['type'] == 'radiobutton':
                        self.settings[name] = tk.BooleanVar()
                        buttons = []
                        toggleFunction = self.toggler(buttons, name)
                        button = ttk.Checkbutton(lf, text=vj['label'], variable=self.settings[name], command=toggleFunction)
                        button.grid(row=row, padx=10, sticky='we')
                        self.buildToolTip(button, vj)
                        self.togglers.append(toggleFunction)
                        row += 1
                        keyoption = name+'-option'
                        self.settings[keyoption] = tk.StringVar()
                        self.settings[keyoption].set(None)
                        for ri in vj['radio']:
                            radio = tk.Radiobutton(lf, text=ri['label'], variable=self.settings[keyoption], value=ri['value'], padx=15, state=tk.DISABLED)
                            radio.grid(row=row, padx=10, sticky='w')
                            self.buildToolTip(radio, ri)
                            buttons.append(radio)
                            row += 1

        # For warnings/text at the bottom
        self.canvas = tk.Canvas()
        self.canvas.grid(row=6, column=0, columnspan=20, pady=10)


    def toggler(self, lst, key):
        def f():
            if self.settings[key].get():
                for li in lst:
                    li.config(state=tk.NORMAL)
            else:
                for li in lst:
                    li.config(state=tk.DISABLED)
        return f

    def buildToolTip(self, button, field):
        if 'help' in field:
            CreateToolTip(button, field['help'])

    def initialize_settings(self):
        for si in self.settings.values():
            # Set here because ttk will set light-blue, but unchecked, checkboxes as defaults
            # This ensures the boxes are blank.
            if type(si.get()) == bool:
                si.set(False)

    def bottomLabel(self, text, fg, row):
        L = tk.Label(self.canvas, text=text, fg=fg)
        L.grid(row=row, columnspan=20)
        self.warnings.append(L)
        self.master.update()

    def clearBottomLabels(self):
        while self.warnings != []:
            warning = self.warnings.pop()
            warning.destroy()
        self.master.update()
        
    def randomSeed(self):
        self.settings['seed'].set(random.randint(0, 1e8))

    def randomize(self, settings=None):
        # Setup settings
        if settings is None:
            settings = { key: value.get() for key, value in self.settings.items() }

        self.clearBottomLabels()
        self.bottomLabel('Randomizing....', 'blue', 0)

        try:
            randomize(settings)
            self.clearBottomLabels()
            self.bottomLabel('Randomizing...done! Good luck!', 'blue', 0)
        except:
            self.clearBottomLabels()
            self.bottomLabel('Randomizing failed.', 'red', 0)


def randomize(settings):

    #############
    # Randomize #
    #############

    file = "./Octopath_Traveler/Content/Character/Database/JobData.uexp"
    JobData.shuffleData(file, settings)

    ##################
    # Generate Patch #
    ##################

    paks = './Octopath_Traveler/Content/Paks/'
    unrealPak = "./UnrealPak.exe"
    patch = "JobData_P.pak"
    target = "../../../Octopath_Traveler/Content/Character/Database/"

    cwd = os.getcwd()
    os.chdir(get_filename(paks))
    command = [unrealPak, patch, f"-Create={target}", "-compress"]
    subprocess.call(command)
    shutil.copy2(patch, cwd)
    os.chdir(cwd)


if __name__ == '__main__':
    GuiApplication()
