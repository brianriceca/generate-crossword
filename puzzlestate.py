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
                 "wordsused": set(),
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
    
    if type(data['dimensions']['width']) == float:
      sys.exit('silly rabbit, widths can\'t be floats')
    elif type(data['dimensions']['width']) == str:
      if data['dimensions']['width'].isnumeric():
        data['dimensions']['width'] = int(data['dimensions']['width'])
      else:
        sys.exit('invalid width')

    if data['dimensions']['width'] <= 0:
      sys.exit('width must be positive')

    if type(data['dimensions']['height']) == float:
      sys.exit('silly rabbit, heights can\'t be float')
    elif type(data['dimensions']['height']) == str:
      if data['dimensions']['height'].isnumeric():
        data['dimensions']['height'] = int(data['dimensions']['height'])
      else:
        sys.exit('invalid height')

    if data['dimensions']['height'] <= 0:
      sys.exit('height must be positive')

    width = int(data['dimensions']['width'])
    height = int(data['dimensions']['height'])

    if 'wordsused' not in data.keys():
        data['wordsused'] = set()
    if 'solution' not in data.keys():
        data['solution'] = \
                  [[None for i in range(width)] for j in range(height)] 
    if 'answerlocations' not in data.keys():
      data['answerlocations'] = dict()
    if 'answerlengths' not in data.keys():
      data['answerlengths'] = dict()
  
    # let's validate the puzzle and die if it is broken

    if 'puzzle' not in data:
      sys.exit('this puzzle file lacks a puzzle')
    if not isinstance(data['puzzle'], list):
      sys.exit('this puzzle file\'s puzzle is the wrong kind of data structure')

    if len(data['puzzle']) != height:
      sys.exit('puzzle should be {} columns high, is {}'.format(height,len(data['puzzle'])))

    for rownumber, row in enumerate(data['puzzle']):
      if not isinstance(row, list):
        sys.exit('this puzzle file\'s puzzle is the wrong kind of data structure')
      if len(row) != width:
        sys.exit('puzzle row {} should be {} wide, is {} wide'.format(rownumber,
                                                                      width,
                                                                      len(row)))
    # squirrel away the clue locations; make sure any filled clues are uppercase
    for row in range(height):
      for col in range(width):
        cellcontents = data['puzzle'][row][col]
        if type(cellcontents) == int and cellcontents > 0:
          data['answerlocations'][cellcontents] = [row,col]
        elif type(cellcontents) == int:
          pass
        elif type(cellcontents) == str and cellcontents.isdigit():
          data['answerlocations'][int(cellcontents)] = [row,col]
          data['puzzle'][row][col] = int(cellcontents)
        elif type(cellcontents) == str and cellcontents.isalpha():
          data['puzzle'][row][col] = data['puzzle'][row][col].toupper()
        elif type(cellcontents) == str and cellcontents == '#':
          pass
        elif isinstance(cellcontents, dict):
          sys.exit("I don't know how to deal with fancy cells yet")
        else:
          sys.exit("weird cell content: [{},{}] is {}".format(row,col,cellcontents))

    # now squirrel away the length of the answer for each clue

    for direction in data['clues']: 
      if direction not in Puzzlestate.directions.keys():
        sys.exit("{} is not a direction".format(direction))
      for cluenumber in data['clues'][direction]:
        xloc,yloc = data['answerlocations'][cluenumber[0]]
        # [1] is the clue for a human solver, we don't care about that
        if data['puzzle'][xloc][yloc] != cluenumber[0]:
          sys.exit('found a mismatch at ({},{}): expected {}, saw {}'.format(
                                                                        xloc,
                                                                        yloc,
                                                                        cluenumber[0],
                                                                        data['puzzle'][xloc][yloc]))
      # now we count the number of blanks from the start of the clue, in the given direction, 
      # to the next '#' or boundary
        
      data['answerlengths'][repr([ direction, cluenumber[0] ])] = 1
      while True:
        xloc += Puzzlestate.directions[direction][0]
        yloc += Puzzlestate.directions[direction][1]
        if xloc == width or yloc == height or data['puzzle'][xloc][yloc] == '#':
          break 
        data['answerlengths'][repr([ direction, cluenumber[0] ])] += 1

    return cls(data)

  def height(self):
    return self.data["dimensions"]["height"]
  def getheight(self):
    return self.height()

  def width(self):
    return self.data["dimensions"]["width"]
  def getwidth(self):
    return self.width()

  def getchar(self,rowno,colno):
    if rowno > self.height() or colno > self.width():
      sys.exit("puzzle is ({},{}), and getchar was called on ({},{})".format(rowno,colno,self.height(),self.width()))
    if self.data["solution"][rowno][colno] is not None:
      return self.data["solution"][rowno][colno]
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
    c2 = self.getchar(rowno,colno)
    if c2 is None:
      return True # Yay!  It's not been filled in yet
    if type(c2) == int:
      return True # It's either a 0 for an empty space or else a clue number
    if type(c2) == str and (
        c2 == '?'
        or c2 == '*'
        or c2 == ' ' 
        or c2 == '.') :
      return True # Yay!  It's not been filled in yet
    if type(c2) == str and c2.upper() == c.upper():
      return True # Yay! It's already the character we want.
    return False # D'oh! The space is already in use with a different letter

  def gettitle(self):
    if 'title' in self.data:
      if isinstance(self.data['title'], str):
        return self.data['title']
    return None

  def settitle(self,newtitle):
    if isinstance(newtitle, str):
      self.data['title'] = newtitle
    else:
      sys.exit('settitle called with something not a string')
    return self

  def writejson(self,filename):
    try:
      with open(filename, 'w') as f:
        json.dump(self.data, f, indent=2, sort_keys=True)
    except OSError:
      sys.exit('Could not write json to {}'.format(filename))
    return self
    
  def writesvg(self,filename,**kwargs):
    showcluenumbers=True
    showsolvedcells=True
    showtitle=True
    if 'showcluenumbers' in kwargs:
      if isinstance(kwargs['showcluenumbers'], bool):
        showcluenumbers = kwargs['showcluenumbers']
      else:
        sys.exit('writesvg keyword args need True or False')

    if 'showsolvedcells' in kwargs:
      if isinstance(kwargs['showsolvedcells'], bool):
        showsolvedcells = kwargs['showsolvedcells']
      else:
        sys.exit('writesvg keyword args need True or False')

    if 'showtitle' in kwargs:
      if isinstance(kwargs['showtitle'], bool):
        showtitle = kwargs['showtitle']
      else:
        sys.exit('writesvg keyword args need True or False')

    title = self.gettitle()
    if title is None or title == '':
      title = 'Untitled Crossword Puzzle'

    if 'title' in kwargs:
      if isinstance(kwargs['title'], str):
        title = kwargs['title']
      else:
        sys.exit('titles need to be strings')

    WIDTH=self.width()
    HEIGHT=self.height()
    CELLSIZE_MM=12
    if showtitle:
      TITLEHEIGHT_MM = 14
    else:
      TITLEHEIGHT_MM = 0
    TOP_MARGIN_MM = CELLSIZE_MM
    BOTTOM_MARGIN_MM = CELLSIZE_MM
    TOP_MARGIN_MM += TITLEHEIGHT_MM
    SIDE_MARGIN_MM = CELLSIZE_MM
    OFFSET_CLUENUM_X=1
    OFFSET_CLUENUM_Y=3
    OFFSET_SOLUTION_X=4
    OFFSET_SOLUTION_Y=9
    WIDTH_MM = CELLSIZE_MM*WIDTH+2*SIDE_MARGIN_MM
    HEIGHT_MM = CELLSIZE_MM*HEIGHT+TOP_MARGIN_MM+BOTTOM_MARGIN_MM
    BLOCK_COLOR = 'gray'
    LINE_COLOR = 'gray'
    CLUENUMBER_STYLE = "font-size:2px; font-family:Times New Roman"
    SOLUTION_STYLE = "font-size:8px; font-family:Arial"
    TITLE_STYLE = "font-size:8px; font-family:Times New Roman"

    PUZZLESIZE = ("{}mm".format(WIDTH_MM),"{}mm".format(HEIGHT_MM))
    
    drawing = svgwrite.Drawing(filename, size=PUZZLESIZE)
    drawing.viewbox(0, 0, HEIGHT_MM, WIDTH_MM)
    
    # draw horizontal lines
    for i in range(1,HEIGHT):
      y = TOP_MARGIN_MM + i * CELLSIZE_MM
#      print("horizontal line from ({},{}) to ({},{})".format(SIDE_MARGIN_MM, y, CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM, y))
      drawing.add(drawing.line(start=(SIDE_MARGIN_MM, y), end=(CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM, y),
                 stroke=LINE_COLOR,stroke_width=1))
    drawing.add(drawing.line(start=(SIDE_MARGIN_MM, 
                            TOP_MARGIN_MM+HEIGHT*CELLSIZE_MM),
                     end=(CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM, 
                          TOP_MARGIN_MM+HEIGHT*CELLSIZE_MM),
                  stroke=LINE_COLOR,stroke_width=1, style='stroke-linecap: round;'))
    drawing.add(drawing.line(start=(SIDE_MARGIN_MM, TOP_MARGIN_MM), 
                     end=(CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM, TOP_MARGIN_MM),
                  stroke=LINE_COLOR,stroke_width=1, style='stroke-linecap: round;'))
    
    # draw vertical lines
    for i in range(1,WIDTH):
      x = SIDE_MARGIN_MM + i * CELLSIZE_MM
#      print("vertical line from ({},{}) to ({},{})".format(x,TOP_MARGIN_MM, x, CELLSIZE_MM*HEIGHT+TOP_MARGIN_MM))
      drawing.add(drawing.line(start=(x,TOP_MARGIN_MM), end=(x, CELLSIZE_MM*HEIGHT+TOP_MARGIN_MM),
                  stroke=LINE_COLOR,stroke_width=1))
    drawing.add(drawing.line(start=(SIDE_MARGIN_MM,TOP_MARGIN_MM), end=(SIDE_MARGIN_MM, CELLSIZE_MM*HEIGHT+TOP_MARGIN_MM),
                stroke=LINE_COLOR,stroke_width=1,style='stroke-linecap: round;'))
    drawing.add(drawing.line(start=(CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM,TOP_MARGIN_MM), end=(CELLSIZE_MM*WIDTH+SIDE_MARGIN_MM, CELLSIZE_MM*HEIGHT+TOP_MARGIN_MM),
                stroke=LINE_COLOR,stroke_width=1,style='stroke-linecap: round;'))


        
    # insert black boxes
    for row in range(HEIGHT):
      for col in range(WIDTH):
        if self.getchar(row,col) == '#':
#          print("drawing a box at x={}, y={}".format(
#                                   col*CELLSIZE_MM+SIDE_MARGIN_MM,
#                                   row*CELLSIZE_MM+TOP_MARGIN_MM
#                                  ))
          drawing.add(drawing.rect(insert=(
                                   col*CELLSIZE_MM+SIDE_MARGIN_MM,
                                   row*CELLSIZE_MM+TOP_MARGIN_MM
                                  ),
                           size=(CELLSIZE_MM,CELLSIZE_MM),
                           fill=BLOCK_COLOR))
  
    if showcluenumbers:
      g = drawing.g(class_='cluenumber',style = CLUENUMBER_STYLE)
      for answer in self.data['answerlocations'].keys():
        row,col = self.data['answerlocations'][answer]
#        print("writing a clue number at x={}, y={}".format(
#                            col*CELLSIZE_MM+SIDE_MARGIN_MM+OFFSET_CLUENUM_X,
#                            row*CELLSIZE_MM+TOP_MARGIN_MM+OFFSET_CLUENUM_Y,
#                           ))

        g.add(drawing.text(answer,
                    insert=(
                            col*CELLSIZE_MM+SIDE_MARGIN_MM+OFFSET_CLUENUM_X,
                            row*CELLSIZE_MM+TOP_MARGIN_MM+OFFSET_CLUENUM_Y,
                           )))
      drawing.add(g)

    if showsolvedcells:
      g = drawing.g(class_='solvedcell', style = SOLUTION_STYLE)
      for row in range(HEIGHT):
        for col in range(WIDTH):
          c = self.getchar(row,col)
          if type(c) == str and c.isalpha():
            g.add(drawing.text(self.getchar(row,col),
                    insert=(
                            col*CELLSIZE_MM+SIDE_MARGIN_MM+OFFSET_SOLUTION_X,
                            row*CELLSIZE_MM+TOP_MARGIN_MM+OFFSET_SOLUTION_Y,
                           )))
      drawing.add(g)

    if showtitle:
      g = drawing.g(class_='title', style = TITLE_STYLE)
      g.add(drawing.text(title,
                    insert=(
                            SIDE_MARGIN_MM,
                            TITLEHEIGHT_MM
                           )))
      drawing.add(g)


    drawing.save()
      
  def random_unsolved_clue(self):
    if len(self.data['unsolved']) == 0:
      return None
    thisclue = random.choice(self.data['unsolved'])
    direction, cluenumber, length = thisclue
    if direction not in Puzzlestate.directions.keys():
      sys.exit('{} is not a direction'.format(direction))
    xinc, yinc = Puzzlestate.directions[direction]
  
    # now we gather the constraints, i.e., letters already filled in

    constraints = list()
    xloc,yloc = self.data['answerlocations'][cluenumber]

    length = 0
    while True:
      xloc += xinc
      yloc += yinc
      length += 1
      if xloc == self.width() or yloc == self.height():
        break
      c = self.getchar(xloc,yloc)
      if type(c) != str:
        continue
      if c.isalpha():
        constraints.append([length,c])
      elif c == '#':
        break
    
    self.data['unsolved'].remove(thisclue)
    return [direction, cluenumber, length, constraints]

  def getwordsused(self):
    try:
      return self.data["wordsused"] 
    except KeyError:
      return None

  def addwordused(self,word):
    self.data["wordsused"].add(word)
    return self

  def copy(self):
    newp = Puzzlestate.blank(self.height(),self.width())
    newp.data = copy.deepcopy(self.data)
    return newp

  def inscribe_word(self,word,direction,cluenumber):
    # returns object containing the word if it was able to inscribe it, 
    # else returns none

    xincrement,yincrement = Puzzlestate.directions[direction]

    # first, a test
    thisx,thisy = self.data['answerlocations'][cluenumber]
    for c in word:
      if ( thisx < 0 or thisx >= self.width()
           or thisy < 0 or thisy >= self.height() ):
        return None
      if self.testchar(thisx,thisy,c):
        pass 
      else:
        return None
      thisx = thisx + xincrement   
      thisy = thisy + yincrement   

    # OK, it fits
    thisx,thisy = self.data['answerlocations'][cluenumber]
   
    for c in word:
      self.setchar(thisx,thisy,c)
      thisx = thisx + xincrement   
      thisy = thisy + yincrement   
    self.addwordused(word)
    return self

  def is_puzzle_solved(self):
    height = self.height()
    width = self.width()
    if len(self.data['puzzle']) != height:
      sys.exit("height of puzzle doesn't match stored height")
    if len(self.data['solution']) != height:
      sys.exit("height of solution doesn't match stored height")
    for i, row in enumerate(self.data['puzzle']):
      if len(row) != width:
        sys.exit("row {} of puzzle doesn't match width".format(i))
      if len(self.data['solution']) != width:
        sys.exit("row {} of solution doesn't match width".format(i))
      for col in row:
        if (self.data['solution'][row][col] is not None and
            self.data['solution'][row][col] != ' ' and
            self.data['solution'][row][col] != self.data['puzzle'][row][col]):
          return False
    return True

  def print(self):
    for rowno in range(self.height()):
      for colno in range(self.width()):
        c = self.getchar(rowno,colno)
        if c is None or c == '':
          print('0 ', end='')
        elif type(c) == str:
          print(c, ' ', end='')
        elif type(c) == int:
          print(c, "?", end='')
        else:
          print("¿ ", end='')
      print()

  def json(self):
    return json.dumps(self.layout)

def main():
  if len(sys.argv) == 1:
    sourcefile = "puzzles/baby-animals-crossword.ipuz"
  else:
    sourcefile = sys.argv[1]
  p = Puzzlestate.fromjsonfile(sourcefile)
  print ("source file is {}".format(sourcefile))

  p.writesvg("{}.svg".format(sourcefile), showtitle=True)
#  p.writejson("{}.ipuzout".format(sourcefile))

if __name__ == '__main__':
    random.seed()
    main()

