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

from puzzlestate import Puzzlestate

def pack_with_words(p, wordlist):
  if not wordlist:
    # Hey! That means we packed all the possible words into the puzzle.
    p.export_puzzlestate()
    return p

    for i, tryword in enumerate(wordlist):
      rest_of_wordlist = [wordlist[x] for x in range(len(wordlist)) if x != i ]
      for trydirection in p.directionlist:
        for trylocation in p.possible_word_starts(tryword,trydirection):
          p2 = p.inscribe_word(tryword,trylocation)
          if p2 is None:
            # oh well, that means we were not able to inscribe this word at this location in this direction.
            # try the next one!
            continue
          else:
            # cool! let's recurse.
            if pack_with_words(p2,rest_of_wordlist):
              return p2

    # if we make it here, that means that none of the words in wordlist can be inscribed.
    print("none of the words in wordlist {} can be inscribed.".format(wordlist))
    return None

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
      wordlist2 = f.readlines()
  except IOError:
    print("{}: couldn't open wordlistfile {}".format(sys.argv[0], wordlistfile))
    sys.exit(2)

  wordlist = [str(x.decode('utf-8').strip()) for x in wordlist2]
  longestword = max(wordlist,key=len)
  maxlen = len(longestword)

  if maxlen > height and maxlen > width:
    print("{}: wordlistfile {} contains a word {} that won't fit in the puzzle".format(sys.argv[0], wordlistfile, longestword))
    sys.exit(3)

  p = Puzzlestate(height,width)

  pack_with_words(p,wordlist)
  p.print()

if __name__ == "__main__":
    main()

