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
itercount = 0

def solve(p,recursion_depth):
  global itercount

  r = Randomword(0)

  #p.export_puzzlestate()

  p2 = None
    
  attemptno = 0
  thisclue = p.random_unsolved_clue()
  if thisclue is None:
    # puzzle is solved! no more unsolved clues
    return p
  direction, cluenumber, wordlength, constraints = thisclue

  print(' ' * recursion_depth, "Trying to solve {} {}".format(cluenumber,direction))

  trywords =  [ x for x in r.randomwords(wordlength, 
                             constraints,
                             ababness) if x not in p.data['wordsused'] ]
  if trywords is None:
    # Welp, no words in the dictionary fit that haven't been tried.
    print(' ' * recursion_depth, "Dang, nothing fits {} {}".format(cluenumber,direction))
    return None
      
  for tryword in trywords:
    itercount += 1
    attemptno += 1 
    p2 = p.copy().inscribe_word(tryword, direction, cluenumber)

    if p2 is None:
      print(' ' * recursion_depth, "I tried {} in {} {}, but it doesn't fit".format(tryword,cluenumber,direction))
      continue

#    p2.settitle('Count {} Depth {} Attempt {}'.format(itercount,recursion_depth,attemptno))
    print(' ' * recursion_depth, "{} seems to work in {} {}!".format(tryword,cluenumber,direction))
    p3 = solve(p2,recursion_depth+1)
    if p3 is None:
      print(' ' * recursion_depth, "Well that didn't work")
      continue
    print(' ' * recursion_depth, "The recursive call came back happy!")
    return p3
  else: 
    print(' ' * recursion_depth, "I tried all my word choices and none of them worked")
    return None

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

  p2 = solve(p,0)
  p2.print()
  p2.writesvg('solution.svg',showtitle=True,showcluenumbers=True,showsolvedcells=True)

if __name__ == "__main__":
    main()

