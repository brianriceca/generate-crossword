#!/usr/bin/env python3

import random
import json
import copy
import sys
import svgwrite

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
      sys.exit('Could not read json from {}'.format(filename))
    
    if ('dimensions' not in data.keys() or 
        'width' not in data['dimensions'].keys() or
        'height' not in data['dimensions'].keys()):
      sys.exit('File {} missing puzzle dimension'.format(filename))
    
    width = int(data['dimensions']['width'])
    height = int(data['dimensions']['height'])

    if 'wordsused' not in data.keys():
        data['wordsused'] = list()
    if 'solution' not in data.keys():
        data['solution'] = \
                  [[None for i in range(width)] for j in range(height)] 
    if 'answerlocations' not in data.keys():
      data['answerlocations'] = dict()
    if 'answerlengths' not in data.keys():
      data['answerlengths'] = dict()

    # squirrel away the clue locations; make sure any filled clues are uppercase
    for row in range(height):
      for col in range(width):
        cellcontents = data['puzzle'][row][col]
        if cellcontents.isdigit():
          data['puzzle'][row][col] = int(cellcontents)
          data['answerlocations'][cellcontents] = [row,col]
        elif cellcontents.isalpha():
          data['puzzle'][row][col] = data['puzzle']['row']['col'].toupper()

    # now squirrel away the length of the answer for each clue

      for direction in data['clues']:
        if direction not in Puzzlestate.directions.keys():
          sys.exit("{} is not a direction".format(direction))
        for cluenumber in data['clues'][direction]:
          print(repr(data['answerlocations']))
          xloc,yloc = data['answerlocations'][cluenumber[0]]
          # [1] is the clue for a human solver, we don't care about that
          if data['puzzle'][xloc][yloc] != cluenumber:
            sys.exit('found a mismatch at ({},{}): expected {}, saw {}'.format(
                                                                            xloc,
                                                                            yloc,
                                                                            cluenumber,
                                                                            data['puzzle'][xloc][yloc]))
        # now we count the number of blanks to the next '#' or boundary
        
        self.data['answerlengths'][repr([ direction, cluenumber ])] = 1

        while True:
          xloc += Puzzlestate.directions[directions][0]
          yloc += Puzzlestate.directions[directions][1]
          if xloc == data['width'] or yloc == data['height'] or data['puzzle'][xloc][yloc] == '#':
            break
          data['answerlengths'][repr([ direction, cluenumber ])] += 1

    return cls(data)

  def writejson(self,filename):
    try:
      with open(filename, 'w') as f:
        json.dump(self.data, f, indent=2, sort_keys=True)
    except OSError:
      sys.exit('Could not write json to {}'.format(filename))
    return self
    
  def writesvg(self,filename):
    WIDTH=self.width()
    HEIGHT=self.height()
    CELLSIZE_MM=12
    TOP_MARGIN_MM = CELLSIZE_MM
    SIDE_MARGIN_MM = CELLSIZE_MM
    OFFSETX=1
    OFFSETY=3
    WIDTH_MM = CELLSIZE_MM*WIDTH+2*SIDE_MARGIN_MM
    HEIGHT_MM = CELLSIZE_MM*HEIGHT+2*TOP_MARGIN_MM
    CSS_STYLES="""
text {
     font-size: 2pt;
     font-family: Times New Roman;
     color: red;
}
"""
      
    if WIDTH_MM > HEIGHT_MM:
      PUZZLESIZE = ("{}mm".format(WIDTH_MM),"{}mm".format(WIDTH_MM))
    else:
      PUZZLESIZE = ("{}mm".format(HEIGHT_MM),"{}mm".format(HEIGHT_MM))
    
    dwg = svgwrite.Drawing(filename, size=PUZZLESIZE)
    dwg.viewbox(0, 0, HEIGHT_MM, WIDTH_MM)
    dwg.defs.add(dwg.style(CSS_STYLES))
    
    # draw horizontal lines
    for i in range(HEIGHT):
      y = TOP_MARGIN_MM + i * CELLSIZE_MM
#      print("horizontal line from ({},{}) to ({},{})".format(SIDE_MARGIN_MM, y, CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM, y))
      dwg.add(dwg.line(start=(SIDE_MARGIN_MM, y), end=(CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM, y),
                  stroke='#111111',stroke_width=1))
    dwg.add(dwg.line(start=(SIDE_MARGIN_MM-1, 
                            TOP_MARGIN_MM+HEIGHT*CELLSIZE_MM),
                     end=(CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM+1, 
                          TOP_MARGIN_MM+HEIGHT*CELLSIZE_MM),
                  stroke='#00FF00',stroke_width=1))
    dwg.add(dwg.line(start=(SIDE_MARGIN_MM-1, TOP_MARGIN_MM), 
                     end=(CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM+1, TOP_MARGIN_MM),
                  stroke='#FFFF00',stroke_width=1))
    
    # draw vertical lines
    for i in range(WIDTH+1):
      x = SIDE_MARGIN_MM + i * CELLSIZE_MM
#      print("vertical line from ({},{}) to ({},{})".format(x,TOP_MARGIN_MM, x, CELLSIZE_MM*HEIGHT+TOP_MARGIN_MM))
      dwg.add(dwg.line(start=(x,TOP_MARGIN_MM), end=(x, CELLSIZE_MM*HEIGHT+TOP_MARGIN_MM),
                  stroke='#111111',stroke_width=1))
        
#    # insert the clue numbers
    for row in range(HEIGHT):
      for col in range(WIDTH):
        if self.getchar(row,col).isdigit():
          dwg.add(dwg.text(self.getchar(row,col),
                  insert=(
                          col*CELLSIZE_MM+TOP_MARGIN_MM+OFFSETX,
                          row*CELLSIZE_MM+SIDE_MARGIN_MM+OFFSETY,
                         )))

    # insert black boxes
    for row in range(HEIGHT):
      for col in range(WIDTH):
        if self.getchar(row,col) == '#':
          dwg.add(dwg.rect(insert=(
                                   col*CELLSIZE_MM+TOP_MARGIN_MM,
                                   row*CELLSIZE_MM+SIDE_MARGIN_MM
                                  ),
                           size=(CELLSIZE_MM,CELLSIZE_MM),
                           fill='gray'))
    


    dwg.save()
      
  def height(self):
    return self.data["dimensions"]["height"]

  def width(self):
    return self.data["dimensions"]["width"]

  def getchar(self,rowno,colno):
    return self.data["puzzle"][rowno][colno]

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
    if (self.getchar(rowno,colno) is None
        or self.getchar(rowno,colno) == '?'
        or self.getchar(rowno,colno) == '*'
        or self.getchar(rowno,colno) == ' ' 
        or self.getchar(rowno,colno) == '.' 
        or int(self.getchar(rowno,colno)) > 0 ):
      return True # Yay!  It's not been filled in yet
    if self.getchar(rowno,colno).upper() == c.upper():
      return True # Yay! It's already the character we want.
    return False # D'oh! The space is already in use with a different letter

  def length_of_puzzleword(self, direction, cluenumber):
    i = 0
    while i < length:
      if self.getchar(xloc,yloc).isalpha():
        constraints.append(list(i,self.puzzle[xloc][yloc]))
        xloc += xinc
        yloc += yinc
        i += 1
     #####  

  def random_unsolved_clue(self):
    direction, cluenumber, length = self.data['unsolved'][random.randint(0,

                                                            len(self.data['unsolved'])-1)]
    if direction not in Puzzlestate.directions.keys():
      sys.exit('{} is not a direction'.format(direction))
    xinc, yinc = Puzzlestate.directions[direction]
  
    # now we gather the constraints, i.e., letters already filled in

    constraints = list()
    xloc,yloc = self.data['answerlocations'][cluenumber]

    i = 0
    while i < length:
      if self.getchar(xloc,yloc).isalpha():
        constraints.append(list(i,self.puzzle[xloc][yloc]))
        xloc += xinc
        yloc += yinc
        i += 1
    return (direction, cluenumber, wordlength, constraints)

  def getwordsused(self):
    try:
      return self.data["wordsused"] 
    except KeyError:
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
    xincrement,yincrement = Puzzlestate.directions[direction]
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

    # OK, it fits
    thisx,thisy = location
    xincrement,yincrement = direction
    for c in word:
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

def main():
  p = Puzzlestate.fromjsonfile("puzzles/baby-animals-crossword.json")

  p.writesvg("puzzles/baby-animals-crossword.svg")
#  p.writejson("/tmp/foo.json")

if __name__ == '__main__':
    random.seed()
    main()

