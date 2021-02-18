**ABOUT**

This is the beginnings of a randomizer for Octopath Traveler (Steam version). Check out 
[mastermind1919's](https://github.com/mastermind1919/OctopathBossRandomizer/releases) for a compatible boss randomizer!

**OPTIONS**

Several options are available:

- Skills: shuffles all skills, weapons, and rescales SP costs and power. Abilities learned from H'aanit's Capture skill can be included in the skill shuffle.

- Costs: adjusts the JP costs of skills.

- Support Skills: shuffles support skills among jobs.

- Stats: shuffles each stat among the 8 PCs as well as stat bonuses from secondary jobs.

- Item shuffler: shuffles hidden items, treasure chests, and those sold by/stolen from NPCs.

- QOL: Miscellaneous options, including starting with the Spurning Ribbon and quickly learning Evasive Maneuvers.

**Usage**

Run the executable from the
[Releases](https://github.com/MarvinXLII/OctopathTravelerJobRandomizer/releases)
page.  When finished, copy the `*_P.pak` files from the new `seed_###`
folder into the `Paks` folder in your game, typically located at
`C:\Program Files (x86)\Steam\steamapps\common\OCTOPATH
TRAVELER\Octopath_Traveler\Content\Paks`.  The executable also allows
you to enter this folder manually, which will automatically copy the
file to its destination.

If you prefer to run the code, you'll have to install Python 3.6+ and
`hjson`.  Settings can be set in the `main.py` file, and the
randomizer can be run with `python main.py`.  If you would prefer to
use the gui, install `tkinter` and run `python gui.py`. You can build
the executable yourself by installing `pyinstaller` and running
`pyinstaller gui.spec`.
