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

def completeboard(sofar,thisitemnumber):
  global puzzle
  global items

  if thisitemnumber == len(items):
    return SUCCESS # we havin steak tonight

  # OK! If we are N recursions in, that means we are going to try to 
  # find a word to fill in the N'th item in items.
  target_item = items[thisitemnumber]

  logging.info(f'r{thisitemnumber:03} Trying to solve {target_item}')

  # Let's iterate through how we got here, looking for words already
  # inscribed that create a constraint for us.
  constraints = list()
  intersectors = puzzle.getintersectors(target_item)
  if intersectors is not None:
    for histentry in sofar:  #histentries look like ("5 Across","Maple")
      i,w = histentry
      if i in intersectors:
        # uh oh, we have to extract a constraint
          native_charcount, foreign_charcount = intersectors[i]
          constraints.append( ( native_charcount, w[foreign_charcount]) )

  if len(constraints) > 0:
    logging.info(f'... r{thisitemnumber:03} with {repr(constraints)}')

  trywords = wf.matchingwords(puzzle.getlength(target_item), constraints)
  if len(trywords) == 0:
    return ABORT
  for trythis in trywords:
    # OK, let's recurse with this candidate word! Will it work?!
    logging.info(f'... r{thisitemnumber:03} letz try {trythis}')
    sofar.append( (target_item,trythis) )
    if (retval := completeboard(sofar,thisitemnumber+1)) == SUCCESS:
      return SUCCESS # yay!
    elif retval == ABORT:
      logging.info(f'... r{thisitemnumber:03} whoa guess {trythis} was a dead end')
      sofar.pop()
      break
    # well crap, forget about this word and try again with the next
    logging.info(f'... r{thisitemnumber:03} bummer, giving up on {trythis}')
    sofar.pop()
  # if we make it here, that means all the candidate words were failures
  logging.info(f'... r{thisitemnumber:03} bigtime bummer, I used up all the words')
  return FAILURE




puzzle = dict()
items = list()
wf = lambda x: x

def main():

  """fill a crossword puzzle bracket with random words"""

  global puzzle
  global items
  global wf

  wf = Wordfountain(seed=0)
  logging.basicConfig(filename=f'/tmp/gc2-{getpid()}.log',
                    level=logging.INFO)
  if len(sys.argv) != 2:
    print(f"usage: {sys.argv[0]} puzzlefile.json ")
    sys.exit(1)
  infile = sys.argv[1]

  puzzle = Puzzlestate.fromjsonfile(infile)

  sofar = list()
  items = list(puzzle.data['items_expanded'])
  bylen = lambda x: puzzle.data['items_expanded'][x]['wordlength']
  byxings = lambda x: len(puzzle.data['items_expanded'][x]['intersectors'])
  items.sort(key=byxings,reverse=True)

  if completeboard(sofar,0) == SUCCESS:
    puzzle.populate_solution_from_changelist(sofar)
    puzzle.print_solution()
    puzzle.writesvg('solution.svg',showtitle=True,showcluenumbers=True,showsolvedcells=True)


if __name__ == "__main__":
  main()
