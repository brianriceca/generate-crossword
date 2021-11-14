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

  class Letterkind:
    vowels = { 'A', 'E', 'I', 'O', 'U', 'Y'}
    safe_vowels = { *vowels, '#' }
    consonants = {
               'B', 'C', 'D', 'F', 'G', 'H',
               'J', 'K', 'L', 'M', 'N', 'P',
               'R', 'S', 'T', 'V', 'W', 'X',
               'Y', # yes Y is in both sets
               'Z' }
    safe_consonants = { *consonants, '#' }
    terminals = { 'S', 'D', 'G' }
    u = { 'U' }
    h = { 'H' }
    hpreceders = { 'C', 'G', 'S', 'T' }
    hfollowers = { *vowels, 'R' }

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
      with open(filename,encoding='utf-8') as f:
        data = json.load(f)
    except OSError:
      raise RuntimeError(f'Could not read json from {filename}')

    if ('dimensions' not in data.keys() or
        'width' not in data['dimensions'].keys() or
        'height' not in data['dimensions'].keys()):
      raise RuntimeError(f'File {filename} missing puzzle dimension')

    if isinstance(data['dimensions']['width'],float):
      raise RuntimeError('silly rabbit, widths can\'t be floats')
    elif isinstance(data['dimensions']['width'],str):
      if data['dimensions']['width'].isnumeric():
        data['dimensions']['width'] = int(data['dimensions']['width'])
      else:
        raise RuntimeError('invalid width')

    if data['dimensions']['width'] <= 0:
      raise RuntimeError('width must be positive')

    if isinstance(data['dimensions']['height'],float):
      raise RuntimeError('silly rabbit, heights can\'t be float')
    elif isinstance(data['dimensions']['height'],str):
      if data['dimensions']['height'].isnumeric():
        data['dimensions']['height'] = int(data['dimensions']['height'])
      else:
        raise RuntimeError('invalid height')

    if data['dimensions']['height'] <= 0:
      raise RuntimeError('height must be positive')

    width = int(data['dimensions']['width'])
    height = int(data['dimensions']['height'])

    if 'wordsused' not in data.keys():
      data['wordsused'] = set()
    if 'solution' not in data.keys():
      data['solution'] = \
                  [[None for i in range(width)] for j in range(height)]
    if 'answerlocations' not in data.keys():
      data['answerlocations'] = {}
    if 'answerlengths' not in data.keys():
      data['answerlengths'] = {}
    if 'unsolved' not in data.keys():
      data['unsolved'] = []

    # let's validate the puzzle and die if it is broken

    if 'puzzle' not in data:
      raise RuntimeError('this puzzle file lacks a puzzle')
    if not isinstance(data['puzzle'], list):
      raise RuntimeError('this puzzle file\'s puzzle is the wrong kind of data structure')

    if len(data['puzzle']) != height:
      raise RuntimeError(f"puzzle should be {height} columns high, is {len(data['puzzle'])}")

    for rownumber, row in enumerate(data['puzzle']):
      if not isinstance(row, list):
        raise RuntimeError('this puzzle file\'s puzzle is the wrong kind of data structure')
      if len(row) != width:
        raise RuntimeError(f'puzzle row {rownumber} should be {width} wide, is {len(row)}')

    # squirrel away the clue locations; make sure any filled clues are uppercase
    for row in range(height):
      for col in range(width):
        cellcontents = data['puzzle'][row][col]
        if isinstance(cellcontents,int) and cellcontents > 0:
          data['answerlocations'][cellcontents] = [row,col]
        elif isinstance(cellcontents,int):
          pass
        elif isinstance(cellcontents,str) and cellcontents.isdigit():
          data['answerlocations'][int(cellcontents)] = [row,col]
          data['puzzle'][row][col] = int(cellcontents)
        elif isinstance(cellcontents,str) and cellcontents.isalpha():
          data['puzzle'][row][col] = data['puzzle'][row][col].toupper()
        elif isinstance(cellcontents,str) and cellcontents == '#':
          pass
        elif isinstance(cellcontents, dict):
          raise RuntimeError("I don't know how to deal with fancy cells yet")
        else:
          raise RuntimeError("weird cell content: [{},{}] is {}".format(row,col,cellcontents))

    # now squirrel away the length of the answer for each clue

    for direction in data['clues']:
      if direction not in Puzzlestate.directions.keys():
        raise RuntimeError("{} is not a direction".format(direction))
      for cluenumber in data['clues'][direction]:
        xloc,yloc = data['answerlocations'][cluenumber[0]]
        # [1] is the clue for a human solver, we don't care about that
        if data['puzzle'][xloc][yloc] != cluenumber[0]:
          raise RuntimeError(f"found a mismatch at ({xloc},{yloc}): expected {cluenumber}, saw {data['puzzle'][xloc][yloc]}")
      # now we count the number of blanks from the start of the clue, in the given direction,
      # to the next '#' or boundary

        n = 1
        while True:
          xloc += Puzzlestate.directions[direction][0]
          yloc += Puzzlestate.directions[direction][1]
          if xloc == width or yloc == height or data['puzzle'][xloc][yloc] == '#':
            break
          n += 1

        data['answerlengths'][repr([ direction, cluenumber[0] ])] = n
        data['unsolved'].append( [ direction, cluenumber[0], n ] )

    return cls(data)

  def height(self):
    return self.data["dimensions"]["height"]
  def getheight(self):
    return self.height()

  def width(self):
    return self.data["dimensions"]["width"]
  def getwidth(self):
    return self.width()

  def _getchar(self,rowno,colno):
    if self.data["solution"][rowno][colno] is not None:
      return self.data["solution"][rowno][colno]
    return self.data["puzzle"][rowno][colno]

  def getchar(self,rowno,colno):
    if rowno >= self.height() or colno >= self.width():
      raise RuntimeError("puzzle is ({},{}), and getchar was called on ({},{})".format(rowno,colno,self.height(),self.width()))
    return self._getchar(rowno,colno)

  def safe_getchar(self,rowno,colno):
    if (rowno >= self.height() or colno >= self.width() or
        rowno < 0 or colno < 0):
      return '#'
    else:
      return str(self._getchar(rowno,colno))

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
      raise RuntimeError('settitle called with something not a string')
    return self

  def writejson(self,filename):
    try:
      with open(filename, 'w') as f:
        json.dump(self.data, f, indent=2, sort_keys=True)
    except OSError:
      raise RuntimeError('Could not write json to {}'.format(filename))
    return self

  def writesvg(self,filename,**kwargs):
    showcluenumbers=True
    showsolvedcells=True
    showtitle=True
    if 'showcluenumbers' in kwargs:
      if isinstance(kwargs['showcluenumbers'], bool):
        showcluenumbers = kwargs['showcluenumbers']
      else:
        raise RuntimeError('writesvg keyword args need True or False')

    if 'showsolvedcells' in kwargs:
      if isinstance(kwargs['showsolvedcells'], bool):
        showsolvedcells = kwargs['showsolvedcells']
      else:
        raise RuntimeError('writesvg keyword args need True or False')

    if 'showtitle' in kwargs:
      if isinstance(kwargs['showtitle'], bool):
        showtitle = kwargs['showtitle']
      else:
        raise RuntimeError('writesvg keyword args need True or False')

    title = self.gettitle()
    if title is None or title == '':
      title = 'Untitled Crossword Puzzle'

    if 'title' in kwargs:
      if isinstance(kwargs['title'], str):
        title = kwargs['title']
      else:
        raise RuntimeError('titles need to be strings')

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
    if 'unsolved' not in self.data or len(self.data['unsolved']) == 0:
      return None
    thisclue = self.data['unsolved'].pop()
    direction, cluenumber, length = thisclue
    if direction not in Puzzlestate.directions.keys():
      raise RuntimeError(f'{direction} is not a direction')
    row_increment, col_increment = Puzzlestate.directions[direction]

    # now we gather the constraints, i.e., letters already filled in

    constraints = list()
    row,col = self.data['answerlocations'][cluenumber]
    if col >= self.width() or row >= self.height():
      raise RuntimeError('answer location for {} {} is corrupt'.format(cluenumber,direction))

    length = 0
    while True:
      if col == self.width() or row == self.height():
        # remember, rows and cols are numbered from zero
        break
      c = self.getchar(row,col)
      if type(c) == str and c.isalpha():
        constraints.append([length,c])
      if type(c) == str and c == '#':
        break
      row += row_increment
      col += col_increment
      length += 1

    # and now we gather the preferences, i.e., certain letters that are more
    # likely to result in a fillable grid.
    # also find the coldspots, in other words, places in this word that
    # make a downward search path from filling in this clue non-unique.
    # BOAT and BOOT lead to the same searchspace if the third character doesn't
    # matter


    preferences = list()
    coldspots = list()
    row,col = self.data['answerlocations'][cluenumber]
    if col >= self.width() or row >= self.height():
      raise RuntimeError('answer location for {} {} is corrupt'.format(cluenumber,direction))
    if direction == 'Across':
      nextletter = lambda row,col: [ row, col+1 ]
      prevletter = lambda row,col: [ row, col-1 ]
    elif direction == 'Down':
      nextletter = lambda row,col: [ row+1, col ]
      prevletter = lambda row,col: [ row-1, col ]
    else:
      raise RuntimeError(f'what kind of direction is {direction}')

    i = 0
    while True:
      if col == self.width() or row == self.height():
        # remember, rows and cols are numbered from zero
        break
      c = self.getchar(row,col)
      if type(c) == str and c.isalpha():
        # no preferences about this letter, since it's fixed!
        break
      if type(c) == str and c == '#':
        break
      p = self.safe_getchar(*prevletter(row,col))
      n = self.safe_getchar(*nextletter(row,col))

      if p == '#' and n == '#':
        coldspots.append(i)
      elif p.isalpha() and n.isalpha():
        coldspots.append(i)

      if p == 'Q':
        preferences.append([i,self.Letterkind.u])
      elif p in { 'T' , 'S' } and n == 'R':
        preferences.append([i,self.Letterkind.h])
      elif p in self.Letterkind.safe_vowels and n in self.Letterkind.safe_vowels:
        preferences.append([i,self.Letterkind.consonants])
      elif p in self.Letterkind.safe_consonants and n in self.Letterkind.safe_consonants:
        preferences.append([i,self.Letterkind.vowels])

      row += row_increment
      col += col_increment
      i += 1

    return [direction, cluenumber, length, constraints, preferences, coldspots]

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

    row_increment,col_increment = Puzzlestate.directions[direction]

    # first, a test
    row,col = self.data['answerlocations'][cluenumber]
    for c in word:
      if row < 0 or col < 0:
        raise RuntimeError('no negative indices thank you')
      if col >= self.width():
        raise RuntimeError('tried to access col={} in a puzzle of width {}'.format(col,self.width()))
      if row >= self.height():
        raise RuntimeError('tried to access row={} in a puzzle of height {}'.format(row,self.height()))
      if self.testchar(row,col,c):
        pass
      else:
        raise RuntimeError('hey whoa, {} was supposed to fit at ({},{})'.format(c,row,col))
      row += row_increment
      col += col_increment

    # OK, it fits
    row,col = self.data['answerlocations'][cluenumber]
    for c in word:
      self.setchar(row,col,c)
      row += row_increment
      col += col_increment

    self.addwordused(word)
    return self

  def is_puzzle_solved(self):
    height = self.height()
    width = self.width()
    if len(self.data['puzzle']) != height:
      raise RuntimeError("height of puzzle doesn't match stored height")
    if len(self.data['solution']) != height:
      raise RuntimeError("height of solution doesn't match stored height")
    for i, row in enumerate(self.data['puzzle']):
      if len(row) != width:
        raise RuntimeError("row {} of puzzle doesn't match width".format(i))
      if len(self.data['solution']) != width:
        raise RuntimeError("row {} of solution doesn't match width".format(i))
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

  def sparseness(self):
    size = self.height() * self.width()
    black_squares = sum ( [ sum ([ 1 for col in row if col == '#' ]) for row in self.data['puzzle'] ] )
    if size == 0:
      raise RuntimeError("puzzle is size zero?")
    return black_squares / size


def main():
  if len(sys.argv) == 1:
    sourcefile = "puzzles/baby-animals-crossword.ipuz"
  else:
    sourcefile = sys.argv[1]
  p = Puzzlestate.fromjsonfile(sourcefile)
  print ("source file is {}".format(sourcefile))
  print ("sparseness is {}".format(p.sparseness()))

  p.writesvg("{}.svg".format(sourcefile), showtitle=True)
#  p.writejson("{}.ipuzout".format(sourcefile))

if __name__ == '__main__':
  """for testing"""
  random.seed()
  main()

