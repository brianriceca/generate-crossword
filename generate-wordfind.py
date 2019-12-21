#!/usr/bin/python3
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

directionlist = ( 
        (1,0),          # forwards
        (1,-1),          # diagonal up forwards
        (0,-1),          # up
        (-1,-1),         # diagonal up backwards
        (-1,0),         # backwards
        (-1,1),        # diagonal down backwards
        (0,1),         # down
        (1,1)          # diagonal down forwards
)

def solve(puzzlestate, wordlist):

    if not wordlist:
      export_puzzlestate(puzzlestate)
      return True
    for i, tryword in enumerate(wordlist):
      rest_of_wordlist = [wordlist[x] for x in range(len(wordlist)) if x != i ]
      for trydirection in directionlist:
        for trylocation in possible_word_starts(puzzlestate,tryword,trydirection):
         puzzlestate2 = copy(puzzlestate)
         if inscribe_word(puzzlestate2,tryword,trylocation):
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

  wordlist = ()
  
  try:
    with open(wordlistfile,'rb') as f:
      wordlist = f.readlines()
  except IOError:
    print("{}: couldn't open wordlistfile {}".format(sys.argv[0], wordlistfile))
    sys.exit(2)

  maxlen = len(max(wordlist,key=len))
  if maxlen > height and maxlen > width:
    print("{}: wordlistfile {} contains a word that won't fit in the puzzle".format(sys.argv[0], wordlistfile))
    sys.exit(3)

  sys.exit(0)
    
  p = puzzlestate(height,width)

  if solve(p,wordlist):
    print("success")
  else:
    print("failure")


if __name__ == "__main__":
    main()

