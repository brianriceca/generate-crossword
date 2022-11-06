#!/usr/bin/env python3

import sqlite3
import os.path
import sys
import argparse
import unidecode

MAX_TO_INDEX = 8

def _explode_word(word):
  mylist = list(word)
  while len(mylist) < MAX_TO_INDEX:
    mylist.append('_')
  return mylist[:MAX_TO_INDEX]

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output')
parser.add_argument('-f', '--force', action='store_true')
parser.add_argument('infile',type=argparse.FileType('r', encoding='latin-1'))

args = parser.parse_args()
infilename = args.infile.name
outfilename = args.output
print(vars(args))

assert infilename is not None

if not os.path.exists(infilename):
  print(f'input file {infilename} doesn\'t exist')
  sys.exit(1)

if outfilename is None:
  if infilename.rfind('.txt') == -1:
    outfilename = infilename + '.db'
  else:
    outfilename = (infilename[::-1].replace('txt.','bd.',1))[::-1]


print(f'new outfilename is {outfilename}')

if os.path.exists(outfilename) and not args.force:
  print(f'output file {outfilename} exists (-f to clobber)')
  sys.exit(1)
  
print('bye')

con = sqlite3.connect(outfilename)
con.execute('''CREATE TABLE words
               (word text NOT NULL, length INTEGER, 
                c0 TEXT,
                c1 TEXT,
                c2 TEXT,
                c3 TEXT,
                c4 TEXT,
                c5 TEXT,
                c6 TEXT,
                c7 TEXT )''')

sql_ddl = ("INSERT INTO words VALUES (?, ?, " +
           "?, ?, ?, ?, ?, ?, ?, ?)" )

cur = con.cursor()
while True:
  line = unidecode.unidecode(args.infile.readline().strip().upper())
  if not line:
    break
  print(f'writing {line}')
  cur.execute(sql_ddl, (line,len(line), *_explode_word(line)))

con.commit()
con.close()
