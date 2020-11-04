import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from release import RELEASE
import hjson
import random
import os
import shutil
import subprocess
import sys
sys.path.append('src')
from Utilities import get_filename
import Ability
import JobData
import Items
import ROM
import Text
import PC


MAIN_TITLE = f"Octopath Traveler Randomizer v{RELEASE}"

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
    def __init__(self, settings=None):
        self.master = tk.Tk()
        self.master.geometry('690x550')
        self.master.title(MAIN_TITLE)
        self.initialize_gui()
        self.initialize_settings(settings)
        self.master.mainloop()


    def initialize_gui(self):

        self.warnings = []
        self.togglers = []
        self.settings = {}
        self.settings['release'] = tk.StringVar()
        self.settings['release'].set(RELEASE)

        with open(get_filename('./data/parameters.json'), 'r') as file:
            fields = hjson.loads(file.read())

        labelfonts = ('Helvetica', 14, 'bold')
        lf = tk.LabelFrame(self.master, text='Output Folder', font=labelfonts)
        lf.grid(row=0, columnspan=2, sticky='nsew', padx=5, pady=5, ipadx=5, ipady=5)

        # Specify output directory
        self.settings['output'] = tk.StringVar()
        self.settings['output'].set('')
        # Find Paks directory
        if os.name == 'nt': # Windows
            paths = [
                "C:/Program Files (x86)/Steam/steamapps/common/OCTOPATH_TRAVELER/Octopath_Traveler/Content/Paks",
                "C:/Program Files (x86)/Steam/steamapps/common/OCTOPATH TRAVELER/Octopath_Traveler/Content/Paks",
                "C:/Program Files (x86)/Steam/Steamapps/common/OCTOPATH_TRAVELER/Octopath_Traveler/Content/Paks",
                "C:/Program Files (x86)/Steam/Steamapps/common/OCTOPATH TRAVELER/Octopath_Traveler/Content/Paks",
                "C:/Program Files (x86)/Steam/steamapps/Common/OCTOPATH_TRAVELER/Octopath_Traveler/Content/Paks",
                "C:/Program Files (x86)/Steam/steamapps/Common/OCTOPATH TRAVELER/Octopath_Traveler/Content/Paks",
                "C:/Program Files (x86)/Steam/Steamapps/Common/OCTOPATH_TRAVELER/Octopath_Traveler/Content/Paks",
                "C:/Program Files (x86)/Steam/Steamapps/Common/OCTOPATH TRAVELER/Octopath_Traveler/Content/Paks",
            ]
            for path in paths:
                if not self.checkPath(path): continue
                self.settings['output'].set(path)
                break

        pathLabel = tk.Label(lf, text='Path to "Paks" folder (optional)')
        pathLabel.grid(row=1, column=0, sticky='w', padx=5, pady=2)

        pathToPak = tk.Entry(lf, textvariable=self.settings['output'], width=65, state='readonly')
        pathToPak.grid(row=0, column=0, columnspan=2, padx=(10,0), pady=3)

        pathButton = tk.Button(lf, text='Browse ...', command=self.getPakPath, width=20) # needs command..
        pathButton.grid(row=1, column=1, sticky='e', padx=5, pady=2)

        lf = tk.LabelFrame(self.master, text="Seed", font=labelfonts)
        lf.grid(row=0, column=2, columnspan=2, sticky='nsew', padx=5, pady=5, ipadx=5, ipady=5)
        self.settings['seed'] = tk.IntVar()
        self.randomSeed()
        # tk.Label(lf, text='Seed:').grid(row=2, column=0, sticky='w', padx=60, pady=10)
        box = tk.Spinbox(lf, from_=0, to=1e8, width=9, textvariable=self.settings['seed'])
        box.grid(row=2, column=0, sticky='e', padx=60)

        seedBtn = tk.Button(lf, text='Random Seed', command=self.randomSeed, width=12, height=1)
        seedBtn.grid(row=3, column=0, columnspan=1, sticky='we', padx=30, ipadx=30)

        self.randomizeBtn = tk.Button(lf, text='Randomize', command=self.randomize, height=1)
        self.randomizeBtn.grid(row=4, column=0, columnspan=1, sticky='we', padx=30, ipadx=30)

        # Tabs setup
        tabControl = ttk.Notebook(self.master)
        tabNames = list(fields.keys())
        tabs = {name: ttk.Frame(tabControl) for name in tabNames}
        for name, tab in tabs.items():
            tabControl.add(tab, text=name)
        tabControl.grid(row=2, column=0, columnspan=20, sticky='news')
        # tabControl.pack(expand=1, fill='both')

        # Tab label
        for name, tab in tabs.items():
            labelDict = fields[name]
            for i, (key, value) in enumerate(labelDict.items()):
                row = 0    # i//4
                column = i # i%4
                # Setup LabelFrame
                lf = tk.LabelFrame(tab, text=key, font=labelfonts)
                lf.grid(row=row, column=column, padx=10, pady=5, ipadx=30, ipady=5, sticky='news')
                # Loop over buttons
                # -- maybe do this in a separate function that returns the button?
                # -- then apply its grid here
                row = 0
                for vj in value:
                    name = vj['name']

                    if vj['type'] == 'checkbutton':
                        self.settings[name] = tk.BooleanVar()
                        buttons = []
                        toggleFunction = self.toggler(buttons, name)
                        button = ttk.Checkbutton(lf, text=vj['label'], variable=self.settings[name], command=toggleFunction)
                        button.grid(row=row, padx=10, sticky='we')
                        self.togglers.append(toggleFunction)
                        self.buildToolTip(button, vj)
                        row += 1
                        if 'indent' in vj:
                            for vk in vj['indent']:
                                self.settings[vk['name']] = tk.BooleanVar()
                                button = ttk.Checkbutton(lf, text=vk['label'], variable=self.settings[vk['name']], state=tk.DISABLED)
                                button.grid(row=row, padx=30, sticky='w')
                                self.buildToolTip(button, vk)
                                buttons.append(button)
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
                            radio.grid(row=row, padx=14, sticky='w')
                            self.buildToolTip(radio, ri)
                            buttons.append(radio)
                            row += 1

        # For warnings/text at the bottom
        self.canvas = tk.Canvas()
        self.canvas.grid(row=6, column=0, columnspan=20, pady=10)

    def checkPath(self, path):
        if path.split('/')[-1] != 'Paks':
            return False
        name = 'Octopath_Traveler-WindowsNoEditor.pak'
        try:
            for file in os.listdir(path):
                p1 = not os.path.isfile(f"{path}/{file}")
                if p1: continue
                if file == name: return True
        except:
            pass
        return False

    def getPakPath(self):
        self.clearBottomLabels()
        path = filedialog.askdirectory()
        if path == (): return
        if self.checkPath(path):
            self.settings['output'].set(path)
        else:
            self.settings['output'].set('')
            self.bottomLabel('Selected path must lead to the Paks folder.', 'red', 0)
            self.bottomLabel('e.g. ....\OCTOPATH_TRAVELER\Octopath_Traveler\Content\Paks', 'red', 1) 
            self.bottomLabel('Otherwise, check for Pak outputs in the new seed folder.', 'red', 2) 

    def toggler(self, lst, key):
        def f():
            if self.settings[key].get():
                try: lst[0].select()
                except: pass
                for li in lst:
                    li.config(state=tk.NORMAL)
            else:
                for li in lst:
                    try: li.deselect()
                    except: pass
                    li.config(state=tk.DISABLED)
                self.turnBoolsOff()
        return f

    def buildToolTip(self, button, field):
        if 'help' in field:
            CreateToolTip(button, field['help'])

    def turnBoolsOff(self):
        for si in self.settings.values():
            if type(si.get()) == bool:
                si.set(False)
            
    def initialize_settings(self, settings):
        if settings is None:
            self.turnBoolsOff()
            return
        for key, value in settings.items():
            if key == 'output': continue
            self.settings[key].set(value)
        for toggle in self.togglers:
            toggle()

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
        # self.randomizeBtn["state"] = "disabled"

        try:
            randomize(settings)
            self.clearBottomLabels()
            self.bottomLabel('Randomizing...done! Good luck!', 'blue', 0)
        except:
            self.clearBottomLabels()
            self.bottomLabel('Randomizing failed.', 'red', 0)


def randomize(settings):

    #########
    # SETUP #
    #########

    pwd = os.getcwd()
    outdir = f"{pwd}/seed_{settings['seed']}"
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)

    tmpdir = f'{pwd}/tmp_otr_v{RELEASE}'
    if os.path.isdir(tmpdir):
        shutil.rmtree(tmpdir)
    os.mkdir(tmpdir)
        
    tar = get_filename("./data/data.tar.bz2")
    shutil.unpack_archive(tar, tmpdir, "bztar")

    #############
    # Randomize #
    #############

    abilityFile = f"{tmpdir}/Octopath_Traveler/Content/Ability/Database/AbilityData.uexp"
    abilities = Ability.shuffleData(abilityFile, settings, outdir)

    jobFile = f"{tmpdir}/Octopath_Traveler/Content/Character/Database/JobData.uexp"
    jobs = JobData.shuffleData(jobFile, settings, outdir, abilities)

    itemFile= f"{tmpdir}/Octopath_Traveler/Content/Object/Database/ObjectData.uexp"
    items = Items.shuffleItems(itemFile, settings, outdir)

    textDir = f"{tmpdir}/Octopath_Traveler/Content/GameText/Database"
    Text.updateText(textDir, abilities)

    pcDir = f'{tmpdir}/Octopath_Traveler/Content/Character/Database'
    PC.inits(pcDir, settings)

    for ability in abilities.values():
        ability.patch()

    with open(abilityFile, 'wb') as file:
        file.write(ability.data)

    for job in jobs.values():
        job.patch()

    with open(jobFile, 'wb') as file:
        file.write(job.data)
    
    for item in items:
        item.patch()

    with open(itemFile, 'wb') as file:
        file.write(item.data)
    

    ################
    # Generate Pak #
    ################

    patch = "rando_P.pak"
    path = f"{tmpdir}/Octopath_Traveler/Content/Paks"
    ROM.patch(patch, path)

    #######################
    # Copy to Output Path #
    #######################

    if settings['output'] != '':
        shutil.copy2(patch, settings['output'])
    shutil.move(patch, outdir)

    #################
    # Dump Settings #
    #################

    settingsCopy = settings.copy()
    settingsCopy['output'] = ''
    with open(f"{outdir}/settings.json", 'w') as file:
        hjson.dump(settingsCopy, file)

    ###########
    # Cleanup #
    ###########

    shutil.rmtree(tmpdir)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        print('Usage: python gui.py <settings.json>')
    elif len(sys.argv) == 2:
        with open(sys.argv[1], 'r') as file:
            settings = hjson.load(file)
        GuiApplication(settings)
    else:
        GuiApplication()
