#!/usr/bin/env python3
'''
generate-crossword.py: fill a crossword puzzle bracket with random words

usage: generate-crossword.py puzzlefile.json
'''

import sys
import copy

from puzzlestate import Puzzlestate
from randomword import Randomword

ababness = 1.0

def solve(p,recursion_depth):
  r = Randomword(0)

  #p.export_puzzlestate()
    
  attemptno = 0
  while True:
    direction, cluenumber, wordlength, constraints = p.random_unsolved_clue()
    if direction is None:
      # puzzle is solved! no more unsolved clues
      return p

    trywords =  [ x for x in r.randomwords(wordlength, 
                             constraints,
                             ababness) if x not in p.data['wordsused'] ]
    if trywords is None:
      # Welp, no words in the dictionary fit that haven't been tried.
      return None
      
    for tryword in trywords:
      p2 = p.copy().inscribe_word(tryword, direction, cluenumber)
      # The inscribe_word method will crash if for some reason
      # the word to be inscribed does not fit.

      if solve(p2,recursion_depth+1):
        break
      attemptno++

  return p2

    
def main():
  infile = ''
  if len(sys.argv) == 2:
    infile = sys.argv[1]
  else:
#    print("usage: {} puzzlefile.json".format(sys.argv[0]))
#    sys.exit(1)
    pass
  if not infile:
    infile = '/Users/brice/generate-crossword/puzzles/baby-animals-crossword.ipuz'

  p = Puzzlestate.fromjsonfile(infile)

  solve(p,0)
  p.print()

if __name__ == "__main__":
    main()

