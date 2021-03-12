## ABOUT

This is a randomizer for Octopath Traveler (Steam and Switch versions). Check out 
[mastermind1919](https://github.com/mastermind1919/OctopathBossRandomizer/releases) for a compatible boss randomizer! (compatible with Steam only)

## OPTIONS

Several options are available:

- Skills: shuffles all skills, weapons, and rescales SP costs and power. Abilities learned from H'aanit's Capture skill can be included in the skill shuffle.

- Costs: adjusts the JP costs of skills.

- Support Skills: shuffles support skills among jobs.

- Stats: shuffles each stat among the 8 PCs as well as stat bonuses from secondary jobs.

- Item shuffler: shuffles hidden items, treasure chests, and those sold by/stolen from NPCs.

- QOL: Miscellaneous options, including starting with the Spurning Ribbon and quickly learning Evasive Maneuvers.

## USAGE

Run the executable from the
[Releases](https://github.com/MarvinXLII/OctopathTravelerJobRandomizer/releases)
page.


#### Steam

Load the `Paks` folder and randomize. When finished, copy the
`*_P.pak` files from the new `seed_###` folder into the `Paks` folder
in your game, typically located at `C:\Program Files
(x86)\Steam\steamapps\common\OCTOPATH
TRAVELER\Octopath_Traveler\Content\Paks`.  The executable also
includes and option to copy this file automatically to this location.

#### Switch

Load the `RomFS`. When finished, copy the `romfs` from the new
`seed_###` folder onto your SD card (e.g. on the latest versions of
atmosphere, `atmosphere\content\titleID\`).


#### Code

If you prefer to run the code, you'll have to install Python 3.6+ and
`hjson` and `tkinter`.  Then, run `python gui.py`. You can build
the executable yourself by installing `pyinstaller` and running
`pyinstaller gui.spec`.


## COMPATIBILITY

Note that paks are not compatbile on both Steam and Switch
releases. For any co-op gameplay or races including both systems,
players will need to generate their own patches.

The simplest way to do this is for one player to share their
`settings.json` file in the `seed_###`. This file includes all
selected settings and can be loaded by clicking the file and dragging
it onto the executable.
