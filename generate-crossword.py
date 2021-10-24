#!/usr/bin/env python3
'''
generate-crossword.py: fill a crossword puzzle bracket with random words

usage: generate-crossword.py puzzlefile.json
'''

import sys
import copy
import logging

from os import getpid
pid = getpid()
logging.basicConfig(filename=f'/tmp/generate-crossword-{pid}.log', encoding='utf-8', level=logging.DEBUG)

def logit(*args):
    msg = ' '.join(args)
    logging.info(msg)

from puzzlestate import Puzzlestate
from randomword import Randomword

itercount = 0
wordsource = 'english1020'

def solve(p,recursion_depth):
  global itercount
  global wordsource

  r = Randomword(0)

  #p.export_puzzlestate()

  p2 = None
    
  attemptno = 0
  thisclue = p.random_unsolved_clue()
  if thisclue is None:
    # puzzle is solved! no more unsolved clues
    return p
  direction, cluenumber, wordlength, constraints, preferences, coldspots = thisclue

  if constraints:
    logit(' ' * recursion_depth, "Trying to solve {} {} with {}".format(cluenumber,direction,repr(constraints)))
  else:
    logit(' ' * recursion_depth, "Trying to solve {} {}".format(cluenumber,direction))

  trywords = r.randomwords(wordlength, 
                             constraints,
                             wordsource )
  if trywords is None:
    # Welp, no words in the dictionary fit
    logit(' ' * recursion_depth, "Dang, nothing fits {} {}".format(cluenumber,direction))
    return None  
    
  trywords =  [ x for x in trywords if x not in p.data['wordsused'] ]
  if trywords is None:
    # Welp, no words in the dictionary fit that haven't been tried.
    logit(' ' * recursion_depth, "Dang, nothing new fits {} {}".format(cluenumber,direction))
    return None
      
  # now we sort trywords so that words matching more preferences are earlier!

  if len(preferences) > 0:
    letters_in_the_right_place = dict()
    for w in trywords:
      score = len(w)
      for pref in preferences:
        n, ok_letters = pref
        if w[n] not in ok_letters:
          score -= 1       
      letters_in_the_right_place[w] = (score * 128) // len(w)
    
    trywords.sort(key=lambda x: letters_in_the_right_place[x])

  for tryword in trywords:
    itercount += 1
    attemptno += 1 
    p2 = p.copy().inscribe_word(tryword, direction, cluenumber)

    if p2 is None:
      logit(' ' * recursion_depth, "I tried {} in {} {}, but it doesn't fit".format(tryword,cluenumber,direction))
      continue

#    p2.settitle('Count {} Depth {} Attempt {}'.format(itercount,recursion_depth,attemptno))
    logit(' ' * recursion_depth, "{} seems to work in {} {}!".format(tryword,cluenumber,direction))
    p3 = solve(p2,recursion_depth+1)
    if p3 is None:
      logit(' ' * recursion_depth, "Well that didn't work")
      continue
    logit(' ' * recursion_depth, "The recursive call came back happy!")
    return p3
  else: 
    logit(' ' * recursion_depth, "I tried all my word choices and none of them worked")
    return None

  return p2

def main():
  global wordsource

  infile = '/Users/brice/generate-crossword/puzzles/baby-animals-crossword.ipuz'
  if len(sys.argv) > 3:
    print("usage: {} puzzlefile.json".format(sys.argv[0]))
    sys.exit(1)
  if len(sys.argv) > 1:
    infile = sys.argv[1]
    if len(sys.argv) > 2:
      wordsource = sys.argv[2]

  p = Puzzlestate.fromjsonfile(infile)

  p2 = solve(p,0)
  p2.print()
  p2.writesvg('solution.svg',showtitle=True,showcluenumbers=True,showsolvedcells=True)

if __name__ == "__main__":
    main()

