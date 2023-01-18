#!/usr/bin/env python3
"""
gc2.py: fill a crossword puzzle bracket with random words

usage: gc2.py puzzlefile.json
"""

SUCCESS = 1
FAILURE = 0
ABORT = -1

import sys
import logging
from os import getpid
from wordfountain import Wordfountain
from puzzlestate import Puzzlestate, Puzzleitem
import os.path
import argparse
import json

parser = argparse.ArgumentParser()
parser.add_argument('-o', '--output')
parser.add_argument('-f', '--force', action='store_true')
parser.add_argument('-d', '--db')
parser.add_argument('infile',type=argparse.FileType('r', encoding='latin-1'))

args = parser.parse_args()
infilename = args.infile.name
outfilename = args.output
worddb = args.db

confdir = os.path.join(os.path.dirname(os.path.realpath(__file__)),"conf")
if not os.path.exists(confdir):
  raise RuntimeError(f'no conf directory at {confdir}')
if not os.path.isdir(confdir):
  raise RuntimeError(f'{confdir} is supposed to be a directory')
conffile = os.path.join(confdir,"crossword.json")
if not os.path.exists(conffile):
  raise RuntimeError(f'missing config file')
with open(conffile,"r") as f:
  config = json.load(f)
with open(os.path.join(confdir,'single_letter_weightings.json')) as f:
  singleletterfreqs = json.load(f)

if worddb is None or worddb == '':
  worddb = config['worddb']
assert isinstance(singleletterfreqs,dict), 'singleletterfreqs needs to be a dict'
nonintersection_weights = { k:config['nonintersection_weight_factor'] * singleletterfreqs[k] for k in singleletterfreqs }
intersection_weights = { k:config['intersection_weight_factor'] * singleletterfreqs[k] for k in singleletterfreqs }
constraint_weights = { k:config['constraint_weight_factor'] * singleletterfreqs[k] for k in singleletterfreqs }


assert infilename is not None

if not os.path.exists(infilename):
  print(f'input file {infilename} doesn\'t exist')
  sys.exit(1)

if outfilename is None:
  if infilename.rfind('.ipuz') == -1:
    outfilename = infilename + '-out.ipuz'
  else:
    outfilename = (infilename[::-1].replace('zupi.','zupi.tou-',1))[::-1]

def _checkerboard(row,col):
  if row % 2:
    return col % 2
  else:
    return (col+1) % 2
    
def _mask_coldspots(tryword, coldspots):
  tryword_exploded = [ x for x in tryword ]
  for loc in coldspots:
    tryword_exploded[loc] = Puzzlestate.COLDSPOT
  return ''.join(tryword_exploded)

def completeboard(sofar,recursiondepth):
  global puzzle
  global items

  if recursiondepth == len(items):
    return SUCCESS # we havin steak tonight

  # OK! If we are N recursions in, that means we are going to try to 
  # find a word to fill in the N'th item in items.
  target_item = items[recursiondepth]

  logging.info(f'r{recursiondepth:03} Trying to solve {target_item}')

  # Let's iterate through how we got here, looking for words already
  # inscribed that create a constraint for us.
  constraints = list()
  intersectors = puzzle.getintersectors(target_item)
  if intersectors is not None:
    for histentry in sofar:  #histentries look like ("5 Across","Maple")
      i,w = histentry
      if i in intersectors:
        # uh oh, we might have to extract a constraint
          native_charcount, foreign_charcount = intersectors[i]
          if isinstance(w[foreign_charcount],str):
            assert w[foreign_charcount] != Puzzlestate.BARRIER
            if w[foreign_charcount] != Puzzlestate.UNSET:
              constraints.append( ( native_charcount, w[foreign_charcount]) )

  if len(constraints) > 0:
    logging.info(f'... r{recursiondepth:03} with {repr(constraints)}')

  # 'intersectors' values look like this:
  # {1 Down: (0, 1), 2 Down: (1, 1), 3 Down: (2, 1), 4 Down: (3, 1), 5 Down: (4, 1)}
  intersection_locs = None
  if intersections is not None:
    intersection_locs = [ intersections[k][0] for k in intersections ]
  intersection_locs = set(intersection_locs)

  # constraints values look like this:
  # [(0, 'R'), (1, 'S'), (2, 'R'), (3, 'R'), (4, 'S')]
  constraint_locs = None
  if constraints is not None:
    constraint_locs = [ i[0] for i in constraints ]
  constraint_locs = list(set(constraint_locs)).sort()
    
  list_of_dicts = list()
  for i,c in enumerate(word):
    if i in constraint_locs:
      list_of_dicts.append(constraint_weights)
    if i in intersection_locs:
      list_of_dicts.append(intersection_weights)
    else:
      list_of_dicts.append(nonintersection_weights)
    
    def _ratewordcandidate(w):
      score = 0
      for i,c in enumerate(w):
        score += vec[i][c]
    return score

  trywords = wf.matchingwords(puzzle.getlength(target_item), constraints)
  if len(trywords) == 0:
    return ABORT
  trywords.sort(key=_ratewordcandidate)
  for trythis in trywords:
    # OK, let's recurse with this candidate word! Will it work?!
    logging.info(f'... r{recursiondepth:03} letz try {trythis}')
    sofar.append( (target_item,trythis) )
    if (retval := completeboard(sofar,recursiondepth+1)) == SUCCESS:
      return SUCCESS # yay!
    elif retval == ABORT:
      logging.info(f'... r{recursiondepth:03} whoa guess {trythis} was a dead end')
      sofar.pop()
      break
    # well crap, forget about this word and try again with the next
    logging.info(f'... r{recursiondepth:03} bummer, giving up on {trythis}')
    sofar.pop()
  # if we make it here, that means all the candidate words were failures
  logging.info(f'... r{recursiondepth:03} bigtime bummer, I used up all the words')
  return FAILURE




puzzle = dict()
items = list()
wf = lambda x: x

def main():

  """fill a crossword puzzle bracket with random words"""

  global puzzle
  global items
  global wf

  wf = Wordfountain(worddb=worddb,seed=0)
  logging.basicConfig(filename=f'/tmp/gc2-{getpid()}.log',
                    level=logging.INFO)

  puzzle = Puzzlestate.fromjsonfile(infilename)

  sofar = list()
  items = list(puzzle.data['items_expanded'])
  bylen = lambda x: puzzle.data['items_expanded'][x]['wordlength']
  byxings = lambda x: len(puzzle.data['items_expanded'][x]['intersectors'])
  items.sort(key=byxings,reverse=True)

  if completeboard(sofar,0) == SUCCESS:
    puzzle.populate_solution_from_changelist(sofar)
    puzzle.writejson(outfilename)
    print('Just saved to json')
    puzzle.print_solution()
    puzzle.writesvg('solution.svg',showtitle=True,showcluenumbers=True,showsolvedcells=True)


if __name__ == "__main__":
  main()
