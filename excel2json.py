import xlrd
import os
import sys
import hjson

def filterRow(row):
    return list(filter(lambda ri: ri != '', row))


filename = './data/jobs.xlsx'
spreadsheet = xlrd.open_workbook(filename)


sheet = spreadsheet.sheet_by_name('Support')
support = {}
for i in range(1, sheet.nrows):
    skill, job, value = sheet.row_values(i)
    support[skill] = {}
    support[skill]['Job'] = job
    support[skill]['Value'] = value

output = 'data/support.json'
with open(output, 'w') as file:
    hjson.dump(support, file, indent=4)
    

sheet = spreadsheet.sheet_by_name('Skills')
skills = {}
for i in range(1, sheet.nrows):
    name, job, weapon, value = sheet.row_values(i)
    skills[name] = {}
    skills[name]['Job'] = job
    skills[name]['Weapon'] = weapon
    skills[name]['Priority'] = value
    skills[name]['Given'] = False

output = 'data/skills.json'
with open(output, 'w') as file:
    hjson.dump(skills, file, indent=4)

