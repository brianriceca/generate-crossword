#!/usr/local/bin/python3

import random
import sys

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

def possible_word_starts(maxx, maxy):
    positionlist = []
    for i in range(maxx):
        for j in range(maxy):
            for d in directionlist:
                newloc = (i,j,d)
                positionlist.append(newloc)
    random.shuffle(positionlist)
    while 1:
        try:
            yield positionlist.pop()
        except IndexError:
            yield [ -1, -1, (0, 0) ]

def main():
    for counter, mystart in enumerate(randomstarts(4,5)):
        print (counter, mystart)
        if mystart[0] == -1:
            sys.exit(1)
    

if __name__ == "__main__":
    main()
