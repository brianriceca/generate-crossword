#!/usr/bin/env python3

"""
gc2.py: fill a crossword puzzle bracket with random words

usage: gc2.py puzzlefile.json
"""

import logging
import os.path
import argparse
from os import getpid
from wordfountain import Wordfountain
from puzzlestate import Puzzlestate, Puzzleitem

SUCCESS = 1
NO_WORDS_MATCH = 0
PRUNE_THIS_BRANCH = -1

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

# class puzzlesolution:
#   def __init__(self, itemlist):
#     self.itemlist = itemlist 
#    self.solution_trail = []
#   def shuffle_the_future:
#     where_to_start = len(self.solution_trail)
#     end_of_list = len(self.itemlist)-1
#     for i in reversed(xrange(where_to_start+1, end_of_list)):
#       j = random.randint(startIdx, i)
#       x[i], x[j] = x[j], x[i]

paths_already_explored = set()

def completeboard(sofar,recursiondepth,sparse=False):
  global puzzle
  global items
  global paths_already_explored

  if recursiondepth == len(items):
    return SUCCESS # we havin steak tonight

  # OK! If we are N recursions in, that means we are going to try to
  # find a word to fill in the N'th item in items.
  target_item = items[recursiondepth]
  row,col = puzzle.answerlocation(target_item.itemnumber)

  logging.info("%03d Trying to solve %s", recursiondepth, target_item)

  # Let's iterate through how we got here, looking for words already
  # inscribed that create a constraint for us.
  constraints = list()
  intersectors = puzzle.getintersectors(target_item)
  if intersectors is not None:
    for histentry in sofar:  
      #histentries look like ("5 Across","MAPLE")
      i,w = histentry
      if i in intersectors:
        # uh oh, we might have to extract a constraint
        native_charcount, foreign_charcount = intersectors[i]
        if isinstance(w[foreign_charcount],str):
          assert w[foreign_charcount] != Puzzlestate.BARRIER
          if w[foreign_charcount] != Puzzlestate.UNSET:
            constraints.append( ( native_charcount, w[foreign_charcount]) )

  if len(constraints) > 0:

    # Have we already been down this path? Abort immediately if so.
    lets_explore = f"{recursiondepth} {target_item} {constraints}"
    if lets_explore in paths_already_explored:
      logging.info("%03d already explored %s, aborting",
                 recursiondepth, lets_explore)
      return NO_WORDS_MATCH
    else:
      paths_already_explored.add(lets_explore)

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

  assert len(list_of_dicts) == puzzle.answerlength(target_item), \
     "yer logic is faulty"
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
    return NO_WORDS_MATCH
  trywords.sort(key=_ratewordcandidate,reverse=True)
  for trythis in trywords:
    logging.info("%03d ...let's try %s for %s", 
                recursiondepth, trythis, target_item)
    sofar.append( (target_item,trythis) )
    if (retval := completeboard(sofar,recursiondepth+1)) == SUCCESS:
      return SUCCESS # yay!
    elif retval == NO_WORDS_MATCH:
      logging.info("%03d ...giving up on %s in %s, let's try this again later ", 
                  recursiondepth, trythis, target_item)
      sofar.pop()

  # if we make it here, that means all the candidate words were failures
  # so we have to choose a different word and try again
  logging.info('%03d ...used up all the possible words, going to reshuffle',recursiondepth)
  if recursiondepth + 1 == length(items)
    logging.info('%03d ...nothing to reshuffle, ugh',recursiondepth)
    raise RuntimeError('dang')
  items[recursiondepth], items[recursiondepth+1] = items[recursiondepth+1], items[recursiondepth] 
  return NO_WORDS_MATCH

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
