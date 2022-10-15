#!/usr/bin/env python3
"""
operations on a crossword puzzle state
"""

import random
import json
import copy
import sys
import os
import logging
from itertools import permutations

import svgwrite

script_folder = os.path.dirname(os.path.realpath(__file__))

class Puzzlestate:
  """
  operations on a crossword puzzle state
  """

  directions = {
    'Across': [0,1],
    'Down': [1,0]
  }

  UNSOLVED = '.'
  BARRIER = '#'

  def _slurpjson(fn):
    result = dict()
    if os.path.isabs(fn):
      pass
    else:
      fn = os.path.join(script_folder,fn)
    try:
      with open(fn,encoding='utf-8') as f:
        result = json.load(f)
    except OSError:
      raise RuntimeError(f'Could not read json from {fn}')
    return result

  def _clue_stringify(**kwargs):
    '''transform a clue as dict to a clue as string'''
    assert 'direction' in kwargs and 'cluenumber' in kwargs, \
      f'This is not a proper clue: {repr(kwargs)}'
    return str(kwargs['cluenumber']) + ' ' + kwargs['direction']

  def _clue_dictify(s):
    '''transform a clue as string to a clue as dict'''
    c = s.split()
    return { 'cluenumber': int(c[0]), 'direction': str(c[1]) }

  def _clue_tupleify(s):
    '''transform a clue as string to a clue as tuple'''
    c = s.split()
    return [ int(c[0]), str(c[1]) ]

  # Directions are defined as [rowincrement,colincrement]

  i_like_vowels = _slurpjson('vowel_friendly_weightings.json')
  i_like_cons = _slurpjson('consonant_friendly_weightings.json')
  i_like_finals = _slurpjson('final_friendly_weightings.json')
  letterpairfreqs = _slurpjson('letter_pair_freqs.json')
  singleletterfreqs = _slurpjson('single_letter_weightings.json')

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
                  [[Puzzlestate.UNSOLVED for col in range(width)]
                    for row in range(height)] ,
                 "solution":
                  [[Puzzlestate.UNSOLVED for col in range(width)]
                    for row in range(height)] })


  @classmethod
  def fromjsonfile(cls,filename):
    def _barrier_or_unsolved(target,row,col):
      '''
      can be called on 'puzzle' or 'solution'
      the advantage if used on 'puzzle' is that it doesn't treat the first
      cell of an answer as special (just because it has a number in it)
      '''
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
      raise RuntimeError(f'File {filename} puzzle file lacks a puzzle')

    if 'clues' not in data:
      raise RuntimeError(f'File {filename} lacks clues')

    if not isinstance(data['puzzle'], list):
      raise RuntimeError(f'File {filename} has a puzzle element w/ the wrong kind of data structure')
    if ('dimensions' not in data.keys() or
        'width' not in data['dimensions'].keys() or
        'height' not in data['dimensions'].keys()):
      raise RuntimeError(f'File {filename} missing puzzle dimension')

    # the list of clues for each direction needs to be a dict, but unfortunately
    # the JSON called for by the ipuz standard makes it a list, arrrgh

    for d in Puzzlestate.directions:
      if not isinstance(data['clues'][d],dict):
        if not isinstance(data['clues'][d],list):
          raise RuntimeError(f"File {filename} has a {d} clues element of type {type(data['clues'][d])}, which is bizarre")

    if isinstance(data['dimensions']['width'],str):
      if data['dimensions']['width'].isnumeric():
        data['dimensions']['width'] = int(data['dimensions']['width'])
      else:
        raise RuntimeError(f"File {filename} invalid width {data['dimensions']['width']}")

    if isinstance(data['dimensions']['height'],str):
      if data['dimensions']['height'].isnumeric():
        data['dimensions']['height'] = int(data['dimensions']['height'])
      else:
        raise RuntimeError(f"File {filename} invalid height {data['dimensions']['height']}")
        raise RuntimeError('invalid height')

    if data['dimensions']['width'] <= 0:
      raise RuntimeError('width must be positive')
    if data['dimensions']['height'] <= 0:
      raise RuntimeError('height must be positive')

    if len(data['puzzle']) != data['dimensions']['height']:
      raise RuntimeError(f"puzzle should be {data['dimensions']['height']} rows high, is {len(data['puzzle'])}")

    for rownumber, row in enumerate(data['puzzle']):
      if not isinstance(row, list):
        raise RuntimeError(f'File {filename} \'s puzzle is the wrong kind of data structure')
      if len(row) != data['dimensions']['width']:
        raise RuntimeError(f"puzzle row {rownumber} should be {data['dimensions']['width']} columns wide, is {len(row)}")

    # now we start populating other fields of the puzzle object

    width = int(data['dimensions']['width'])
    height = int(data['dimensions']['height'])

    if 'wordsused' not in data.keys():
      data['wordsused'] = set()
      # TODO: detect the words in the solution, if any, and add them to the set

    if 'solution' not in data.keys():
      data['solution'] = copy.deepcopy(data['puzzle'])
      for row in range(height):
        for col in range(width):
          if (isinstance(data['puzzle'][row][col],int)):
            # solution shouldn't have clue numbers in the first cell of answers
            data['solution'][row][col] = Puzzlestate.UNSOLVED

    if 'answerlocations' not in data:
      data['answerlocations'] = {}
    if 'answerlengths' not in data:
      data['answerlengths'] = {}
    if 'clues_expanded' not in data:
      data['clues_expanded'] = {}

    if 'solved_clues' not in data:
      data['solved_clues'] = list()
    if 'unsolved_clues' not in data:
      data['unsolved_clues'] = list(data['clues_expanded'].keys())
  
    # squirrel away the clue locations; make sure any filled cells are uppercase

    for row in range(height):
      for col in range(width):
        cellcontents = data['puzzle'][row][col]
        # first, let's determine whether what's here is a clue number,
        # and make sure it is an integer if it is

        if isinstance(thisclue := cellcontents,int):
          # cool, no work to do, let's just confirm it's positive
          if thisclue < 0:
            raise RuntimeError(f'whoa, clue numbers must be positive, unlike [{row},{col}], which is {cellcontents}')
          elif thisclue == 0:
            cellcontents = Puzzlestate.UNSOLVED
          else:
            data['answerlocations'][thisclue] = [row,col]
        elif isinstance(thisclue,str):
          if thisclue.isdigit():
            data['puzzle'][row][col] = int(thisclue)
            data['answerlocations'][int(thisclue)] = [row,col]
          elif (cellcontents == Puzzlestate.UNSOLVED or
                cellcontents == Puzzlestate.BARRIER):
            pass
          else:
            data['puzzle'][row][col] = data['puzzle'][row][col].upper()
        elif isinstance(cellcontents, dict):
          raise RuntimeError("I don't know how to deal with fancy cells yet")
        else:
          raise RuntimeError(f"weird cell content: [{row},{col}] is {cellcontents}, type {type(cellcontents)}")

    # now squirrel away the length of the answer for each clue,
    # as well as, for each [row,col] all the clues that touch that space

    data['clues_that_touch_cell'] = [[ set() for i in range(width)]
                    for j in range(height)]

    _clues_that_touch_clue = dict()
    for direction in data['clues']:
      if direction not in Puzzlestate.directions:
        raise RuntimeError(f"{direction} is not a direction")
      for clue in data['clues'][direction]:
        cluenumber = int(clue[0])
        row,col = data['answerlocations'][cluenumber]
        assert data['puzzle'][row][col] == cluenumber, \
          f"at ({row},{col}): expected {cluenumber}, saw {data['puzzle'][row][col]}"

        # now we count the number of blanks from the start of the clue,
        # in the given direction, to the next BARRIER or boundary

        n = 1
        while True:
          data['clues_that_touch_cell'][row][col].add(Puzzlestate._clue_stringify(direction=direction, cluenumber=cluenumber ))
          row += Puzzlestate.directions[direction][0]
          col += Puzzlestate.directions[direction][1]
          if (col == width or row == height or
              data['puzzle'][row][col] == Puzzlestate.BARRIER):
            break
          n += 1

        data['answerlengths'][Puzzlestate._clue_stringify(direction=direction, cluenumber=cluenumber)] = n
        data['unsolved_clues'].append(Puzzlestate._clue_stringify(direction=direction, cluenumber=cluenumber))

    # now we have, for each cell, a set of clues that touch that cell
    # let's transpose that into, for each clue, a set of (other) clues that touch
    # that clue

    for row in range(height):
      for col in range(width):
        for cluea,clueb in list(permutations(data['clues_that_touch_cell'][row][col],2)):
          if cluea not in _clues_that_touch_clue:
            _clues_that_touch_clue[cluea] = set()
          _clues_that_touch_clue[cluea].add(clueb)

    # now let's populate clues_expanded
    # sample dict item:
    # '1 Down': { cluetext: 'Launches', length: 5, [ '1 Across', '14 Across', '17 Across', '20 Across']

    for d in data['clues']:
      for numberpluscluetext in data['clues'][d]:
        cno = int(numberpluscluetext[0])
        cluetext = numberpluscluetext[1]
        myclue = Puzzlestate._clue_stringify(cluenumber=cno,direction=d)
        data['clues_expanded'][myclue] = {
          'cluetext': cluetext,
          'wordlength': data['answerlengths'][myclue],
          'location': data['answerlocations'][cno],             # [row,col]
          'intersecting_clues': _clues_that_touch_clue[myclue]
        }

    return cls(data)

#####################
# OK, that's all the constructors
#####################

  def height(self):
    return self.data["dimensions"]["height"]
  def getheight(self):
    return self.height()

  def width(self):
    return self.data["dimensions"]["width"]
  def getwidth(self):
    return self.width()

  def _getchar(self,rowno,colno,target='solution'):
    return self.data["solution"][rowno][colno]

  def getchar(self,rowno,colno,target='solution'):
    assert target in ('puzzle','solution'), \
      f'expected either puzzle or solution, got {target}'
    assert rowno < self.height() and colno < self.width(), \
      f"puzzle is ({self.height()},{self.width()}), and getchar was called on ({rowno},{colno})"
    return self._getchar(rowno,colno,target=target)

  def safe_getchar(self,rowno,colno,target='solution'):
    assert target in ('puzzle','solution'), \
      f'expected either puzzle or solution, got {target}'
    if (rowno >= self.height() or colno >= self.width() or
        rowno < 0 or colno < 0):
      return Puzzlestate.BARRIER
    result = self._getchar(rowno,colno,target=target)
    if isinstance(result,int):
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

  def setint(self,rowno,colno,i):
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
    self.data["puzzle"][rowno][colno] = int(i)
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

  def setbarrier(self,rowno,colno):
    self.data['puzzle'][rowno][colno] = Puzzlestate.BARRIER

  def clearbarrier(self,rowno,colno):
    self.data['puzzle'][rowno][colno] = Puzzlestate.UNSOLVED

  def togglebarrier(self,rowno,colno):
    if self.data['puzzle'][rowno][colno] == Puzzlestate.UNSOLVED:
      self.data['puzzle'][rowno][colno] = Puzzlestate.BARRIER
    else:
      self.data['puzzle'][rowno][colno] = Puzzlestate.UNSOLVED

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
    self.data['wordsused'] = list(self.data['wordsused'])
    try:
      with open(filename, 'w', encoding='utf-8') as f:
        listify = lambda x: list(x)
        json.dump(self.data, f, indent=2, sort_keys=True, default=listify)
    except OSError:
      raise RuntimeError(f'Could not write json to {filename}') from None
    self.data['wordsused'] = set(self.data['wordsused'])
    return self

  def writesvg(self,filename,**kwargs):
    if 'showcluenumbers' in kwargs and not isinstance(kwargs['showcluenumbers'], bool):
        raise RuntimeError('showcluenumbers arg must be True or False')

    if 'showsolvedcells' in kwargs and not isinstance(kwargs['showsolvedcells'], bool):
        raise RuntimeError('showsolvedcells arg must be True or False')

    if 'showtitle' in kwargs and not isinstance(kwargs['showtitle'], bool):
        raise RuntimeError('showsolvedcells arg must be True or False')

    if 'highlight_cells' in kwargs and not isinstance(kwargs['highlight_cells'], list):
        raise RuntimeError('highlight_cells value must be a list of [startingcell,direction,count]')

    if 'text_below_puzzle' in kwargs and not isinstance(kwargs['text_below_puzzle'], str):
        raise RuntimeError('text_below_puzzle arg must be a str')

    title = self.gettitle()
    if title is None or title == '':
      title = 'Untitled Crossword Puzzle'

    if 'title' in kwargs:
      if isinstance(kwargs['title'], str):
        title = kwargs['title']
      else:
        raise RuntimeError('titles need to be strings')

    _fn = 'svg_params.json'
    try:
      with open(_fn,encoding='utf-8') as f:
        _s = json.load(f)
    except OSError:
      raise RuntimeError(f'Could not read my SVG params from {_fn}')

    _w = self.width()
    _h = self.height()
    if 'showtitle' not in kwargs or not kwargs['showtitle']:
      _s['title_height_mm'] = 0

    _s['top_margin_mm'] = _s['cellsize_mm'] + _s['title_height_mm']
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
    for i in range(1,_h):
      y = _s['top_margin_mm'] + i * _s['cellsize_mm']
      drawing.add(drawing.line(
                          start=(_s['side_margin_mm'], y),
                          end=(_s['cellsize_mm']*_w+_s['side_margin_mm'], y),
                          stroke=_s['line_color'],stroke_width=_s['line_width']))

    # draw top and bottom lines
    drawing.add(drawing.line(
                        start=(_s['side_margin_mm'], _s['top_margin_mm']+_h*_s['cellsize_mm']),
                        end=(_s['cellsize_mm']*_w+_s['side_margin_mm'], _s['top_margin_mm']+_h*_s['cellsize_mm']),
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
                          end=(x,_s['cellsize_mm']*_h+_s['top_margin_mm']),

                          stroke=_s['line_color'],stroke_width=_s['line_width']))

    drawing.add(drawing.line(
                        start=(_s['side_margin_mm'],_s['top_margin_mm']),
                        end=(_s['side_margin_mm'], _s['cellsize_mm']*_h+_s['top_margin_mm']),
                        stroke=_s['line_color'],stroke_width=1,style=_s['outer_line_style']))
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

    # insert highlights

    if 'highlight_cells' in kwargs:
      for rc, direction, cellcount in kwargs['highlight_cells']:
        row,col = rc
        row_increment, col_increment = Puzzlestate.directions[direction]

        i = 0
        while i < cellcount:
          drawing.add(drawing.rect(
                           insert=(
                                   col*_s['cellsize_mm']+_s['side_margin_mm'],
                                   row*_s['cellsize_mm']+_s['top_margin_mm']
                                  ),
                           size=(_s['cellsize_mm'],_s['cellsize_mm']),
                           fill=_s['highlight_color']))
          row += row_increment
          col += col_increment
          i += 1

    if 'showcluenumbers' in kwargs and kwargs['showcluenumbers']:
      g = drawing.g(class_='cluenumber',style = _s['cluenumber_style'])
      for answer in self.data['answerlocations'].keys():
        row,col = self.data['answerlocations'][answer]

        g.add(drawing.text(answer,
                    insert=(
                            col*_s['cellsize_mm']+_s['side_margin_mm']+_s['offset_cluenum_x'],
                            row*_s['cellsize_mm']+_s['top_margin_mm']+_s['offset_cluenum_y'],
                           )))
      drawing.add(g)

    if 'showsolvedcells' in kwargs and kwargs['showsolvedcells']:
      g = drawing.g(class_='solvedcell', style = _s['solution_style'])
      for row in range(_h):
        for col in range(_w):
          c = self.getchar(row,col)
          if isinstance(c,str) and c.isalpha():
            g.add(drawing.text(c,
                    insert=(
                            col*_s['cellsize_mm']+_s['side_margin_mm']+_s['offset_solution_x'],
                            row*_s['cellsize_mm']+_s['top_margin_mm']+_s['offset_solution_y'],
                           )))
      drawing.add(g)

    if 'showtitle' in kwargs and kwargs['showtitle']:
      if title is None or title == '':
        mytitle = self.gettitle()
      else:
        mytitle = title
      g = drawing.g(class_='title', style = _s['title_style'])
      g.add(drawing.text(title,
                    insert=(
                            _s['side_margin_mm'],
                            _s['title_height_mm']
                           )))
      drawing.add(g)


    drawing.save()

  def intersecting_clues(self, cluenumber, direction):
    return self.data[Puzzlestate._clue_stringify(
                                            cluenumber=cluenumber,
                                            direction=direction)]['intersecting_clues']


  def unsolved_clues(self):
    '''
    return a dict of clues to be solved
    { 'clue' : str : 
      'wordlength' : int,
      'constraints' : [ [ index, whichchar ], ... ],
      'coldspots' : [ index, ... ]
    }
    '''
    if 'unsolved_clues' not in self.data:
      raise RuntimeError('missing unsolved data element')
    if 'solved_clues' not in self.data:
      raise RuntimeError('missing solved_clues data element')

    if len(self.data['unsolved_clues']) == 0:
      # wow, nothing left to do!
      return None


    unsolved_clue_list = self.data['unsolved_clues']
    
    helpful_clue_dict = {}

    for clue in unsolved_clue_list:
      cluenumber, direction = Puzzlestate._clue_tupleify(clue)
      row_increment, col_increment = Puzzlestate.directions[direction]

      helpful_clue_dict[clue] = {}
      # now we gather the constraints, i.e., letters already filled in

      if 'constraints' in self.data['clues_expanded'][clue]:
        helpful_clue_dict[clue]['constraints'] = self.data['clues_expanded'][clue]['constraints']
      else:
        helpful_clue_dict[clue]['constraints'] = []
      helpful_clue_dict[clue]['wordlength'] = self.data['answerlengths'][clue]

      # and now we gather coldspots, in other words, places in this word that
      # make a downward search path from filling in this clue non-unique.
      #    ? ? B ?
      #    ? ? O ?
      #    # # A #
      #    ? ? T ?
      # BOOT would lead to the same searchspace as BOAT searchspace if the third character doesn't matter
  
      coldspots = []
      row,col = self.data['answerlocations'][cluenumber]
      if col >= self.width() or row >= self.height():
        raise RuntimeError(f'answer location for {cluenumber} {direction} is corrupt')
      assert direction in ('Across','Down'), \
        f'what kind of direction is {direction}'
      if direction == 'Across':
        port = lambda row,col: [ row-1, col ]
        starboard = lambda row,col: [ row+1, col ]
      else:
        port = lambda row,col: [ row, col+1 ]
        starboard = lambda row,col: [ row, col-1 ]
  
      i = 0
      while True:
        if col == self.width() or row == self.height():
          # remember, rows and cols are numbered from zero
          break
        c = self.getchar(row,col)
        if isinstance(c,str) and c.isalpha():
          # no preferences about this letter, since it's fixed!
          break
        if isinstance(c,str) and c == Puzzlestate.BARRIER:
          break
        p = self.safe_getchar(*starboard(row,col))
        n = self.safe_getchar(*port(row,col))
  
        if p == Puzzlestate.BARRIER and n == Puzzlestate.BARRIER:
          coldspots.append(i)
  
        row += row_increment
        col += col_increment
        i += 1
      helpful_clue_dict[clue]['coldspots'] = coldspots
  
    return helpful_clue_dict

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

  def score_word(self,words_to_try,direction,cluenumber,safe=True):

    if safe:
      if self.test_word(words_to_try,direction,cluenumber):
        pass
      else:
        return None

    row_increment,col_increment = Puzzlestate.directions[direction]
    assert direction in ('Across','Down'), \
      f'what kind of direction is {direction}'
    if direction == 'Across':
      port = lambda row,col: [ row, col+1 ]
      starboard = lambda row,col: [ row, col-1 ]
    else:
      port = lambda row,col: [ row+1, col ]
      starboard = lambda row,col: [ row-1, col ]

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
    for i,tryword in enumerate(words_to_try):
      letter_to_starboard = self.safe_getchar(*starboard(row,col))
      letter_to_port = self.safe_getchar(*port(row,col))
#gotta fix this region
      if ( (letter_to_port == Puzzlestate.BARRIER and letter_to_starboard == Puzzlestate.BARRIER) or
           (letter_to_starboard == Puzzlestate.UNSOLVED and letter_to_starboard == Puzzlestate.UNSOLVED) ):
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
    i = 0
    for c in word:
      self.setchar(row,col,c)
      for clue in self.data['clues_that_touch_cell']:
        self.clues_expanded[clue]['constraints'].add([i,c])
      row += row_increment
      col += col_increment
      i += 1

    logging.info(f"inscribed {word} into {cluenumber} {direction}")

    # update the constraints in clues_expanded



    self.addwordused(word)
    return self

  def is_puzzle_solved(self):
    height = self.height()
    width = self.width()
    assert len(self.data['puzzle']) == height, \
      "height of puzzle doesn't match stored height"
    assert len(self.data['solution']) == height, \
      "height of solution doesn't match stored height"
    for i, row in enumerate(self.data['puzzle']):
      assert len(row) == width, \
        f"row {i} of puzzle doesn't match width"
      assert len(self.data['solution']) == width, \
        f"row {i} of solution doesn't match width"
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
    listify = lambda x: list(x)
    return json.dumps(self.data,default=listify)

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
    assert size > 0, "puzzle is size zero?"
    return black_squares / size

  def _safe_getcellcontents(self, rowno, colno):
    if (rowno < 0 or rowno >= self.height() or
        colno < 0 or colno >= self.width()) :
      return Puzzlestate.BARRIER
    else:
      return self.data['puzzle'][rowno][colno]


  def upsert_clue_text(self,cluenumber,direction,text=''):
    if direction not in Puzzlestate.directions:
      raise RuntimeError(f"{direction} is not a direction")
    if len(text) == 0:
      text = 'Lorem ipsum'
    if 'clues' not in self.data:
      self.data['clues'] = dict()
    if direction not in self.data['clues']:
      self.data['clues'][direction] = list()
    self.data['clues'][direction].append([cluenumber,text])


  def insert_clue_numbers(self):
    cluenumber = 1
    for rowno,row in enumerate(self.data["puzzle"]):
      for colno,col in enumerate(row):
        if (c := self._safe_getcellcontents(rowno,colno)) == Puzzlestate.BARRIER:
          continue
        if isinstance(c,int):
          raise RuntimeError(f'hey, I found cell R{rowno}C{colno} already occupied by a clue number')
        starts_an_across = (self._safe_getcellcontents(rowno-1,colno) == Puzzlestate.BARRIER 
                            and
                            self._safe_getcellcontents(rowno+1,colno) != Puzzlestate.BARRIER)
        starts_a_down = (self._safe_getcellcontents(rowno,colno-1) == Puzzlestate.BARRIER 
                         and
                         self._safe_getcellcontents(rowno,colno+1) != Puzzlestate.BARRIER)
        if starts_an_across or starts_a_down:
          self.setint(rowno,colno,cluenumber)
        if starts_an_across:
          self.upsert_clue_text(cluenumber,'Across')
        elif starts_a_down:
          self.upsert_clue_text(cluenumber,'Down')
        if starts_an_across or starts_a_down:
          cluenumber += 1
    return self
        
def main():
  """for testing"""
  if len(sys.argv) == 1:
    sourcefile = "samplepuzzles/baby-animals-crossword.ipuz"
  else:
    sourcefile = sys.argv[1]
  puzzle = Puzzlestate.fromjsonfile(sourcefile)
  print (f"source file is {sourcefile}")
  print (f"sparseness is {puzzle.sparseness()}")

  puzzle.writesvg(f"{sourcefile}.svg",
                  showtitle=True,
                  showsolvedcells=True,
                  highlight_cells=[ [ [4,7],  'Down',   6],
                                    [ [11,9], 'Across', 3] ] )
  puzzle.writejson(f"{sourcefile}.out.ipuz")

if __name__ == '__main__':
  random.seed()
  main()
