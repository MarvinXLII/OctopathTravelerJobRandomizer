**ABOUT**

This is the beginnings of a randomizer for Octopath Traveler (Steam version). Check out 
[mastermind1919's](https://github.com/mastermind1919/OctopathBossRandomizer/releases) for a compatible boss randomizer!

**OPTIONS**

Several options are available:

- Skills: shuffles all skills, weapons, and rescales SP costs and power.

- Costs: adjusts the JP costs of skills.

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
When finished, copy the "*_P.pak" files from the new seed_### folder into the "Paks" folder in your game,
typically located at "C:\Program Files (x86)\Steam\steamapps\common\OCTOPATH TRAVELER\Octopath_Traveler\Content\Paks".
The executable also allows you to enter this folder manually, which will automatically copy the files to their destination.

If you prefer to run the code, you'll have to install Python 3.6+ and `hjson`. 
Settings can be set in the `main.py` file, and the randomizer can be run with `python main.py`.
If you would prefer to use the gui, run `python gui.py` or build it yourself with `pyinstaller gui.spec`.
