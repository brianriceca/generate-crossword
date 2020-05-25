#!/usr/bin/env python3
'''
generate-wordfind.py: create a hidden-word puzzle

usage: generate-wordfind.py height width wordlistfile

Geometry:
  
   0
   1
   2
   ...
   height-1
             0 1 2 ... width-1
'''

import sys
import copy

import puzzlestate

def solve(puzzlestate, wordlist):
  if not wordlist:
    # Hey! That means we solved the puzzle.
    export_puzzlestate(puzzlestate)
    return True

    for i, tryword in enumerate(wordlist):
      rest_of_wordlist = [wordlist[x] for x in range(len(wordlist)) if x != i ]
      for trydirection in puzzlestate.directionlist:
        for trylocation in puzzlestate.possible_word_starts(tryword,trydirection):
          puzzlestate2 = puzzlestate.inscribe_word(tryword,trylocation):
          if puzzlestate2 is None:       
            # oh well, that means we were not able to inscribe this word at this location in this direction.
            # try the next one!
            continue
          else:
            # cool! let's recurse.
            solve(puzzlestate2,rest_of_wordlist)             
           if solve(puzzlestate2,rest_of_wordlist):
              return True
    return False

def main():
  if len(sys.argv) != 4 or int(sys.argv[1]) < 1 or int(sys.argv[2]) < 1:
    print("usage: {} height width wordlistfile".format(sys.argv[0]))
    sys.exit(1)
  
  height = int(sys.argv[1])
  width = int(sys.argv[2])
  wordlistfile = sys.argv[3]  

  wordlist = list()
 
  try:
    with open(wordlistfile,'rb') as f:
      wordlist = f.readlines()
  except IOError:
    print("{}: couldn't open wordlistfile {}".format(sys.argv[0], wordlistfile))
    sys.exit(2)

  wordlist = [x.strip() for x in wordlist]
  longestword = max(wordlist,key=len)
  maxlen = len(longestword)

  if maxlen > height or maxlen > width:
    print("{}: wordlistfile {} contains a word {} that won't fit in the puzzle".format(sys.argv[0], wordlistfile, longestword))
    sys.exit(3)

  for w in wordlist:
    print("\"{}\"".format(w))

  p = puzzlestate(height,width)

  if solve(p,wordlist):
    print("success")
  else:
    print("failure")


if __name__ == "__main__":
    main()

