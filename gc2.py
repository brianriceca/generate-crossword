#!/usr/bin/env python3
"""
gc2.py: fill a crossword puzzle bracket with random words

usage: gc2.py puzzlefile.json
"""

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

def solve(puzzle,recursion_depth):
  """
  attempt to find a word that fits into one item in puzzle and then
  recursively solve the puzzle with that word inserted
  if we fail, then try a different item instead
  """

  puzzle2 = None
  wf = Wordfountain(seed=0)

  #puzzle.export_puzzlestate()

  l = puzzle.incomplete_items()
  def _wordlength(w):
    return l[w]['wordlength']

  itemlist = sorted(l, key=_wordlength)

  for thisitem in itemlist:
    itemnumber = thisitem.itemnumber
    direction = thisitem.direction
    if thisitem is None:
      # puzzle is solved! no more incomplete items
      return puzzle
    assert 'wordlength' in l[thisitem], f'incomplete_items[{thisitem}] lacks wordlength'
    wordlength = l[thisitem]['wordlength']
    if 'constraints' in l[thisitem]:
      constraints = l[thisitem]['constraints']
    else:
      constraints = None

    if 'coldspots' in l[thisitem]:
      coldspots = l[thisitem]['coldspots']
    else:
      coldspots = None

    if constraints:
      logging.info(f'r{recursion_depth:03} Trying to solve {itemnumber} {direction} with {repr(constraints)}')
    else:
      logging.info(f'r{recursion_depth:03} Trying to solve {itemnumber} {direction}')

    trywords = wf.matchingwords(wordlength, constraints)
    if len(trywords) == 0:
      # Welp, no words in the dictionary fit
      logging.info(f'{recursion_depth:03} nothing fits {itemnumber} {direction}')
      continue

    trywords =  [ x for x in trywords if x not in puzzle.getwordsused() ]
    if len(trywords) == 0:
      # Welp, no words in the dictionary fit that haven't been tried.
      logging.info(f'{recursion_depth:03} nothing new fits {itemnumber} {direction}')

      continue

    # now we sort trywords so that words that score higher are earlier!

    trywords.sort(key=lambda x: puzzle.score_word(x, direction, itemnumber),reverse=True)

    explored_words_that_fit = set()
    for tryword in trywords:
      tryword_masked = _mask_coldspots(tryword,coldspots)
      if tryword_masked in explored_words_that_fit:
        logging.info(f'{recursion_depth:03} no point in pursuing {tryword}')
        continue
      explored_words_that_fit.add(tryword_masked)
      puzzle2 = puzzle.copy().inscribe_word(tryword, direction, itemnumber)

      if puzzle2 is None:
        raise RuntimeError(f'{recursion_depth:03} tried {tryword} in {itemnumber} {direction}, but it doesnt fit')

      logging.info(f'{recursion_depth:03} {tryword} seems to work in {itemnumber} {direction}!')
      puzzle3 = solve(puzzle2,recursion_depth+1)
      if puzzle3 is None:
        logging.info(f"{recursion_depth:03} the recursive call with {direction} {itemnumber} == {tryword} failed")
        continue
      logging.info(f"{recursion_depth:03} the recursive call with {direction} {itemnumber} == {tryword} came back happy!")
      return puzzle3

  return None
  


def main():
  """fill a crossword puzzle bracket with random words"""
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
  items.sort(key=bylen,reverse=True)

  if completeboard(sofar,0):
    puzzle2.print()
    puzzle2.writesvg('solution.svg',showtitle=True,showcluenumbers=True,showsolvedcells=True)

if __name__ == "__main__":
  main()

def completeboard(sofar,thisitemnumber):
  if thisitemnumber > len(items):
    return True
  trywords = wf.matchingwords(thisitem.length, thisitem.constraints)
  for trythis in trywords:
    sofar.append(Puzzleitem(
    if completeboard(sofar
