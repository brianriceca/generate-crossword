#!/usr/local/bin/python3

def possible_word_starts(maxx, maxy, word, direction):
    positionlist = []
    minx = miny = 0
    if direction[0] == 0:
      pass
    elif direction[0] == -1:
      pass
    else:
      maxx = maxx - len(word)
    if direction[1] == 0:
      miny = 
    elif direction[1] == -1:
      miny = 
    else:
      miny = 
    for i in range(minx,maxx):
      for j in range(minx,maxy):
        newloc = (i,j)
        positionlist.append(newloc)
    random.shuffle(positionlist)
    while 1:
        try:
            yield positionlist.pop()
        except IndexError:
            yield [ -1, -1, (0, 0) ]

def main():
    for counter, mystart in enumerate(possible_word_starts(4,5,"foo", (0,1) )):
        print (counter, mystart)
        if mystart[0] == -1:
            sys.exit(1)
    

if __name__ == "__main__":
    main()
