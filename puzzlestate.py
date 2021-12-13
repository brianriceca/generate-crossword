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

  # Directions are defined as [rowincrement,colincrement]

  directions = {
    'Across': [0,1],
    'Down': [1,0]
  }

  UNSOLVED = '.'
  BARRIER = '#'

  _fn = 'vowel_friendly_weightings.json'
  try:
    with open(_fn,encoding='utf-8') as f:
      i_like_vowels = json.load(f)
  except OSError:
    raise RuntimeError(f'Could not read json from {_fn}')

  _fn = 'consonant_friendly_weightings.json'
  try:
    with open(_fn,encoding='utf-8') as f:
      i_like_consonants = json.load(f)
  except OSError:
    raise RuntimeError(f'Could not read json from {_fn}')

  _fn = 'final_friendly_weightings.json'
  try:
    with open(_fn,encoding='utf-8') as f:
      i_like_finals = json.load(f)
  except OSError:
    raise RuntimeError(f'Could not read json from {_fn}')

  _fn = 'letter_pair_freqs.json'
  try:
    with open(_fn,encoding='utf-8') as f:
      letterpairfreqs = json.load(f)
  except OSError:
    raise RuntimeError(f'Could not read json from {_fn}')

  def __init__(self,data):
    self.data = data

  @classmethod
  def blank(cls,height,width):
    if int(width) <= 0 or int(height) <= 0:
      return None
    return cls( {"dimensions": {"height": int(height),
                                "width": int(width)},
                 "wordsused": set(),
                 "puzzle":
                  [[Puzzlestate.UNSOLVED for i in range(width)]
                    for j in range(height)] ,
                 "solution":
                  [[Puzzlestate.UNSOLVED for i in range(width)] 
                    for j in range(height)] })


  @classmethod
  def fromjsonfile(cls,filename):
    def _barrier_or_unsolved(target,row,col):
      if data[target][row][col] == Puzzlestate.BARRIER:
        return Puzzlestate.BARRIER
      return Puzzlestate.UNSOLVED

    try:
      with open(filename,encoding='utf-8') as f:
        data = json.load(f)
    except OSError:
      raise RuntimeError(f'Could not read json from {filename}')

    # all the validation happens here

    if 'puzzle' not in data:
      raise RuntimeError('this puzzle file lacks a puzzle')

    if not isinstance(data['puzzle'], list):
      raise RuntimeError('this puzzle file\'s puzzle is the wrong kind of data structure')
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

    if len(data['puzzle']) != data['dimensions']['height']:
      raise RuntimeError(f"puzzle should be {data['dimensions']['height']} rows high, is {len(data['puzzle'])}")

    for rownumber, row in enumerate(data['puzzle']):
      if not isinstance(row, list):
        raise RuntimeError('this puzzle file\'s puzzle is the wrong kind of data structure')
      if len(row) != width:
        raise RuntimeError(f"puzzle row {rownumber} should be {data['dimensions']['width']} columns wide, is {len(row)}")

    # now we start populating fields of the puzzle object

    width = int(data['dimensions']['width'])
    height = int(data['dimensions']['height'])

    if 'wordsused' not in data.keys():
      data['wordsused'] = set()

    if 'solution' not in data.keys():
      for row in range(height):
        for col in range(width):
          if (type(data['puzzle'][row][col],int) or
                   data['puzzle'][row][col] == Puzzlestate.UNSOLVED):
            data['solution'] = Puzzlestate.UNSOLVED
          else:
            data['solution'][row][col] = chr(data['puzzle'][row][col])
          
    if 'answerlocations' not in data.keys():
      data['answerlocations'] = {}
    if 'answerlengths' not in data.keys():
      data['answerlengths'] = {}
    if 'unsolved' not in data.keys():
      data['unsolved'] = []

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
        elif isinstance(cellcontents,str) and cellcontents == Puzzlestate.BARRIER:
          pass
        elif isinstance(cellcontents, dict):
          raise RuntimeError("I don't know how to deal with fancy cells yet")
        else:
          raise RuntimeError(f"weird cell content: [{row},{col}] is {cellcontents}")

    # now squirrel away the length of the answer for each clue,
    # as well as, for each [row,col] all the clues that touch that space

    data['clues_that_touch'] = [[ set() for i in range(width)]
                    for j in range(height)] 

    for direction in data['clues']:
      if direction not in Puzzlestate.directions.keys():
        raise RuntimeError(f"{direction} is not a direction")
      for cluenumber in data['clues'][direction]:
        row,col = data['answerlocations'][cluenumber[0]]
        # [1] is the clue for a human solver, we don't care about that
        if data['puzzle'][row][col] != cluenumber[0]:
          raise RuntimeError(f"found a mismatch at ({row},{col}): expected {cluenumber}, saw {data['puzzle'][row][col]}")

      # now we count the number of blanks from the start of the clue, 
      # in the given direction, to the next BARRIER or boundary

        n = 1
        while True:
          row += Puzzlestate.directions[direction][0]
          col += Puzzlestate.directions[direction][1]
          if (col == width or row == height or
              data['puzzle'][row][col] == Puzzlestate.BARRIER):
            break
          data['clues_that_touch'][row][col].add( [ direction, cluenumber[0] ] )
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
      return Puzzlestate.BARRIER
    result = self._getchar(rowno,colno)
    if type(result,int):
      return Puzzlestate.UNSOLVED
    return result

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
    if isinstance(c2,str) and c2 == Puzzlestate.UNSOLVED:
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
      raise RuntimeError(f'Could not write json to {filename}') from None
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

    _fn = 'puzzle_svg_params.json'
    try:
      with open(_fn,encoding='utf-8') as f:
        _s = json.load(f)
    except OSError:
      raise RuntimeError(f'Could not read json from {_fn}')

    _w = self.width()
    _h = self.height()
    if showtitle:
      pass
    else:
      _s['titleheight_mm'] = 0

    _s['top_margin_mm'] = _s['cellsize_mm'] + _s['titleheight_mm']
    _s['bottom_margin_mm'] = _s['cellsize_mm']
    _s['side_margin_mm'] = _s['cellsize_mm']

    _s['width_mm'] = _s['cellsize_mm']*_w + 2*_s['side_margin_mm']
    _s['height_mm'] = (_s['cellsize_mm']*_h + 
                       _s['top_margin_mm'] +
                       _s['bottom_margin_mm'])

    drawing = svgwrite.Drawing(filename, 
              size=(f"{_s['width_mm']}mm",f"{_s['height_mm']}mm"))
    drawing.viewbox(0, 0, _s['height_mm'], _s['width_mm'])

    # draw interior horizontal lines
    for i in range(1,_s['height']):
      y = _s['top_margin_mm'] + i * _s['cellsize_mm']
      drawing.add(drawing.line(
                          start=(_s['side_margin_mm'], y), 
                          end=(_s['cellsize_mm']*_w+_s['side_margin_mm'], y),
                          stroke=_s['line_color'],stroke_width=_s['line_width']))

    # draw top and bottom lines
    drawing.add(drawing.line(
                        start=(_s['side_margin_mm'], _s['top_margin_mm']+_s['height']*_s['cellsize_mm']),
                        end=(_s['cellsize_mm']*_w+_s['side_margin_mm'], _s['top_margin_mm']+_s['height']*_s['cellsize_mm']),
                        stroke=_s['line_color'],stroke_width=_s['line_width'], style=_s['outer_line_style']))

    drawing.add(drawing.line(
                        start=(_s['side_margin_mm'], _s['top_margin_mm']),
                        end=(_s['cellsize_mm']*_w+_s['side_margin_mm'], _s['top_margin_mm']),
                        stroke=_s['line_color'],stroke_width=_s['line_width'], style=_s['outer_line_style']))

    # draw vertical lines
    for i in range(1,_w):
      x = _s['side_margin_mm'] + i * _s['cellsize_mm']
      drawing.add(drawing.line(
                          start=(x,_s['top_margin_mm']), 
                          end=(x,_s['cellsize_mm']*_s['height']+_s['top_margin_mm']),

                          stroke=_s['line_color'],stroke_width=_s['line_width']))

    drawing.add(drawing.line(
                        start=(_s['side_margin_mm'],_s['top_margin_mm']),
                        end=(_s['side_margin_mm'], _s['cellsize_mm']*_h'+_s['top_margin_mm']),
                        stroke=LINE_COLOR,stroke_width=1,style=_s['outer_line_style']))
    drawing.add(drawing.line(
                        start=(_s['cellsize_mm']*_w+_s['side_margin_mm'],_s['top_margin_mm']), 
                        end=(_s['cellsize_mm']*_w+_s['side_margin_mm'], _s['cellsize_mm']*_h + _s['top_margin_mm']),
                        stroke=_s['line_color'],stroke_width=_s['line_width'],style=_s['outer_line_style']))


    # insert black boxes
    for row in range(_h):
      for col in range(_w):
        if self.getchar(row,col) == Puzzlestate.BARRIER:
          drawing.add(drawing.rect(
                           insert=(
                                   col*_s['cellsize_mm']+_s['side_margin_mm'],
                                   row*_s['cellsize_mm']+_s['top_margin_mm']
                                  ),
                           size=(_s['cellsize_mm'],_s['cellsize_mm']),
                           fill=_s['block_color']))

    if showcluenumbers:
      g = drawing.g(class_='cluenumber',style = _s['cluenumber_style'])
      for answer in self.data['answerlocations'].keys():
        row,col = self.data['answerlocations'][answer]

        g.add(drawing.text(answer,
                    insert=(
                            col*_s['cellsize_mm']+_s['side_margin_mm']+_s['offset_cluenum_x'],
                            row*_s['cellsize_mm']+_s['top_margin_mm']+_s['offset_cluenum_y'],
                           )))
      drawing.add(g)

    if showsolvedcells:
      g = drawing.g(class_='solvedcell', style = _s['solution_style'])
      for row in range(_h):
        for col in range(_w):
          c = self.getchar(row,col)
          if isinstance(c,str) and c.isalpha():
            g.add(drawing.text(self.getchar(row,col),
                    insert=(
                            col*_s['cellsize_mm']+_s['side_margin_mm']+_s['offset_solution_x'],
                            row*_s['cellsize_mm']+_s['top_margin_mm']+_s['offset_solution_y'],
                           )))
      drawing.add(g)

    if showtitle:
      g = drawing.g(class_='title', style = _s['title_style'])
      g.add(drawing.text(title,
                    insert=(
                            _s['side_margin_mm'],
                            _s['title_height_mm']
                           )))
      drawing.add(g)


    drawing.save()

  def intersecting_clues(self, cluenumber, direction):
    intersections = set()
    row, col = data['answerlocations'][cluenumber]
    row_increment, col_increment = Puzzlestate.directions[direction]
    while True:
      if col == self.width() or row == self.height():
        # remember, rows and cols are numbered from zero
        break
      for c,d in self.data['clues_that_touch'][row][col]:
        if c != cluenumber or d != direction:
          intersections.add( [c,d] )
      row += row_increment   
      col += col_increment   
    return intersections

  def random_unsolved_clue(self):
    if 'unsolved' not in self.data:
      raise RuntimeError('missing unsolved data element')
    if len(self.data['unsolved']) == 0:
      return None
    try:
      prevdirection, prevcluenumber = random.choice( self.data['solved_clues'] )
      direction, cluenumber = random.choice( self.find_intersectors(prevdirection, prevcluenumber) )
      length = self.data['answerlengths'][repr([ direction, cluenumber ])]
    except IndexError:
      thisclue = self.data['unsolved'].pop()
      direction, cluenumber, length = thisclue
      if direction not in Puzzlestate.directions.keys():
        raise RuntimeError(f'{direction} is not a direction') from None

    row_increment, col_increment = Puzzlestate.directions[direction]
      
    # now we gather the constraints, i.e., letters already filled in

    constraints = []
    row,col = self.data['answerlocations'][cluenumber]
    if col >= self.width() or row >= self.height():
      raise RuntimeError(f'answer location for {cluenumber} {direction} is corrupt')

    length = 0
    while True:
      if col == self.width() or row == self.height():
        # remember, rows and cols are numbered from zero
        break
      c = self.getchar(row,col)
      if isinstance(c,str) and c.isalpha():
        constraints.append([length,c])
      if isinstance(c,str) and c == BARRIER:
        break
      row += row_increment
      col += col_increment
      length += 1

    # and now we gather coldspots, in other words, places in this word that
    # make a downward search path from filling in this clue non-unique.
    # BOAT and BOOT lead to the same searchspace if the third character doesn't
    # matter

    coldspots = []
    row,col = self.data['answerlocations'][cluenumber]
    if col >= self.width() or row >= self.height():
      raise RuntimeError(f'answer location for {cluenumber} {direction} is corrupt')
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
      if isinstance(c,str) and c == BARRIER:
        break
      p = self.safe_getchar(*starboard(row,col))
      n = self.safe_getchar(*port(row,col))

      if p == BARRIER and n == BARRIER:
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

    # is that first space an even space or an odd space?

    if row % 2:
      if col % 2: 
        score_machine =  [lambda x: Puzzlestate.i_like_vowels[ord(x)-65] ,
                          lambda x: Puzzlestate.i_like_cons[ord(x)-65] ]
      else:
        score_machine =  [lambda x: Puzzlestate.i_like_cons[ord(x)-65] ,
                          lambda x: Puzzlestate.i_like_vowels[ord(x)-65] ]
    else:
      if col % 2: 
        score_machine =  [lambda x: Puzzlestate.i_like_cons[ord(x)-65] ,
                          lambda x: Puzzlestate.i_like_vowels[ord(x)-65] ]
      else:
        score_machine =  [lambda x: Puzzlestate.i_like_vowels[ord(x)-65] ,
                          lambda x: Puzzlestate.i_like_cons[ord(x)-65] ]

    score = 0
    for i,c in enumerate(tryword):
      predecessor = self.safe_getchar(*starboard(row,col))
      successor = self.safe_getchar(*port(row,col))

      if ( (predecessor == Puzzlestate.BARRIER and successor == Puzzlestate.BARRIER) or
           (predecessor == Puzzlestate.UNSOLVED and successor == Puzzlestate.UNSOLVED) ):
        if len(tryword) == i:
          score += Puzzlestate.i_like_finals[ord(c)-65]
        else:
          score += score_machine[i % 2](c)       
        row += row_increment
        col += col_increment
        continue
      if isinstance(successor,str) and successor.isalpha():
        score += self.letterpairfreqs[ord(c)-65][ord(successor)-65]
      elif isinstance(predecessor,str) and predecessor.isalpha():
        score += self.letterpairfreqs[ord(predecessor)-65][ord(c)-65]

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
        elif isinstance(c,str):
          print(c, ' ', end='')
        elif isinstance(c,int):
          print(c, "?", end='')
        else:
          print("¿ ", end='')
      print()

  def json(self):
    return json.dumps(self.data)

  def print_solution(self):
    for rowno in range(self.height()):
      for colno in range(self.width()):
        c = self.data['solution'][rowno][colno]
        if c is None or c == '':
          print('0 ', end='')
        elif isinstance(c,str):
          print(c, ' ', end='')
        elif isinstance(c,int):
          print(c, "?", end='')
        else:
          print("¿ ", end='')
      print()

  def sparseness(self):
    size = self.height() * self.width()
    black_squares = sum ( [ sum ([ 1 for col in row if col == Puzzlestate.BARRIER ]) 
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
  puzzle = Puzzlestate.fromjsonfile(sourcefile)
  print (f"source file is {sourcefile}")
  print (f"sparseness is {puzzle.sparseness()}")

  puzzle.writesvg(f"{sourcefile}.svg".format(sourcefile), showtitle=True)
#  puzzle.writejson("f{sourcefile}.out.ipuz")

if __name__ == '__main__':
  random.seed()
  main()
