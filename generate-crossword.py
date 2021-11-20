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

#logging.basicConfig(filename=f'/tmp/generate-crossword-{getpid()}.log',
#                    level=logging.DEBUG)

def logit(how_much_to_indent,*args):
  """
  wrapper around logging call with numerically controlled indention

  TODO: maybe replace with decorator?
  """
  msg = ' ' * how_much_to_indent + ' '.join(args)
  logging.info(msg)

DEFAULT_PUZZLE = '/Users/brice/generate-crossword/puzzles/baby-animals-crossword.ipuz'
DEFAULT_WORDSOURCE = 'english1020'

def _mask_coldspots(tryword, coldspots):
  tryword_exploded = [ x for x in tryword ]
  for loc in coldspots:
    tryword_exploded[loc] = "~"
  return ''.join(tryword_exploded)

def solve(puzzle,recursion_depth,wordsource):
  """
  attempt to find a word that fits into one clue in puzzle and then
  recursively solve the puzzle with that clue inserted
  """

  puzzle2 = None
  wordspitter = Randomword(0)

  #puzzle.export_puzzlestate()

  thisclue = puzzle.random_unsolved_clue()
  if thisclue is None:
    # puzzle is solved! no more unsolved clues
    return puzzle
  direction, cluenumber, wordlength, constraints, coldspots = thisclue

  if constraints:
    logit(recursion_depth, f'Trying to solve {cluenumber} {direction} with {repr(constraints)}')
  else:
    logit(recursion_depth, f'Trying to solve {cluenumber} {direction}')

  trywords = wordspitter.randomwords(wordlength,
                                     constraints,
                                     wordsource )
  if len(trywords) == 0:
    # Welp, no words in the dictionary fit
    logit(recursion_depth, f'Dang, nothing fits {cluenumber} {direction}')
    return None

  trywords =  [ x for x in trywords if x not in puzzle.data['wordsused'] ]
  if len(trywords) == 0:
    # Welp, no words in the dictionary fit that haven't been tried.
    logit(recursion_depth, f'Dang, nothing new fits {cluenumber} {direction}')
    return None

  # now we sort trywords so that words that score higher are earlier!

  trywords.sort(key=lambda x: puzzle.score_word(x, direction, cluenumber),reverse=True)

  paths_already_explored = set()
  for tryword in trywords:
    tryword_masked = _mask_coldspots(tryword,coldspots)
    if tryword_masked in paths_already_explored:
      logit(recursion_depth,f'hey, no point in pursuing {tryword}')
      continue
    paths_already_explored.add(tryword_masked)
    puzzle2 = puzzle.copy().inscribe_word(tryword, direction, cluenumber)

    if puzzle2 is None:
      logit(recursion_depth,
            f'I tried {tryword} in {cluenumber} {direction}, but it doesnt fit')
      continue

#   puzzle2.settitle(f'Depth {recursion_depth}')
    logit(recursion_depth, f'{tryword} seems to work in {cluenumber} {direction}!')
    puzzle3 = solve(puzzle2,recursion_depth+1,wordsource)
    if puzzle3 is None:
      logit(recursion_depth,
            f"Bummer, the recursive call with {direction} {cluenumber} == {tryword} failed")
      continue
    logit(recursion_depth,
          f"The recursive call with {direction} {cluenumber} == {tryword} came back happy!")
    return puzzle3


def main():
  """fill a crossword puzzle bracket with random words"""
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
