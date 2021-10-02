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

def solve(p):
  r = Randomword(0)

  #p.export_puzzlestate()
    
  already_tried_words = list()
  while True:
    direction, cluenumber, wordlength, constraints = p.random_unsolved_clue()
    if direction is None:
      # puzzle is solved! no more unsolved clues
      return p

    tryword = r.randomword(wordlength, 
                           already_tried_words, 
                           constraints,
                           ababness) 
    if tryword is None:
      # Welp, no words in the dictionary fit that haven't been tried.
      return None
      
    p2 = p.copy().inscribe_word(tryword, direction, cluenumber, cluelength)
    # The inscribe_word method will crash if for some reason
    # the word to be inscribed does not fit.
    # The method also removes the inscribed clue from the list of unsolved 
    # clues.

    already_tried_words.append(tryword)

    if solve(p2):
      break

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
    infile = '/Users/brice/generate-crossword/puzzles/baby-animals-crossword.json'

  p = Puzzlestate.fromjsonfile(infile)

  solve(p)
  p.print()

if __name__ == "__main__":
    main()

