#!/usr/bin/env python3
"""
operations on a crossword puzzle state
"""

import random
import json
import copy
import sys
import svgwrite

class Puzzlestate:
  """
  operations on a crossword puzzle state
  """

  # Directions are defined as (rowincrement,colincrement)

  directions = {
    'Across': [0,1],
    'Down': [1,0]
  }

  letterpairfreqs = [
        [ 1, 20, 33, 52, 0, 12, 18, 5, 39, 1, 12, 57, 26, 181, 1, 20, 1, 75, 95, 104, 9, 20, 13, 1, 26, 1 ],
        [ 11, 1, 0, 0, 47, 0, 0, 0, 6, 1, 0, 17, 0, 0, 19, 0, 0, 11, 2, 1, 21, 0, 0, 0, 11, 0 ],
        [ 31, 0, 4, 0, 38, 0, 0, 38, 10, 0, 18, 9, 0, 0, 45, 0, 1, 11, 1, 15, 7, 0, 0, 0, 1, 0 ],
        [ 48, 20, 9, 13, 57, 11, 7, 25, 50, 3, 1, 11, 14, 16, 41, 6, 0, 14, 35, 56, 10, 2, 19, 0, 10, 0 ],
        [ 110, 23, 45, 126, 48, 30, 15, 33, 41, 3, 5, 55, 47, 111, 33, 28, 2, 169, 115, 83, 6, 24, 50, 9, 26, 0 ],
        [ 25, 2, 3, 2, 20, 11, 1, 8, 23, 1, 0, 8, 5, 1, 40, 2, 0, 16, 5, 37, 8, 0, 3, 0, 2, 0 ],
        [ 24, 3, 2, 2, 28, 3, 4, 35, 18, 1, 0, 7, 3, 4, 23, 1, 0, 12, 9, 16, 7, 0, 5, 0, 1, 0 ],
        [ 114, 2, 2, 1, 302, 2, 1, 6, 97, 0, 0, 2, 3, 1, 49, 1, 0, 8, 5, 32, 8, 0, 4, 0, 4, 0 ],
        [ 10, 5, 32, 33, 23, 17, 25, 6, 1, 1, 8, 37, 37, 179, 24, 6, 0, 27, 86, 93, 1, 14, 7, 2, 0, 2 ],
        [ 2, 0, 0, 0, 2, 0, 0, 0, 3, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 8, 0, 0, 0, 0, 0  ],
        [ 6, 1, 1, 1, 29, 1, 0, 2, 14, 0, 0, 2, 1, 9, 4, 0, 0, 0, 5, 4, 1, 0, 2, 0, 2, 0 ],
        [ 40, 3, 2, 36, 64, 10, 1, 4, 47, 0, 3, 56, 4, 2, 41, 3, 0, 2, 11, 15, 8, 3, 5, 0, 31, 0 ],
        [ 44, 7, 1, 1, 68, 2, 1, 3, 25, 0, 0, 1, 5, 2, 29, 11, 0, 3, 10, 1, 9, 8, 0, 4, 0, 18, 0 ],
        [ 40, 7, 25, 146, 66, 8, 92, 16, 33, 2, 8, 9, 7, 8, 60, 4, 1, 3, 33, 106, 6, 2, 12, 0, 11, 0 ],
        [ 16, 12, 13, 18, 5, 80, 7, 11, 12, 1, 13, 26, 48, 106, 36, 15, 0, 84, 28, 57, 115, 12, 46, 0, 5, 1 ],
        [ 23, 1, 0, 0, 30, 1, 0, 3, 12, 0, 0, 15, 1, 0, 21, 10, 0, 18, 5, 11, 6, 0, 1, 0, 1, 0 ],
        [ 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 9, 0, 0, 0, 0, 0  ],
        [ 50, 7, 10, 20, 133, 8, 10, 12, 50, 1, 8, 10, 14, 16, 55, 6, 0, 14, 37, 42, 12, 4, 11, 0, 21, 0 ],
        [ 67, 11, 17, 7, 74, 11, 4, 50, 49, 2, 6, 13, 12, 10, 57, 20, 2, 4, 43, 109, 20, 2, 24, 0, 4, 0 ],
        [ 59, 10, 11, 7, 75, 9, 3, 330, 76, 1, 2, 17, 11, 7, 115, 4, 0, 28, 34, 56, 17, 1, 31, 0, 16, 0 ],
        [ 7, 5, 12, 7, 7, 2, 14, 2, 8, 0, 1, 34, 8, 36, 1, 16, 0, 44, 35, 48, 0, 0, 2, 0, 1, 0 ],
        [ 5, 0, 0, 0, 65, 0, 0, 0, 11, 0, 0, 0, 0, 0, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0 ],
        [ 66, 1, 1, 2, 39, 1, 0, 44, 39, 0, 0, 2, 1, 12, 29, 0, 0, 3, 4, 4, 1, 0, 2, 0, 1, 0 ],
        [ 1, 0, 2, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0  ],
        [ 18, 7, 6, 6, 14, 7, 3, 10, 11, 1, 1, 4, 6, 3, 36, 4, 0, 3, 19, 20, 1, 1, 12, 0, 2, 0 ],
        [ 1, 0, 0, 0, 3, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0  ]
        ]

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

    if isinstance(data['dimensions']['width'],str):
      if data['dimensions']['width'].isnumeric():
        data['dimensions']['width'] = int(data['dimensions']['width'])
      else:
        raise RuntimeError('invalid width')

    if data['dimensions']['width'] <= 0:
      raise RuntimeError('width must be positive')

    if isinstance(data['dimensions']['height'],str):
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
          raise RuntimeError(f"weird cell content: [{row},{col}] is {cellcontents}")

    # now squirrel away the length of the answer for each clue

    for direction in data['clues']:
      if direction not in Puzzlestate.directions.keys():
        raise RuntimeError(f"{direction} is not a direction")
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
          if (xloc == width or yloc == height or
              data['puzzle'][xloc][yloc] == '#'):
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
      raise RuntimeError(f"puzzle is ({self.height()},{self.width()}), and getchar was called on ({rowno},{colno})")
    return self._getchar(rowno,colno)

  def safe_getchar(self,rowno,colno):
    if (rowno >= self.height() or colno >= self.width() or
        rowno < 0 or colno < 0):
      return '#'
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
    if isinstance(c2,int):
      return True # It's either a 0 for an empty space or else a clue number
    if isinstance(c2,str) and c2 in ('?', '*', ' ', '.'):
      return True # Yay!  It's not been filled in yet
    if isinstance(c2,str) and c2.upper() == c.upper():
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
      with open(filename, 'w', encoding='utf-8') as f:
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

    PUZZLESIZE = (f"{WIDTH_MM}mm",f"{HEIGHT}mm")

    drawing = svgwrite.Drawing(filename, size=PUZZLESIZE)
    drawing.viewbox(0, 0, HEIGHT_MM, WIDTH_MM)

    # draw horizontal lines
    for i in range(1,HEIGHT):
      y = TOP_MARGIN_MM + i * CELLSIZE_MM
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
          if isinstance(c,str) and c.isalpha():
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
    if 'unsolved' not in self.data:
      raise RuntimeError('missing unsolved data element')
    if len(self.data['unsolved']) == 0:
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
      if isinstance(c,str) and c.isalpha():
        constraints.append([length,c])
      if isinstance(c,str) and c == '#':
        break
      row += row_increment
      col += col_increment
      length += 1

    # and now we gather coldspots, in other words, places in this word that
    # make a downward search path from filling in this clue non-unique.
    # BOAT and BOOT lead to the same searchspace if the third character doesn't
    # matter

    coldspots = list()
    row,col = self.data['answerlocations'][cluenumber]
    if col >= self.width() or row >= self.height():
      raise RuntimeError('answer location for {} {} is corrupt'.format(cluenumber,direction))
    if direction == 'Across':
      port = lambda row,col: [ row-1, col ]
      starboard = lambda row,col: [ row+1, col ]
    elif direction == 'Down':
      port = lambda row,col: [ row, col+1 ]
      starboard = lambda row,col: [ row, col-1 ]
    else:
      raise RuntimeError(f'what kind of direction is {direction}')

    i = 0
    while True:
      if col == self.width() or row == self.height():
        # remember, rows and cols are numbered from zero
        break
      c = self.getchar(row,col)
      if isinstance(c,str) and c.isalpha():
        # no preferences about this letter, since it's fixed!
        break
      if isinstance(c,str) and c == '#':
        break
      p = self.safe_getchar(*starboard(row,col))
      n = self.safe_getchar(*port(row,col))

      if p == '#' and n == '#':
        coldspots.append(i)

      row += row_increment
      col += col_increment
      i += 1

    return [direction, cluenumber, length, constraints, coldspots]

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

  def test_word(self,word,direction,cluenumber):

    row_increment,col_increment = Puzzlestate.directions[direction]

    row,col = self.data['answerlocations'][cluenumber]
    for c in word:
      if row < 0 or col < 0:
        return False
      if col >= self.width():
        return False
      if row >= self.height():
        return False
      if self.testchar(row,col,c):
        pass
      else:
        return False
      row += row_increment
      col += col_increment
    return True

  def score_word(self,tryword,direction,cluenumber,safe=True):
    # returns object containing the word if it was able to inscribe it,
    # else returns none

    if safe:
      if self.test_word(tryword,direction,cluenumber):
        pass
      else:
        return None

    row_increment,col_increment = Puzzlestate.directions[direction]
    if direction == 'Across':
      port = lambda row,col: [ row, col+1 ]
      starboard = lambda row,col: [ row, col-1 ]
    elif direction == 'Down':
      port = lambda row,col: [ row+1, col ]
      starboard = lambda row,col: [ row-1, col ]
    else:
      raise RuntimeError(f'what kind of direction is {direction}')

    row,col = self.data['answerlocations'][cluenumber]
    score = 0
    for c in tryword:
      predecessor = self.safe_getchar(*starboard(row,col))
      successor = self.safe_getchar(*port(row,col))

      if predecessor == '#' and successor == '#':
        # no preferences about this letter, since it's surrounded by borders!
        row += row_increment
        col += col_increment
        continue
      if isinstance(predecessor,str) and predecessor.isalpha():
        score += self.letterpairfreqs[ord(predecessor)-65][ord(c)-65]
      if isinstance(successor,str) and successor.isalpha():
        score += self.letterpairfreqs[ord(c)-65][ord(successor)-65]

      row += row_increment
      col += col_increment

    return score

  def inscribe_word(self,word,direction,cluenumber,safe=True):
    """
    returns object containing the word if it was able to inscribe it,
    else returns none
    """

    if safe:
      if self.test_word(word,direction,cluenumber):
        pass
      else:
        return None

    row_increment,col_increment = Puzzlestate.directions[direction]

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
    black_squares = sum ( [ sum ([ 1 for col in row if col == '#' ]) 
                                   for row in self.data['puzzle'] ] )
    if size == 0:
      raise RuntimeError("puzzle is size zero?")
    return black_squares / size


def main():
  """for testing"""
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
