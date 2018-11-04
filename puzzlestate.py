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

class puzzlestate:
  def __init__(self,height,width):
    self.height = height
    self.width = width
    self.layout = [[None for i in range(width)] for j in range(height)]
    self.wordsused = []
  def getheight():
    return self.height
  def getwidth():
    return self.width
  def getwordsused():
    return self.wordsused
  def getchar(x,y):
    return self.layout[y][x]
  def inscribe_word(word,location,direction):
    thisx,thisy = location
    xincrement,yincrement = direction
    for i,c in enumerate(word):
      if self.layout[thisy][thisx] == c:
        pass
      elif self.layout[thisy][thisx] == None:
         self.layout[thisy][thisx] = c
      else:
        return False
      thisx = thisx + xincrement   
      thisy = thisy + yincrement   
    self.wordsused.append(word)
    return True     

def main():
  mypuzzlestate = puzzlestate(6,6)
  location = [ 0, 0 ]
  direction = [ 1, 0 ]
  if mypuzzlestate.inscribe_word("hello",location,direction):
    print("success")
  else:
    print("failure")

if __name__ == '__main__':
    main()
