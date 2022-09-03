#!/usr/bin/env python3
"""
generate-crossword.py: fill a crossword puzzle bracket with random words

usage: generate-crossword.py puzzlefile.json
"""

import sys
import logging
from os import getpid
from randomword import Randomword
from puzzlestate import Puzzlestate


DEFAULT_PUZZLE = '/Users/brice/generate-crossword/samplepuzzles/baby-animals-crossword.ipuz'
DEFAULT_WORDSOURCE = 'english1020'

def _checkerboard(row,col):
  if row % 2:
    return col % 2
  else:
    return (col+1) % 2
    
def _mask_coldspots(tryword, coldspots):
  tryword_exploded = [ x for x in tryword ]
  for loc in coldspots:
    tryword_exploded[loc] = "~"
  return ''.join(tryword_exploded)

def solve(puzzle,recursion_depth,wordsource):
  """
  attempt to find a word that fits into one clue in puzzle and then
  recursively solve the puzzle with that clue inserted
  if we fail, then try a different clue instead
  """

  puzzle2 = None
  wordspitter = Randomword(0)

  #puzzle.export_puzzlestate()

  awesomest_first = lambda c: c['wordlength']

  cluelist = sorted(puzzle.unsolved_clues(),key=awesomest_first)

  for thisclue in cluelist:
    if thisclue is None:
      # puzzle is solved! no more unsolved clues
      return puzzle
    cluenumber, direction, wordlength, constraints, coldspots = thisclue

    

    if constraints:
      logging.info(f'r{recursion_depth:03} Trying to solve {cluenumber} {direction} with {repr(constraints)}')
    else:
     logging.info(f'r{recursion_depth:03} Trying to solve {cluenumber} {direction}')

    trywords = wordspitter.randomwords(wordlength,
                                     constraints,
                                     wordsource )
    if len(trywords) == 0:
      # Welp, no words in the dictionary fit
      logging.info(f'{recursion_depth:03} nothing fits {cluenumber} {direction}')
      continue

    trywords =  [ x for x in trywords if x not in puzzle.data['wordsused'] ]
    if len(trywords) == 0:
      # Welp, no words in the dictionary fit that haven't been tried.
      logging.info(f'{recursion_depth:03} nothing new fits {cluenumber} {direction}')

      continue

    # now we sort trywords so that words that score higher are earlier!

    trywords.sort(key=lambda x: puzzle.score_word(x, direction, cluenumber),reverse=True)

    explored_words_that_fit = set()
    for tryword in trywords:
      tryword_masked = _mask_coldspots(tryword,coldspots)
      if tryword_masked in explored_words_that_fit:
        logging.info(f'{recursion_depth:03} no point in pursuing {tryword}')
        continue
      explored_words_that_fit.add(tryword_masked)
      puzzle2 = puzzle.copy().inscribe_word(tryword, direction, cluenumber)

      if puzzle2 is None:
        raise RuntimeError(f'{recursion_depth:03} tried {tryword} in {cluenumber} {direction}, but it doesnt fit')

      logging.info(f'{recursion_depth:03} {tryword} seems to work in {cluenumber} {direction}!')
      puzzle3 = solve(puzzle2,recursion_depth+1,wordsource)
      if puzzle3 is None:
        logging.info(f"{recursion_depth:03} the recursive call with {direction} {cluenumber} == {tryword} failed")
        continue
      logging.info(f"{recursion_depth:03} the recursive call with {direction} {cluenumber} == {tryword} came back happy!")
      return puzzle3

  return None
  


def main():
  """fill a crossword puzzle bracket with random words"""
  logging.basicConfig(filename=f'/tmp/generate-crossword-{getpid()}.log',
                    level=logging.INFO)
  infile = DEFAULT_PUZZLE
  wordsource = DEFAULT_WORDSOURCE
  if len(sys.argv) > 3:
    print(f"usage: {sys.argv[0]} puzzlefile.json")
    sys.exit(1)
  if len(sys.argv) > 1:
    infile = sys.argv[1]
    if len(sys.argv) > 2:
      wordsource = sys.argv[2]

  puzzle = Puzzlestate.fromjsonfile(infile)

  puzzle2 = solve(puzzle,0,wordsource)
  puzzle2.print()
  puzzle2.writesvg('solution.svg',showtitle=True,showcluenumbers=True,showsolvedcells=True)

if __name__ == "__main__":
  main()
