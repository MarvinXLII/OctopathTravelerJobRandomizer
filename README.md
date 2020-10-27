**ABOUT**

This is the beginnings of a Job randomizer for Octopath Traveler (Steam version).

**OPTIONS**

Several options are available:

- Skills: shuffles all skills among jobs.

- Costs: shuffles the JP costs of skills (NB: these will be sorted in increasing order).

- Support Skills: shuffles support skills among jobs.

- Stat bonuses: shuffles each stat among the 8 PCs.

- Item shuffler: shuffles hidden items and treasure chests.

**FUTURE WORK**

Future releases will hopefully include:

- Shuffling/randomizing equippable weapons (currently leads to
  in-battle side-effects at the moment).

- Shuffling base Jobs of the PCs.

- Other random stuff!

Don't forget to check out
[mastermind1919's](https://github.com/mastermind1919/OctopathBossRandomizer)
boss randomizer! They should be compatible!

**Usage**

Run the executable from the Releases section. When finished, copy the
"JobData_P.pak" and "Items_P.pak" into the "Paks" folder in you game,
typically located at "C:\Program Files
(x86)\Steam\steamapps\common\OCTOPATH
TRAVELER\Octopath_Traveler\Content\Paks".

If you prefer to run the code, you'll have to install Python 3.6+ and `hjson`. 
Settings can be set in the `main.py` file, and can be run with `python main.py`.
If you would prefer to use the gui, you must build it yourself. Install `pyinstaller`
 and run `pyinstaller gui.spec`.
