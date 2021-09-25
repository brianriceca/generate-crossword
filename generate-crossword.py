#!/usr/bin/env python3
'''
generate-crossword.py: fill a crossword puzzle bracket with random words

usage: generate-crossword.py puzzlefile.json

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
    (direction, cluenumber, wordlength, constraints) = p.random_unsolved_clue()
    if direction is None:
      # puzzle is solved! no more unsolved clues
      return p

    tryword = r.randomword(wordlength, 
                           already_tried_words, 
                           constraints,
                           ababness) 
    if tryword is None:
      # no words in the dictionary fit that haven't been tried
      return None
      
    p2 = p.inscribe_word(tryword, direction, cluelength)
    # the inscribe_word method guarantees it fits

    already_tried_words.append(tryword)

    p3 = solve(p2)
    if p3:
      break

  return p3

    
def main():
  if len(sys.argv) != 2:
    print("usage: {} puzzlefile.json".format(sys.argv[0]))
    sys.exit(1)

  p = Puzzlestate.fromjsonfile(sys.argv[1])

  solve(p)
  p.print()

if __name__ == "__main__":
    main()

