import hjson
import binascii
import sys
import shutil
import os
import random
from copy import deepcopy
from Utilities import get_filename


class ABILITIES:
    def __init__(self, abilitySets, abilityData, settings):
        self.abilitySets = abilitySets # BP groups, icons, etc.
        self.abilityData = abilityData # Stats, names, etc.

        # Settings for the skill shuffler
        self.weaponShuffle = settings['skills-weapons']
        self.divineSeparately = settings['skills-one-divine']
        self.advancedSeparately = settings['skills-separate']

        # Use for filtering groups, reorganizing data, adding descriptions, etc.
        with open(get_filename('json/ability.json'),'r') as file:
            self.abilityJSON = hjson.load(file)
        with open(get_filename('json/capture.json'),'r') as file:
            self.captureJSON = hjson.load(file)
        # For checking if job allows for use of that weapon
        with open(get_filename('json/weapons.json'),'r') as file:
            self.jobWeapons = hjson.load(file)

        # Group all the data needed about each set
        self.sets = {}
        self.candidates = {}
        self.capture = {}
        self.modRatio = {}
        self.ratioPercentChange = {}
        for key, data in self.abilitySets.table.items():
            # Get ability names
            abilities = self.abilitySets.getAbilityNames(key)
            # Store data in appropriate dictionary
            if abilities[0] in self.abilityJSON:
                self.sets[key] = {
                    'Job': self.abilityJSON[abilities[0]]['Job'],
                    'Divine': self.abilityJSON[abilities[0]]['Divine'],
                    'Advanced': self.abilityJSON[abilities[0]]['Advanced'],
                    'Weapon': self.abilityJSON[abilities[0]]['Weapon'],
                    'Element': self.abilityJSON[abilities[0]]['Element'],
                    'Priority': self.abilityJSON[abilities[0]]['Priority'],
                    'Swap': None,
                }
                self.candidates[key] = {
                    'Key': key,
                    'Weapon': self.abilityJSON[abilities[0]]['Weapon'],
                    'Element': self.abilityJSON[abilities[0]]['Element'],
                    'Data': data,
                }
                # Store whether or not to mod ratio for job skills
                for ability in abilities:
                    self.modRatio[ability] = self.abilityJSON[ability]['ModRatio']
                # Print/Spoiler logs only
                self.ratioPercentChange[key] = 0
            elif abilities[0] in self.captureJSON:
                self.capture[key] = {
                    'Weapon': self.captureJSON[abilities[0]]['Weapon'],
                    'Element': self.captureJSON[abilities[0]]['Element'],
                    'Icon': self.captureJSON[abilities[0]]['Icon'],
                }
            else:
                # E.g. Exclude Attack, Run, Concoct skills. 
                continue

        # RUNE to ABILITY -- used for identifying ability data to update ratios
        self.runeToAbility = {
            'BT_ABI_397': 'BT_ABI_FIRE',
            'BT_ABI_401': 'BT_ABI_ICE',
            'BT_ABI_405': 'BT_ABI_THUNDER',
            'BT_ABI_409': 'BT_ABI_WIND',
            'BT_ABI_413': 'BT_ABI_LIGHT',
            'BT_ABI_417': 'BT_ABI_DARK',
        }


    def shuffleWithinJob(self, slotKeys):
        table = self.abilitySets.table
        for i, si in enumerate(slotKeys):
            j = random.randrange(i, len(slotKeys))
            sj = slotKeys[j]
            self.sets[si]['Swap'], self.sets[sj]['Swap'] = self.sets[sj]['Swap'], self.sets[si]['Swap']

    def getSkillCandidate(self, slot, candidates):
        weights = []
        job = self.sets[slot]['Job']
        for candidate in candidates:
            weapon = self.candidates[candidate]['Weapon']
            if weapon:
                weights.append(self.jobWeapons[job][weapon])
            else:
               weights.append(True)
        # Get a candidate
        if any(weights):
            return random.choices(candidates, weights)[0]
        else:
            return None
        
    def shuffleSets(self, slotKeys, candidateKeys):
        table = self.abilitySets.table
        random.shuffle(slotKeys)
        for slot in slotKeys:
            # Skil if the slot has been filled
            if self.sets[slot]['Swap']:
                continue

            # Pick a candidate ability set
            candidate = self.getSkillCandidate(slot, candidateKeys)
            if candidate:
                candidateKeys.remove(candidate)
            else: # No candidate
                return False

            # Swap data
            self.sets[slot]['Swap'] = self.candidates[candidate]
            self.isCandAvail[candidate] = False

            # Exit if there are no more candidates left
            if not candidateKeys:
                break

        # Either all candidates got used or all slots were filled!
        return True

    def filterSkills(self, priority=None, divine=False, advanced=False):
        skillset = list(self.sets.keys())
        skillset = filter(lambda key: self.isCandAvail[key], skillset)
        if priority:
            skillset = filter(lambda key: self.sets[key]['Priority'] <= priority, skillset)
        if divine:
            skillset = filter(lambda key: self.sets[key]['Divine'], skillset)
        if advanced:
            skillset = filter(lambda key: self.sets[key]['Advanced'], skillset)
        return list(skillset)

    def shuffleWeapons(self):
        # Keep vanilla distribution of weapon-constrained skills
        keys = list(filter(lambda key: self.sets[key]['Weapon'], self.sets.keys()))
        for i, ki in enumerate(keys):
            j = random.randrange(i, len(keys))
            kj = keys[j]
            self.candidates[ki]['Weapon'], self.candidates[kj]['Weapon'] = self.candidates[kj]['Weapon'], self.candidates[ki]['Weapon']

    def shuffleJobAbilities(self):
        # Build lists of set keys
        initSets = [f"JOB0{i}_ABI_0{j}" for i in range(8) for j in range(1,3)]
        baseSets = [f"JOB0{i}_ABI_0{j}" for i in range(8) for j in range(3,9)]
        divineBaseSets = [f"JOB0{i}_ABI_08" for i in range(8)]
        advancedSets = []
        divineAdvancedSets = []
        for i in range(8, 12):
            x = str(i).rjust(2, '0')
            for j in range(1, 9):
                advancedSets.append( f"JOB{x}_ABI_0{j}" )
            divineAdvancedSets.append( f"JOB{x}_ABI_08" )

        # Loop until all are shuffled
        while True:
            # Reset
            self.isCandAvail = {key:True for key in self.candidates}
            for setData in self.sets.values():
                setData['Swap'] = None

            if self.weaponShuffle:
                self.shuffleWeapons()

            if self.divineSeparately and self.advancedSeparately:
                # Divine skills of advanced jobs only -- must be done first!!!
                slots = list(divineAdvancedSets)
                skills = self.filterSkills(divine=True, advanced=True)
                if not self.shuffleSets(slots, skills):
                    continue
                # Divine skills of base jobs (already filled divine skills of advanced jobs included)
                slots = list(divineBaseSets)
                skills = self.filterSkills(divine=True, advanced=False)
                if not self.shuffleSets(slots, skills):
                    continue
                # base skills of advanced jobs (divine skills include but already filled)
                slots = list(advancedSets)
                skills = self.filterSkills(divine=False, advanced=True)
                if not self.shuffleSets(slots, skills):
                    continue

            elif self.divineSeparately:
                # Shuffle ALL divine skills only
                slots = divineBaseSets + divineAdvancedSets
                skills = self.filterSkills(divine=True)
                if not self.shuffleSets(slots, skills):
                    continue

            elif self.advancedSeparately:
                # Shuffle ALL advanced skills only
                slots = list(advancedSets)
                skills = self.filterSkills(advanced=True)
                if not self.shuffleSets(slots, skills):
                    continue

            # STARTING SKILLS
            slots = list(initSets)
            skills = self.filterSkills(priority=1)
            if not self.shuffleSets(slots, skills):
                continue

            # THE REST
            slots = baseSets + advancedSets
            skills = self.filterSkills(priority=2)
            if not self.shuffleSets(slots, skills):
                continue

            skills = self.filterSkills(priority=3)
            if not self.shuffleSets(slots, skills):
                continue

            skills = self.filterSkills(priority=4)
            if not self.shuffleSets(slots, skills):
                continue

            break

        # SHUFFLE SETS SO DIVINE SKILLS CAN END UP ANYWHERE
        for i in range(8):
            slots = [f'JOB0{i}_ABI_0{j}' for j in range(3, 9)]
            self.shuffleWithinJob(slots)
        for i in range(8, 12):
            x = str(i).rjust(2, '0')
            slots = [f'JOB{x}_ABI_0{j}' for j in range(1, 9)]
            self.shuffleWithinJob(slots)

        # Patch all set data with swapped data
        for key, setData in self.sets.items():
            self.abilitySets.table[key] = setData['Swap']['Data']
            # Update all abilities with a weapon as needed
            if setData['Swap']['Weapon']:
                abilityKeys = self.abilitySets.getAbilityNames(key)
                oldWeapon = self.sets[setData['Swap']['Key']]['Weapon']
                newWeapon = setData['Swap']['Weapon']
                for ability in abilityKeys:
                    self.abilityData.patchWeapon(ability, setData['Swap']['Weapon'])
                    self.abilityData.patchPhysicalDetail(ability, oldWeapon, newWeapon)

    def getCompatibleCapture(self, slot, candidates):
        weights = []
        weapon = self.sets[slot]['Weapon']
        element = self.sets[slot]['Element']
        for candidate in candidates:
            candWeap = self.capture[candidate]['Weapon']
            candElem = self.capture[candidate]['Element']
            boolVal = weapon == candWeap and element == candElem
            weights.append(boolVal)
        if any(weights):
            return random.choices(candidates, weights)[0]
        else:
            return None
                    
    def randomCaptureSkills(self):
        # Loop over all keys rather than sample a set of keys.
        # It **might** be possible to have no candidates for a slot.
        keys = list(self.sets.keys())
        random.shuffle(keys)
        candidates = list(self.capture.keys())
        swaps = {}
        count = random.randrange(8, 17)
        while count:
            slot = keys.pop()
            # Cannot overwrite Hired Help (abilities BT_ABI_025,.... seemed to be hard coded as calling HH rather than using the ability table)
            if self.abilitySets.getAbilityNames(slot)[0] == 'BT_ABI_025':
                continue
            # Get and store suitable candidate
            candidate = self.getCompatibleCapture(slot, candidates)
            if candidate:
                swaps[slot] = candidate
                candidates.remove(candidate)
                count -= 1

        # Update ability data rather than set to preserve skills from H'aanit's Capture
        for slot, candidate in swaps.items():
            # Menu Icons
            icon = self.capture[candidate]['Icon']
            self.abilitySets.patchMenuIcon(slot, icon)
            # Ability data
            slotAbil = self.abilitySets.getAbilityNames(slot)
            candAbil = self.abilitySets.getAbilityNames(candidate)
            # Patch skills with capture skills
            for sa, ca in zip(slotAbil, candAbil):
                # Overwrite ability
                detailName = self.abilityData.getDetailName(sa) # Not all BT_ABI_DETAIL_4??? exist; use that of overwritten ability
                self.abilityData.table[sa] = deepcopy(self.abilityData.table[ca])
                self.abilityData.patchDetailName(sa, detailName)
                # Overwrite SP costs
                self.abilityData.patchSP(sa, self.captureJSON[ca]['SP'])
                # Add description
                self.abilityData.patchDetail(sa, self.captureJSON[ca]['Description'])
                # Patch ratio
                self.abilityData.patchRatio(sa, self.captureJSON[ca]['Ratio'])
                # Overwrite modRatio
                self.modRatio[sa] = self.captureJSON[ca]['ModRatio']


    def randomSP(self):
        for key in self.sets:
            abilities = self.abilitySets.getAbilityNames(key)
            cost = self.abilityData.getSP(abilities[0])
            change = round(0.5 + cost * random.random() * 0.3)
            change *= 1 if random.random() > 0.5 else -1
            cost += change
            for ability in abilities:
                self.abilityData.patchSP(ability, cost)
            
    def randomRatio(self):
        def updateRatio(ability, value, sign):
            ratio = self.abilityData.getRatio(ability)
            change = round(0.5 + ratio * value)
            ratio += sign*change
            self.abilityData.patchRatio(ability, ratio)
        
        for key in self.sets:
            value = random.random() * 0.3
            sign = 1 if random.random() > 0.5 else -1
            abilities = self.abilitySets.getAbilityNames(key)
            if self.modRatio[abilities[0]]:
                self.ratioPercentChange[key] = sign * int(100*value)
            else:
                self.ratioPercentChange[key] = None
            if abilities[0] in self.runeToAbility:
                ability = self.runeToAbility[abilities[0]]
                updateRatio(ability, value, sign)
            else:
                for ability in abilities:
                    if self.modRatio[ability]:
                        updateRatio(ability, value, sign)

    def printLog(self, path):
        jobs = [
            'Merchant', 'Thief', 'Warrior', 'Hunter',
            'Cleric', 'Dancer', 'Scholar', 'Apothecary',
            'Warmaster', 'Sorcerer', 'Starseer', 'Runelord',
        ]
        
        fileName = os.path.join(path, 'spoiler_job_skills.log')
        with open(fileName, 'w') as file:
            file.write('============\n')
            file.write(' JOB SKILLS \n')
            file.write('============\n')
            file.write('\n')

            for i, job in enumerate(jobs):
                file.write(job+'\n')
                file.write('-'*len(job)+'\n\n')
                file.write(' '*32 + 'Weapon'.rjust(10, ' ') + 'SP'.rjust(10, ' ') + 'Power Change'.rjust(15, ' ') + '\n\n')
                
                x = str(i).rjust(2,'0')
                keys = [f"JOB{x}_ABI_0{j}" for j in range(1,9)]
                for key in keys:
                    ability = self.abilitySets.getAbilityNames(key)[0]
                    name = self.abilityData.getDisplay(ability)
                    file.write('  '+name.ljust(30, ' '))
                    
                    weapon = self.abilityData.getWeapon(ability)
                    if weapon:
                        file.write(weapon.rjust(10, ' '))
                    else:
                        file.write(' '*10)
                        
                    cost = self.abilityData.getSP(ability)
                    file.write(str(cost).rjust(10, ' '))

                    ratio = self.ratioPercentChange[key]
                    if ratio is None:
                        file.write('---'.rjust(15, ' '))
                    else:
                        file.write(f"{ratio}%".rjust(15, ' '))
                    file.write('\n')
                file.write('\n\n\n')
