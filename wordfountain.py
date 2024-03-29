#!/usr/bin/env python3

import random
import time
import json
import copy
import sys
import os
import re
import sqlite3
import os.path
import functools
from typing import List, Tuple

class Wordfountain:
  def __init__(self,worddb=None,seed=0):
    assert worddb is None or isinstance(worddb, str), \
      "wordfountain db filename must be a string"
    if worddb is None or worddb == '':
      worddb = os.environ.get('CROSSWORD_WORDDB')
    
#    if not os.path.isabs(worddb):
#      home = os.path.expanduser('~')
#      assert os.path.isdir(home), "you lack a homedir"
#      worddb = os.path.join(home,'.crossword', worddb)

    if seed == 0:
      random.seed(int(time.time()))
    else:
      random.seed(seed)

    self.con = sqlite3.connect('file://' + worddb + '?mode=ro', uri=True)
    self.con.row_factory = lambda cursor, row: row[0]

  def matchingwords(self, desired_length: int, constraints: List[Tuple]) -> List:
    query = 'SELECT word FROM words WHERE length = ' + str(desired_length)
    for c in constraints:
      query += ' AND c' + str(c[0]) + " = '" + str(c[1]) + "'"

    query += ';'

    cur = self.con.cursor()

    matches = cur.execute(query).fetchall()

    random.shuffle(matches)
    return matches

# end of class methods

def main():

  emptyset = set()
  emptylist = list()

  wf = Wordfountain(seed=0)

  words = wf.matchingwords(3,emptylist)
  print(words)
  
  constraintlist = [ [ 1, 'I' ] ]
  words = wf.matchingwords(3,constraintlist)
  print(words)
  
if __name__ == '__main__':
    main()

