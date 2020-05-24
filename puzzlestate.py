#!/usr/bin/env python3

import random
import json

'''
Geometry:
  
          0
          1
          2
        ...
   height-1
             0 1 2 ... width-1

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
'''

class puzzlestate:
  def __init__(self,height,width):
    self.height = height
    self.width = width
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
  def inscribe_word(self,word,location,direction):
    thisx,thisy = location
    xincrement,yincrement = direction
    for c in word:
      if thisx < 0 or thisx >= self.width or thisy < 0 or thisy >= self.height:
        return False
      if self.layout[thisy][thisx] == c:
        pass # Yay! It's already the character we want.
      elif self.layout[thisy][thisx] == None:
        self.layout[thisy][thisx] = c
      else:
        return False
      thisx = thisx + xincrement   
      thisy = thisy + yincrement   
    self.wordsused.append(word)
    print(self.layout)
    return True     
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
  p = puzzlestate(height,width)
  location = [ 0, 0 ]
  direction = [ 1, 0 ]

  print("about to inscribe word 1")
  if p.inscribe_word("super",location,direction):
    print("success")
  else:
    print("failure")

  location = [ 2, 1 ]
  direction = [ 0, -1 ]
  print("about to inscribe word 2")
  if p.inscribe_word("up",location,direction):
    print("success")
  else:
    print("failure")

  location = [ 5, 4 ]
  direction = [ -1, 0 ]
  print("about to inscribe word 3")
  if p.inscribe_word("boot",location,direction):
    print("success")
  else:
    print("failure")
  print(p.getchar(0,0))
  print(p.getchar(0,1))
  print(p.getchar(1,1))

  trial_word = "foo"
  trial_direction = [ -1, -1 ]
  word_start_list = p.possible_word_starts(trial_word, trial_direction)

  for loc in word_start_list:
    last_status = p.inscribe_word(trial_word,loc,trial_direction)
    if last_status:
      break

  if last_status:
    print("success")
  else:
    print("failure")

  p.print()
  print(p.json())

if __name__ == '__main__':
    main()

