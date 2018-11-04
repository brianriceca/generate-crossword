#!/usr/local/bin/python3
'''
Geometry:
  
    0 1 2 ... width-1
   0
   1
   2
   ...
   height-1
'''

directionlist = ( 
        (1,0),          # forwards
        (1,1),          # diagonal up forwards
        (0,1),          # up
        (-1,1),         # diagonal up backwards
        (-1,0),         # backwards
        (-1,-1),        # diagonal down backwards
        (0,-1),         # down
        (1,-1)          # diagonal down forwards
)

def solve(puzzlestate, wordlist):

    if not wordlist:
      export_puzzlestate(puzzlestate)
      return True
    for i, tryword in enumerate(wordlist):
      rest_of_wordlist = [wordlist[x] for x in range(len(wordlist)) if x != i ]
      for trydir in directionlist:
        for tryloc in possible_word_starts(puzzlestate,tryword,trydir):
          if word(puzzlestate,tryword,tryloc):
            puzzlestate2 = copy(puzzlestate)
            inscribe_word(puzzlestate2,tryword,tryloc)
            if solve(puzzlestate2,rest_of_wordlist):
              return True
    return False

def main():
  if len(sys.argv) != 4 or int(sys.argv[1]) < 1 or int(sys.argv[2]) < 1:
  	print("usage: %s height width wordlistfile\n" % sys.argv[0])
  	sys.exit(1)
	
  height = sys.argv[1]
  width = sys.argv[2]
  wordlistfile = sys.argv[3]	

  wordlist = ()
	
  try:
  	with open(wordlistfile,'rb') as f:
  		wordlist = f.readlines()
  except IOError:
  	print("%s: couldn't open wordlistfile %s\n" % (sys.argv[0], wordlistfile))
  	sys.exit(2)


if __name__ == "__main__":
    main()

