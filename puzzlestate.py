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
import svgwrite
from itertools import permutations
from dataclasses import dataclass
from typing import Dict

confdir = os.path.join(os.path.dirname(os.path.realpath(__file__)),"conf")
if not os.path.exists(confdir):
  raise RuntimeError(f'no conf directory at {confdir}')
if not os.path.isdir(confdir):
  raise RuntimeError(f'{confdir} is supposed to be a directory')
conffile = os.path.join(confdir,"crossword.json")
if not os.path.exists(conffile):
  raise RuntimeError(f'missing config file')


class Puzzlegeometry:
  # Directions are defined as [rowincrement,colincrement]
  directions = {
    'Across': [0,1],
    'Down': [1,0]
  }

def _otherdirection(d):
  assert isinstance(d,str), f"{d} must be a string but is {type(d)}"
  assert (d == 'Across') or (d == 'Down'), f"only valid directions are Across and Down, not {d}"
  if d == 'Across':
    return 'Down'
  return 'Across'

@dataclass(frozen=True,order=True)
class Puzzleitem:
  itemnumber: int
  direction: str
  def fromlist(aslist):
    return Puzzleitem(itemnumber=int(aslist[0]),direction=str(aslist[1]))
  def fromstr(asstr):
    i,d = asstr.split()
    return Puzzleitem(itemnumber=int(i),direction=str(d))
  def __post_init__(self):
    if self.direction not in Puzzlegeometry.directions:
      raise ValueError(f'{self.direction} is not a valid direction')
    if not isinstance(self.itemnumber,int) or (self.itemnumber < 0):
      raise ValueError(f'{self.itemnumber} is not a valid itemnumber')
  def __repr__(self):
    return f'{self.itemnumber} {self.direction}'

class Puzzlestate:
  """
  operations on a crossword puzzle state
  """
  UNSET = '.'
  BARRIER = '#'
  COLDSPOT = '~'

  with open(conffile,'r') as f:
    config = json.load(f)
  worddb = config['worddb']

  def _slurpjson(fn: str):
    result = dict()
    try:
      if not os.path.isabs(fn):
        fn = os.path.join(confdir,fn)
      with open(fn,encoding='utf-8') as f:
        result = json.load(f)
    except OSError:
      raise RuntimeError(f'Could not read json from {fn}')
    return result

  i_like_vowels = _slurpjson('vowel_friendly_weightings.json')
  i_like_cons = _slurpjson('consonant_friendly_weightings.json')
  i_like_finals = _slurpjson('final_friendly_weightings.json')
  letterpairfreqs = _slurpjson('letter_pair_freqs.json')
  singleletterfreqs = _slurpjson('single_letter_weightings.json')

  def __init__(self,data):
    self.data = data

  @classmethod
  def blank(cls,height:int,width:int, title='Untitled'):
    if int(width) <= 0 or int(height) <= 0:
      return None
    return cls( {"dimensions": {"height": int(height),
                                "width": int(width)},
                 "wordsused": set(),
                 "puzzle":
                  [[Puzzlestate.UNSET for col in range(width)]
                    for row in range(height)] ,
                 "solution":
                  [[Puzzlestate.UNSET for col in range(width)]
                    for row in range(height)] })


  @classmethod
  def fromjsonfile(cls,filename):
    def _barrier_or_unset(target,row,col):
      '''
      can be called on 'puzzle' or 'solution'
      the advantage if used on 'puzzle' is that it doesn't treat the first
      cell of an answer as special (just because it has a number in it)
      '''
      if data[target][row][col] == Puzzlestate.BARRIER:
        return Puzzlestate.BARRIER
      return Puzzlestate.UNSET

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

    for d in Puzzlegeometry.directions:
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
          if (isinstance(data['puzzle'][row][col],int) or
              (isinstance(data['puzzle'][row][col],str) and 
               data['puzzle'][row][col].isdigit())):
            # solution shouldn't have item numbers in the first cell of answers
            data['solution'][row][col] = Puzzlestate.UNSET

    if 'answerlocations' not in data:
      data['answerlocations'] = {}
    if 'answerlengths' not in data:
      data['answerlengths'] = {}
    if 'items_expanded' not in data:
      data['items_expanded'] = {}

    if 'completed_items' not in data:
      data['completed_items'] = list()
    if 'incomplete_items' not in data:
      data['incomplete_items'] = list(data['items_expanded'].keys())
  
    # populate data['answerlocations']; make sure any filled cells are uppercase
    # note that we store item locations by integer not by the dataclass Puzzleitem
    # because 10 Down is the same location as 10 Across

    for row in range(height):
      for col in range(width):
        # first, let's determine whether what's here is an item number,
        # and make sure it is an integer if it is
        thisitemno = data['puzzle'][row][col]
        if (isinstance(thisitemno,int) or
            isinstance(thisitemno,str) and thisitemno.isdigit()):
          data['puzzle'][row][col] = int(thisitemno)
          thisitemno = data['puzzle'][row][col]
          if thisitemno < 0:
            raise RuntimeError(f'whoa, item numbers must be positive, unlike [{row},{col}], which is {thisitemno}')
          elif thisitemno == 0:
            # it's an empty cell
            data['puzzle'][row][col] = Puzzlestate.UNSET
          else:
            # it's the start of a puzzle item, and we need to grab its number
            data['answerlocations'][thisitemno] = [row,col]
            data['puzzle'][row][col] = Puzzlestate.UNSET
        elif isinstance(thisitemno,str): data['puzzle'][row][col] = data['puzzle'][row][col].upper()
        elif isinstance(thisitemno, dict):
          raise RuntimeError("I don't know how to deal with fancy cells yet")
        else:
          raise RuntimeError(f"weird cell content: [{row},{col}] is {thisitemno}, type {type(cellcontents)}")

    # now squirrel away the length of the answer for each item,
    # as well as, for each [row,col] all the items that touch that space

    data['items_that_touch_cell'] = [[ list() for i in range(width)]
                                                      for j in range(height)]

    for direction in data['clues']:
      if direction not in Puzzlegeometry.directions:
        raise RuntimeError(f"{direction} is not a direction")
      for numberpluscluetext in data['clues'][direction]:
        itemnumber = int(numberpluscluetext[0])
        row,col = data['answerlocations'][itemnumber]
        assert data['puzzle'][row][col] == Puzzlestate.UNSET, \
          f"at ({row},{col}): expected {Puzzlestate.UNSET}, saw {data['puzzle'][row][col]}"

        # now we count the number of blanks from the start of the item,
        # in the given direction, to the next BARRIER or boundary

        thisitem = Puzzleitem(itemnumber=itemnumber, direction=direction)
        n = 0
        while True:
          data['items_that_touch_cell'][row][col].append( (thisitem, n) )
          row += Puzzlegeometry.directions[direction][0]
          col += Puzzlegeometry.directions[direction][1]
          if (col == width or row == height or
              data['puzzle'][row][col] == Puzzlestate.BARRIER):
            break
          n += 1

        data['answerlengths'][thisitem] = n+1
        data['incomplete_items'].append(thisitem)

    # now let's start to populate items_expanded
    # sample dict item:
    # '1 Down': 
    #  { cluetext: 'Launches', 
    #    wordlength: 5, 
    #    location: [row,col]
    #  }

    for d in data['clues']:
      for numberpluscluetext in data['clues'][d]:
        cno = int(numberpluscluetext[0])
        cluetext = numberpluscluetext[1]
        myitem = Puzzleitem(itemnumber=cno,direction=d)
        data['items_expanded'][myitem] = {
          'cluetext': cluetext,
          'wordlength': data['answerlengths'][myitem],
          'location': data['answerlocations'][cno],             # [row,col]
        }

    # we have, for each cell in any item, the 1 or 2 items that touch that cell
    # let's transpose that into, for each item, a DICT of tuples 
    # {                             
    #  another_item_that_touches_this_item:     Puzzleitem
    #     (charcount_in_this_item,              counting from 0
    #      charcount_in_other_item))            counting from 0
    # }

    for direction in data['clues']:
      for itempluscluetext in data['clues'][direction]:
        itemnumber = int(itempluscluetext[0])
        row,col = data['answerlocations'][itemnumber]
        thisitem = Puzzleitem(itemnumber=itemnumber, direction=direction)
        n = 0
        intersectors = dict()
        while True:
          if (intersectorlist := data['items_that_touch_cell'][row][col]):
            for i,n2 in intersectorlist:
              if i != thisitem:
                intersectors[i] = (n,n2)
          row += Puzzlegeometry.directions[direction][0]
          col += Puzzlegeometry.directions[direction][1]
          if (col == width or row == height or
              data['puzzle'][row][col] == Puzzlestate.BARRIER):
            break
          n += 1
        data['items_expanded'][thisitem]['intersectors'] = intersectors

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
      return Puzzlestate.UNSET
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
    if isinstance(c2,int) or (isinstance(c2,str) and c2.isdigit()):
      return True # It's an item number
    if isinstance(c2,str) and c2 == Puzzlestate.UNSET:
      return True # Yay!  It's not been filled in yet
    if isinstance(c2,str) and c2.upper() == c.upper():
      return True # Yay! It's already the character we want.
    return False # D'oh! The space is already in use with a different letter

  def setbarrier(self,rowno,colno):
    self.data['puzzle'][rowno][colno] = Puzzlestate.BARRIER

  def clearbarrier(self,rowno,colno):
    self.data['puzzle'][rowno][colno] = Puzzlestate.UNSET

  def togglebarrier(self,rowno,colno):
    if self.data['puzzle'][rowno][colno] == Puzzlestate.UNSET:
      self.data['puzzle'][rowno][colno] = Puzzlestate.BARRIER
    else:
      self.data['puzzle'][rowno][colno] = Puzzlestate.UNSET

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

  def _listify(x):
    if isinstance(x,Puzzleitem):
      return [ x.itemnumber, x.direction ]
    else:
      return list(x)

  def writejson(self,filename):
    tempcopy = copy.deepcopy(self.data)
    tempcopy['wordsused'] = list(tempcopy['wordsused'])
    tempcopy['answerlengths'] = {f'{k.itemnumber} {k.direction}': tempcopy['answerlengths'][k] for k in tempcopy['answerlengths']}
    try:
      with open(filename, 'w', encoding='utf-8') as f:
        json.dump(self.data, f, indent=2, sort_keys=True, skipkeys=True, default=Puzzlestate._listify)
    # TODO: stringify Puzzleitem's so that they can be saved (and so we don't need skipkeys)
    except OSError:
      raise RuntimeError(f'Could not write json to {filename}') from None
    self.data['wordsused'] = set(self.data['wordsused'])
    return self

  def writejson(self,filename):
    self.data['wordsused'] = list(self.data['wordsused'])
    try:
      with open(filename, 'w', encoding='utf-8') as f:
        json.dump(self.data, f, indent=2, sort_keys=True, skipkeys=True, default=Puzzlestate._listify)
    # TODO: stringify Puzzleitem's so that they can be saved (and so we don't need skipkeys)
    except OSError:
      raise RuntimeError(f'Could not write json to {filename}') from None
    self.data['wordsused'] = set(self.data['wordsused'])
    return self

  def writesvg(self,filename,**kwargs):
    assert 'showcluenumbers' not in kwargs or isinstance(kwargs['showcluenumbers'],bool), \
        'showcluenumbers arg must be True or False'

    assert 'showsolvedcells' not in kwargs or isinstance(kwargs['showsolvedcells'],bool), \
        'showsolvedcells arg must be True or False'

    assert 'showtitle' not in kwargs or isinstance(kwargs['showtitle'],bool), \
        'showsolvedcells arg must be True or False'

    assert 'highlight_cells' not in kwargs or isinstance(kwargs['highlight_cells'],list), \
        'highlight_cells value must be a list of [startingcell,direction,count]'

    assert 'text_below_puzzle' not in kwargs or isinstance(kwargs['text_below_puzzle'],str), \
        'text_below_puzzle arg must be a str'

    title = self.gettitle()
    if title is None or title == '':
      title = 'Untitled Crossword Puzzle'

    if 'title' in kwargs:
      if isinstance(kwargs['title'], str):
        title = kwargs['title']
      else:
        raise RuntimeError('titles need to be strings')

    _w = self.width()
    _h = self.height()
    if 'showtitle' not in kwargs or not kwargs['showtitle']:
      Puzzlestate.config['title_height_mm'] = 0

    Puzzlestate.config['top_margin_mm'] = Puzzlestate.config['cellsize_mm'] + Puzzlestate.config['title_height_mm']
    Puzzlestate.config['bottom_margin_mm'] = Puzzlestate.config['cellsize_mm']
    Puzzlestate.config['side_margin_mm'] = Puzzlestate.config['cellsize_mm']

    Puzzlestate.config['width_mm'] = Puzzlestate.config['cellsize_mm']*_w + 2*Puzzlestate.config['side_margin_mm']
    Puzzlestate.config['height_mm'] = (Puzzlestate.config['cellsize_mm']*_h +
                       Puzzlestate.config['top_margin_mm'] +
                       Puzzlestate.config['bottom_margin_mm'])

    drawing = svgwrite.Drawing(filename,
              size=(f"{Puzzlestate.config['width_mm']}mm",f"{Puzzlestate.config['height_mm']}mm"))
    drawing.viewbox(0, 0, Puzzlestate.config['height_mm'], Puzzlestate.config['width_mm'])

    # draw interior horizontal lines
    for i in range(1,_h):
      y = Puzzlestate.config['top_margin_mm'] + i * Puzzlestate.config['cellsize_mm']
      drawing.add(drawing.line(
                          start=(Puzzlestate.config['side_margin_mm'], y),
                          end=(Puzzlestate.config['cellsize_mm']*_w+Puzzlestate.config['side_margin_mm'], y),
                          stroke=Puzzlestate.config['line_color'],stroke_width=Puzzlestate.config['line_width']))

    # draw top and bottom lines
    drawing.add(drawing.line(
                        start=(Puzzlestate.config['side_margin_mm'], Puzzlestate.config['top_margin_mm']+_h*Puzzlestate.config['cellsize_mm']),
                        end=(Puzzlestate.config['cellsize_mm']*_w+Puzzlestate.config['side_margin_mm'], Puzzlestate.config['top_margin_mm']+_h*Puzzlestate.config['cellsize_mm']),
                        stroke=Puzzlestate.config['line_color'],stroke_width=Puzzlestate.config['line_width'], style=Puzzlestate.config['outer_line_style']))

    drawing.add(drawing.line(
                        start=(Puzzlestate.config['side_margin_mm'], Puzzlestate.config['top_margin_mm']),
                        end=(Puzzlestate.config['cellsize_mm']*_w+Puzzlestate.config['side_margin_mm'], Puzzlestate.config['top_margin_mm']),
                        stroke=Puzzlestate.config['line_color'],stroke_width=Puzzlestate.config['line_width'], style=Puzzlestate.config['outer_line_style']))

    # draw vertical lines
    for i in range(1,_w):
      x = Puzzlestate.config['side_margin_mm'] + i * Puzzlestate.config['cellsize_mm']
      drawing.add(drawing.line(
                          start=(x,Puzzlestate.config['top_margin_mm']),
                          end=(x,Puzzlestate.config['cellsize_mm']*_h+Puzzlestate.config['top_margin_mm']),

                          stroke=Puzzlestate.config['line_color'],stroke_width=Puzzlestate.config['line_width']))

    drawing.add(drawing.line(
                        start=(Puzzlestate.config['side_margin_mm'],Puzzlestate.config['top_margin_mm']),
                        end=(Puzzlestate.config['side_margin_mm'], Puzzlestate.config['cellsize_mm']*_h+Puzzlestate.config['top_margin_mm']),
                        stroke=Puzzlestate.config['line_color'],stroke_width=1,style=Puzzlestate.config['outer_line_style']))
    drawing.add(drawing.line(
                        start=(Puzzlestate.config['cellsize_mm']*_w+Puzzlestate.config['side_margin_mm'],Puzzlestate.config['top_margin_mm']),
                        end=(Puzzlestate.config['cellsize_mm']*_w+Puzzlestate.config['side_margin_mm'], Puzzlestate.config['cellsize_mm']*_h + Puzzlestate.config['top_margin_mm']),
                        stroke=Puzzlestate.config['line_color'],stroke_width=Puzzlestate.config['line_width'],style=Puzzlestate.config['outer_line_style']))


    # insert black boxes
    for row in range(_h):
      for col in range(_w):
        if self.getchar(row,col) == Puzzlestate.BARRIER:
          drawing.add(drawing.rect(
                           insert=(
                                   col*Puzzlestate.config['cellsize_mm']+Puzzlestate.config['side_margin_mm'],
                                   row*Puzzlestate.config['cellsize_mm']+Puzzlestate.config['top_margin_mm']
                                  ),
                           size=(Puzzlestate.config['cellsize_mm'],Puzzlestate.config['cellsize_mm']),
                           fill=Puzzlestate.config['block_color']))

    # insert highlights

    if 'highlight_cells' in kwargs:
      for rc, direction, cellcount in kwargs['highlight_cells']:
        row,col = rc
        row_increment, col_increment = Puzzlegeometry.directions[direction]

        i = 0
        while i < cellcount:
          drawing.add(drawing.rect(
                           insert=(
                                   col*Puzzlestate.config['cellsize_mm']+Puzzlestate.config['side_margin_mm'],
                                   row*Puzzlestate.config['cellsize_mm']+Puzzlestate.config['top_margin_mm']
                                  ),
                           size=(Puzzlestate.config['cellsize_mm'],Puzzlestate.config['cellsize_mm']),
                           fill=Puzzlestate.config['highlight_color']))
          row += row_increment
          col += col_increment
          i += 1

    if 'showcluenumbers' in kwargs and kwargs['showcluenumbers']:
      g = drawing.g(class_='cluenumber',style = Puzzlestate.config['cluenumber_style'])
      for answer in self.data['answerlocations'].keys():
        row,col = self.data['answerlocations'][answer]

        g.add(drawing.text(answer,
                    insert=(
                            col*Puzzlestate.config['cellsize_mm']+Puzzlestate.config['side_margin_mm']+Puzzlestate.config['offset_cluenum_x'],
                            row*Puzzlestate.config['cellsize_mm']+Puzzlestate.config['top_margin_mm']+Puzzlestate.config['offset_cluenum_y'],
                           )))
      drawing.add(g)

    if 'showsolvedcells' in kwargs and kwargs['showsolvedcells']:
      g = drawing.g(class_='solvedcell', style = Puzzlestate.config['solution_style'])
      for row in range(_h):
        for col in range(_w):
          c = self.getchar(row,col)
          if isinstance(c,str) and c.isalpha():
            g.add(drawing.text(c,
                    insert=(
                            col*Puzzlestate.config['cellsize_mm']+Puzzlestate.config['side_margin_mm']+Puzzlestate.config['offset_solution_x'],
                            row*Puzzlestate.config['cellsize_mm']+Puzzlestate.config['top_margin_mm']+Puzzlestate.config['offset_solution_y'],
                           )))
      drawing.add(g)

    if 'showtitle' in kwargs and kwargs['showtitle']:
      if title is None or title == '':
        mytitle = self.gettitle()
      else:
        mytitle = title
      g = drawing.g(class_='title', style = Puzzlestate.config['title_style'])
      g.add(drawing.text(title,
                    insert=(
                            Puzzlestate.config['side_margin_mm'],
                            Puzzlestate.config['title_height_mm']
                           )))
      drawing.add(g)


    drawing.save()

  def answerlength(item):
    return self.data['answerlengths'][item]

  def intersecting_items(self, itemnumber, direction):
    return self.data[Puzzleitem(itemnumber=itemnumber,
                                direction=direction)]['intersecting_items']


  def incomplete_items(self):
    '''
    return a dict of items to be solved
    { 'item' : str : 
      'wordlength' : int,
      'constraints' : [ [ index, whichchar ], ... ],
      'coldspots' : [ index, ... ]
    }
    '''
    assert 'incomplete_items' in self.data, 'missing incomplete_items element'
    assert 'completed_items' in self.data, 'missing completed_items element'

    if len(self.data['incomplete_items']) == 0:
      # wow, nothing left to do!
      return None


    incomplete_item_list = self.data['incomplete_items']
    
    helpful_item_dict = {}

    for item in incomplete_item_list:
      row_increment, col_increment = Puzzlegeometry.directions[item.direction]

      helpful_item_dict[item] = {}
      # now we gather the constraints, i.e., letters already filled in

      if 'constraints' in self.data['items_expanded'][item]:
        helpful_item_dict[item]['constraints'] = self.data['items_expanded'][item]['constraints']
      else:
        helpful_item_dict[item]['constraints'] = []
      helpful_item_dict[item]['wordlength'] = self.data['answerlengths'][item]

      # and now we gather coldspots, in other words, places in this word that
      # make a downward search path from filling in this item non-unique.
      #    ? ? B ?
      #    ? ? O ?
      #    # # A #
      #    ? ? T ?
      # BOOT would lead to the same searchspace as BOAT does if the third 
      # character doesn't matter
  
      coldspots = []
      row,col = self.data['answerlocations'][item.itemnumber]
      if col >= self.width() or row >= self.height():
        raise RuntimeError(f'answer location for {item.itemnumber} {item.direction} is corrupt')
      if item.direction == 'Across':
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
      helpful_item_dict[item]['coldspots'] = coldspots
  
    return helpful_item_dict

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

  def test_word(self,word,direction,itemnumber):

    row_increment,col_increment = Puzzlegeometry.directions[direction]

    row,col = self.data['answerlocations'][itemnumber]
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

  def score_word(self,word_to_try,direction,itemnumber,safe=True):

    return 1
    if safe:
      if self.test_word(word_to_try,direction,itemnumber):
        pass
      else:
        raise RuntimeError(f'{word_to_try} was supposed to fit in {itemnumber} {direction}')

    row_increment,col_increment = Puzzlestate.directions[direction]
    assert direction in ('Across','Down'), \
      f'what kind of direction is {direction}'
    if direction == 'Across':
      port = lambda row,col: [ row, col+1 ]
      starboard = lambda row,col: [ row, col-1 ]
    else:
      port = lambda row,col: [ row+1, col ]
      starboard = lambda row,col: [ row-1, col ]

    row,col = self.data['answerlocations'][itemnumber]

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
    for i,tryword in enumerate(word_to_try):
      letter_to_starboard = self.safe_getchar(*starboard(row,col))
      letter_to_port = self.safe_getchar(*port(row,col))
#gotta fix this region
      if ( (letter_to_port == Puzzlestate.BARRIER and letter_to_starboard == Puzzlestate.BARRIER) or
           (letter_to_starboard == Puzzlestate.UNSET and letter_to_starboard == Puzzlestate.UNSET) ):
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

  def inscribe_word_in_solution(self,item,word):
    """
    returns object containing the word if it was able to inscribe it,
    else returns none
    """
    direction = item.direction
    itemnumber = item.itemnumber

    row_increment,col_increment = Puzzlegeometry.directions[direction]

    row,col = self.data['answerlocations'][itemnumber]
    i = 0
    for c in word:
      self.data['solution'][row][col] = c
      row += row_increment
      col += col_increment
      i += 1

    logging.info(f"inscribed {word} into {itemnumber} {direction}")

    # update the constraints in items_expanded



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

  def populate_solution_from_changelist(self,changelist):
    for c in changelist:
      self.inscribe_word_in_solution(c[0],c[1])
      
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

  def getintersectors(self,item) -> Dict:
    if 'intersectors' not in self.data['items_expanded'][item]:
      return None
    return self.data['items_expanded'][item]['intersectors']

  def getlength(self,item) -> int:
    return self.data['answerlengths'][item]

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


  def upsert_item_text(self,itemnumber,direction,text=''):
    if direction not in Puzzlegeometry.directions:
      raise RuntimeError(f"{direction} is not a direction")
    if len(text) == 0:
      text = 'Lorem ipsum'
    if 'clues' not in self.data:
      self.data['clues'] = dict()
    if direction not in self.data['clues']:
      self.data['clues'][direction] = list()
    self.data['clues'][direction].append([itemnumber,text])


  def insert_item_numbers(self):
    itemnumber = 1
    for rowno,row in enumerate(self.data["puzzle"]):
      for colno,col in enumerate(row):
        if (c := self._safe_getcellcontents(rowno,colno)) == Puzzlestate.BARRIER:
          continue
        if isinstance(c,int):
          raise RuntimeError(f'hey, I found cell R{rowno}C{colno} already occupied by an item number')
        starts_an_across = (self._safe_getcellcontents(rowno-1,colno) == Puzzlestate.BARRIER 
                            and
                            self._safe_getcellcontents(rowno+1,colno) != Puzzlestate.BARRIER)
        starts_a_down = (self._safe_getcellcontents(rowno,colno-1) == Puzzlestate.BARRIER 
                         and
                         self._safe_getcellcontents(rowno,colno+1) != Puzzlestate.BARRIER)
        if starts_an_across or starts_a_down:
          self.setint(rowno,colno,itemnumber)
        if starts_an_across:
          self.upsert_item_text(itemnumber,'Across')
        elif starts_a_down:
          self.upsert_item_text(itemnumber,'Down')
        if starts_an_across or starts_a_down:
          itemnumber += 1
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
