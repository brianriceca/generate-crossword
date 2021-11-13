#!/usr/bin/env python3
"""
generate-crossword.py: fill a crossword puzzle bracket with random words

usage: generate-crossword.py puzzlefile.json
"""

import sys
import copy
import logging
from os import getpid

from randomword import Randomword
from puzzlestate import Puzzlestate

logging.basicConfig(filename=f'/tmp/generate-crossword-{getpid()}.log',
                    encoding='utf-8', level=logging.DEBUG)

def logit(how_much_to_indent,*args):
  """
  wrapper around logging call with numerically controlled indention

  TODO: maybe replace with decorator?
  """
  msg = ' ' * how_much_to_indent + ' '.join(args)
  logging.info(msg)

itercount = 0
wordsource = 'english1020'

def solve(p,recursion_depth):
  """
  attempt to find a word that fits into one clue in puzzle p and then
  recursively solve the puzzle with that clue inserted
  """
  
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
  direction, cluenumber, wordlength, constraints, preferences = thisclue

  if constraints:
    logit(recursion_depth,
        f'Trying to solve {cluenumber} {direction} with {repr(constraints)}')
  else:
    logit(recursion_depth,
        f'Trying to solve {cluenumber} {direction}')

  trywords = r.randomwords(wordlength,
                             constraints,
                             wordsource )
  if len(trywords) == 0:
    # Welp, no words in the dictionary fit
    logit(recursion_depth, f'Dang, nothing fits {cluenumber} {direction}')
    return None

  trywords =  [ x for x in trywords if x not in p.data['wordsused'] ]
  if len(trywords) == 0:
    # Welp, no words in the dictionary fit that haven't been tried.
    logit(recursion_depth, f'Dang, nothing new fits {cluenumber} {direction}')
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

    trywords.sort(key=lambda x: letters_in_the_right_place[x],reverse=True)

  for tryword in trywords:
    itercount += 1
    attemptno += 1
    p2 = p.copy().inscribe_word(tryword, direction, cluenumber)

    if p2 is None:
      logit(recursion_depth,
            f'I tried {tryword} in {cluenumber} {direction}, but it doesnt fit')
      continue

#   p2.settitle(f'Count {itercount} Depth {recursion_depth} Attempt {attemptno}')
    logit(recursion_depth, f'{tryword} seems to work in {cluenumber} {direction}!')
    p3 = solve(p2,recursion_depth+1)
    if p3 is None:
      logit(recursion_depth, "Well that didn't work")
      continue
    logit(recursion_depth,
          f"The recursive call with {direction} {cluenumber} == {tryword} came back happy!")
    return p3
  
  logit(recursion_depth,
        f"Bummer, the recursive call with {direction} {cluenumber} == {tryword} failed")
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
