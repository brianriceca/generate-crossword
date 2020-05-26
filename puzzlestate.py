#!/usr/bin/env python3

import random
import json
import copy

class Puzzlestate:
  '''
Geometry:
  
          0
          1
          2
        ...
   height-1
             0 1 2 ... width-1
  '''

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

  def __init__(self,width,height):
    self.width = width
    self.height = height
    self.layout = [[None for i in range(width)] for j in range(height)]
    self.wordsused = list()
  def getheight(self):
    return self.height
  def getwidth(self):
    return self.width
  def getwordsused(self):
    return self.wordsused
  def getchar(self,x,y):
    return self.layout[y][x]
  def copy(self):
    newp = Puzzlestate(self.width,self.height)
    newp.layout = copy.deepcopy(self.layout)
    return newp
  def setchar(self,x,y,c):
    x = int(x)
    y = int(y)
    if x < 0:
      return None
    if y < 0:
      return None
    if x >= self.width:
      return None
    if y >= self.height:
      return None
    self.layout[y][x] = c
    return self

  def inscribe_word(self,word,location,direction):
    # returns a new puzzle state object containing the word if it was able to inscribe it, else None

    # first, a test
    thisx,thisy = location
    xincrement,yincrement = direction

    for c in word:
      if thisx < 0 or thisx >= self.width or thisy < 0 or thisy >= self.height:
        return None
      if self.layout[thisy][thisx] == c:
        pass # Yay! It's already the character we want.
      elif self.layout[thisy][thisx] == None:
        pass
      else:
        return None
      thisx = thisx + xincrement   
      thisy = thisy + yincrement   

    # OK, now for real
    newpuzzlestate = self.copy()
    thisx,thisy = location
    xincrement,yincrement = direction

    for c in word:
      assert (not (thisx < 0 or thisx >= newpuzzlestate.width or thisy < 0 or thisy >= newpuzzlestate.height)), "out of range"
      assert ((newpuzzlestate.layout[thisy][thisx] == None) or (newpuzzlestate.layout[thisy][thisx] == c)), "found a conflict"
      newpuzzlestate.layout[thisy][thisx] = c
      thisx = thisx + xincrement   
      thisy = thisy + yincrement   

    newpuzzlestate.wordsused.append(word)
    return newpuzzlestate

  def print(self):
    for i in range(self.height):
      for j in range(self.width):
        c = self.layout[i][j]
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
    maxy = self.height - 1

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
  p = Puzzlestate(width,height)
  location = [ 0, 0 ]
  direction = [ 1, 0 ]

  print("about to inscribe word 1")
  p1 = p.inscribe_word("super",location,direction)
  if p1 is None:
    print("failure")
  else:
    print("success")

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
  direction = p.directionlist[random.randrange(8)]
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

