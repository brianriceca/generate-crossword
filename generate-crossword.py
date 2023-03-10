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
parser.add_argument('-d', '--db')
parser.add_argument('infile',type=argparse.FileType('r', encoding='latin-1'))

args = parser.parse_args()
infilename = args.infile.name
outfilename = args.output
worddb = args.db

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

words_already_tried = dict()

def completeboard(sofar,recursiondepth,sparse=False):
  global puzzle
  global items
  global words_already_tried

  if recursiondepth == len(items):
    return SUCCESS # we havin steak tonight

  # OK! If we are N recursions in, that means we are going to try to
  # find a word to fill in the N'th item in items.
  target_item = items[recursiondepth]
  row,col = puzzle.answerlocation(target_item.itemnumber)

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
    logging.info(f'r{recursiondepth:03} ...with constraints {repr(constraints)}')

  # 'intersectors' values look like this:
  # {1 Down: (0, 1), 2 Down: (1, 1), 3 Down: (2, 1), 4 Down: (3, 1), 5 Down: (4, 1)}
  intersection_locs = None
  if intersectors is not None:
    intersection_locs = [ intersectors[k][0] for k in intersectors ]
  intersection_locs = set(intersection_locs)

  # constraints values look like this:
  # [(0, 'R'), (1, 'S'), (2, 'R'), (3, 'R'), (4, 'S')]
  constraint_locs = None
  if constraints is not None:
    constraint_locs = [ i[0] for i in constraints ]
  constraint_locs = list(set(constraint_locs)).sort()

  list_of_dicts = list()

  if sparse:
    for i in range(puzzle.answerlength(target_item)):
      if constraint_locs and i in constraint_locs:
        list_of_dicts.append( [ 0 for a in range(26) ])
      elif intersection_locs and i in intersection_locs:
        list_of_dicts.append(Puzzlestate.PREFER_COMMON_LETTERS)
      else:
        list_of_dicts.append(Puzzlestate.SINGLE_LETTER_FREQS)
  else:
    if _checkerboard(row,col):
      prefer_a_vowel = True
    else:
      prefer_a_vowel = False
    for i in range(puzzle.answerlength(target_item)):
      if prefer_a_vowel:
        list_of_dicts.append(Puzzlestate.I_LIKE_VOWELS)
      else:
        list_of_dicts.append(Puzzlestate.I_LIKE_CONSONANTS)
      prefer_a_vowel = not prefer_a_vowel

  assert len(list_of_dicts) == puzzle.answerlength(target_item), "yer logic is faulty"
  def _ratewordcandidate_lambda(vec):
    def _rater(w):
      score = 0
      for i,c in enumerate(w):
        score += vec[i][ord(c)-ord('A')]
      return score
    return _rater

  _ratewordcandidate = _ratewordcandidate_lambda(list_of_dicts)

  trywords = wf.matchingwords(puzzle.getlength(target_item), constraints)
  if len(trywords) == 0:
    return ABORT
  trywords.sort(key=_ratewordcandidate,reverse=True)
  for trythis in trywords:
    if target_item in words_already_tried and trythis in words_already_tried[target_item]:
      logging.info(f"r{recursiondepth:03} ...I have already explored {trythis}")
      break
    # OK, let's recurse with this candidate word! Will it work?!
    logging.info(f"r{recursiondepth:03} ...let's try {trythis} for {target_item}")
    sofar.append( (target_item,trythis) )
    if target_item not in words_already_tried:
      words_already_tried[target_item] = set()
    words_already_tried[target_item].add(trythis)
    if (retval := completeboard(sofar,recursiondepth+1)) == SUCCESS:
      return SUCCESS # yay!
    elif retval == ABORT:
      logging.info(f"r{recursiondepth:03} ...{trythis} was a dead end, caused abort")
      sofar.pop()
      break
    # well crap, forget about this word and try again with the next
    logging.info("%03d ...giving up on %s in %s, on to the next possibility", 
                  recursiondepth, trythis, target_item)
    sofar.pop()
  # if we make it here, that means all the candidate words were failures
  logging.info(f'r{recursiondepth:03} ...used up all the possible words')
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

  sparseness = puzzle.sparseness()
  sofar = list()
  items = list(puzzle.data['items_expanded'])
  bylen = lambda x: puzzle.data['items_expanded'][x]['wordlength']
  byxings = lambda x: len(puzzle.data['items_expanded'][x]['intersectors'])
  items.sort(key=byxings,reverse=True)

  if completeboard(sofar,0,sparse=(sparseness < 0.6)) == SUCCESS:
    puzzle.populate_solution_from_changelist(sofar)
    puzzle.writejson(outfilename)
    print('Just saved to json')
    puzzle.print_solution()
    puzzle.writesvg('solution.svg',showtitle=True,showcluenumbers=True,showsolvedcells=True)


if __name__ == "__main__":
  main()
