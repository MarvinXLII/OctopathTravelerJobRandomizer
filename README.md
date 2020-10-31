**ABOUT**

This is the beginnings of a Job randomizer for Octopath Traveler (Steam version). Check out 
[mastermind1919's](https://github.com/mastermind1919/OctopathBossRandomizer/releases) for a compatible boss randomizer!

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

**Usage**

Run the executable from the [Releases](https://github.com/MarvinXLII/OctopathTravelerJobRandomizer/releases) page. 
When finished, copy the "JobData_P.pak" and "Items_P.pak" from the new seed_### folder into the "Paks" folder in your game,
typically located at "C:\Program Files (x86)\Steam\steamapps\common\OCTOPATH TRAVELER\Octopath_Traveler\Content\Paks".
The executable also allow you to enter this folder manually, which will automatically copy the files to their destination.

If you prefer to run the code, you'll have to install Python 3.6+ and `hjson`. 
Settings can be set in the `main.py` file, and can be run with `python main.py`.
If you would prefer to use the gui, you must build it yourself. Install `pyinstaller`
 and run `pyinstaller gui.spec`.
