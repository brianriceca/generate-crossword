#!/usr/bin/env python3

import random
import json
import copy

class Puzzlestate:

# Directions are defined as (rowincrement,colincrement)
  
  directions = {
    'Across': [0,1],
    'Down': [1,0]
  }

  def __init__(self,data):
    self.data = data

  @classmethod
  def blank(cls,height,width):
    if int(width) <= 0 or int(height) <= 0:
      return None
    return cls( {"dimensions": {"height": int(height), 
                                "width": int(width)},
                 "wordsused": [],
                 "solution": 
                  [[None for i in range(width)] for j in range(height)] })


  @classmethod
  def fromjsonfile(cls,filename):
    try:
      with open(filename) as f:
        data = json.load(f)
    except OSError:
      return False

    data.cluelocations = dict()
    for row in range(data.height):
      for col in range(data.width):
        cluenumber = int(data.puzzle[row][col])
        if cluenumber > 0:
          data.cluelocations[cluenumber] = list(row,col)
    return cls(data)

  def writejson(self,filename):
    try:
      with open(filename, 'w') as f:
        json.dump(self.data, f, indent=2, sort_keys=True)
    except OSError:
      return False
    return self

  def height(self):
    return self.data["dimensions"]["height"]

  def width(self):
    return self.data["dimensions"]["width"]

  def getchar(self,rowno,colno):
    return self.data["solution"][rowno][colno]

  def setchar(self,rowno,colno,c):
    rowno = int(rowno)
    colno = int(colno)
    if rowno < 0:
      raise IndexError("row number " + str(rowno) + " too small")
    if colno < 0:
      raise IndexError("col number " + str(colno) + " too small")
    if rowno >= self.height():
      raise IndexError("row number " + str(rowno) + " too big")
    if colno >= self.width():
      raise IndexError("col number " + str(colno) + " too big")
    self.data["solution"][rowno][colno] = c.upper()
    return self

  def testchar(self,rowno,colno,c):
    rowno = int(rowno)
    colno = int(colno)
    if rowno < 0:
      raise IndexError("row number " + str(rowno) + " too small")
    if colno < 0:
      raise IndexError("col number " + str(colno) + " too small")
    if rowno >= self.height():
      raise IndexError("row number " + str(rowno) + " too big")
    if colno >= self.width():
      raise IndexError("col number " + str(colno) + " too big")
    if self.getchar(rowno,colno) is None:
      return True # Yay!  It's not been filled in yet
    if self.getchar(rowno,colno).upper() == c.upper():
      return True # Yay! It's already the character we want.
    elif ( self.getchar(rowno,colno) == '?'
             or self.getchar(rowno,colno) == '*'
             or self.getchar(rowno,colno) == '.' ):
      return True # Yay!  It's not been filled in yet
    return False # D'oh! The space is already in use with a different letter

  def random_unsolved_clue(self):
    (direction, cluenumber, length) = self.unsolved[random.randint(0,

                                                              length(self.unsolved)-1)]
    assert(direction in directions.keys()
    (xinc, yinc) = directions[direction]
  
    # now we gather the constraints, i.e., letters already filled in

    constraints = list()
    (xloc,yloc) = self.cluelocations[cluenumber]

    i = 0
    while i < length:
      if (ord(self.puzzle[xloc][yloc]) >= ord('A') and
          ord(self.puzzle[xloc][yloc]) <= ord('Z')):
        constraints.append(i,self.puzzle[xloc][yloc])
        xloc += xinc
        yloc += yinc
        i += 1
    return (direction, cluenumber, wordlength, constraints)

  def getwordsused(self):
    try:
      return self.data["wordsused"] except KeyError:
      return None

  def addwordused(self,word):
    self.data["wordsused"].append(word)
    return self

  def copy(self):
    newp = Puzzlestate.blank(self.height(),self.width())
    newp.data = copy.deepcopy(self.data)
    return newp

  def inscribe_word(self,word,location,direction):
    # returns object containing the word if it was able to inscribe it, 
    # else throws an exception

    # first, a test
    thisx,thisy = location
    xincrement,yincrement = direction

    for c in word:
      if ( thisx < 0 or thisx >= self.width()
           or thisy < 0 or thisy >= self.height() ):
        raise ValueError('out of bounds')
      if self.testchar(thisx,thisy,c):
        pass 
      else:
        raise ValueError('conflict with already inscribed word')
      thisx = thisx + xincrement   
      thisy = thisy + yincrement   

    thisx,thisy = location
    xincrement,yincrement = direction

    for c in word:
      assert thisx >= 0, "thisx value " + str(thisx) + " before the range"
      assert thisy >= 0, "thisy value " + str(thisy) + " before the range"
      assert thisx < self.height(), \
              "thisx value " + str(thisx) + " after the range"
      assert thisy < self.width(), \
              "thisy value " + str(thisy) + " after the range"
      assert self.getchar(thisx,thisy) == None   \
             or self.getchar(thisx,thisy) == '?' \
             or self.getchar(thisx,thisy) == '*' \
             or self.getchar(thisx,thisy) == '.' \
             or self.getchar(thisx,thisy).upper() == c.upper() , "found a conflict"

      self.setchar(thisx,thisy,c)
      thisx = thisx + xincrement   
      thisy = thisy + yincrement   
    self.addwordused(word)
    return self

  def print(self):
    for rowno in range(self.height()):
      for colno in range(self.width()):
        c = self.getchar(rowno,colno)
        if c:
          print("{0:s} ".format(c), end='')
        else:
          print('* ', end='')
      print()
  def json(self):
    return json.dumps(self.layout)
  def possible_word_starts(self, word, direction):
    # Until we know the desired direction, the word can start anywere in the puzzle.
    minx = 0
    maxx = self.width - 1

    miny = 0
    maxy = self.height() - 1

    # Now let's refine the bounding box based on the desired direction.

    if direction[0] == 0: # it's a horizontal word
      pass
    elif direction[0] == -1: # it goes up
      minx = len(word) 
    elif direction[0] == 1: # it goes down
      maxx = maxx - len(word)
    else:
      raise ValueError("{} can't be this value".format(direction[0]))

    if direction[1] == 0: # it's a vertical word
      pass
    elif direction[1] == -1: # it's right to left
      miny = len(word)
    elif direction[1] == 1: # it's left to right
      miny = miny - len(word)
    else:
      raise ValueError("{} can't be this value".format(direction[1]))
    positionlist = list()
    for i in range(minx,maxx):
      for j in range(miny,maxy):
        newloc = (i,j)
        positionlist.append(newloc)
    random.shuffle(positionlist)
    return positionlist


def main():
  height = 5
  width = 6
  p = Puzzlestate.blank(width,height)
  location = [ 0, 0 ]
  direction = [ 1, 0 ]

  print("about to inscribe word 1")
  p1 = p.inscribe_word("super",location,direction)
  if p1 is None:
    print("failure")
  else:
    print("success!")

  location = [ 2, 1 ]
  direction = [ 0, -1 ]
  print("about to inscribe word 2")
  p2 = p1.inscribe_word("up",location,direction)
  if p2 is None:
    print("failure")
    p2 = p
  else:
    print("success")

  p2.print()

  location = [ 5, 4 ]
  
  randstate =  random.randrange(len(Puzzlestate.direction))
  print("randstate is {}".format(randstate))
  direction = Puzzlestate.direction[randstate]
  trial_word = "boot"
  print("about to inscribe word {} at location {}, direction {}".format(trial_word,location,direction))
  p3 = p2.inscribe_word(trial_word,location,direction)
  if p3 is None:
    print("failure")
    p3 = p2
  else:
    print("success")
  print(p.getchar(1,1))

  print("===========")
  trial_word = "foo"
  trial_direction = [ -1, -1 ]
  word_start_list = p3.possible_word_starts(trial_word, trial_direction)

  for loc in word_start_list:
    p4 = p3.inscribe_word(trial_word,loc,trial_direction)
    last_status = p3.inscribe_word(trial_word,loc,trial_direction)
    if p4 is not None:
      break

  if p4 is None:
    print("failure")
  else:
    print("success")

  p4.print()
  print(p4.json())

if __name__ == '__main__':
    random.seed()
    main()

