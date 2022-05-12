#!/usr/bin/env python3

import random
import time
import json
import copy
import sys
import os
import re
import sqlite3


class Randomword:

  WORDDB="/Users/brice/generate-crossword/words.db"
  con = None

  categories = {}

  def __init__(self,seed=0):
    if seed == 0:
      random.seed(int(time.time()))
    else:
      random.seed(seed)
    self.con = sqlite3.connect('file:' + Randomword.WORDDB + '?mode=ro', uri=True)

  def randomwords(self, desired_length, constraints, category):

    if not isinstance(category, int):
      raise RuntimeError(f'category {category} is sposta be an int')
  
    pattern = list('_' * desired_length)
    if constraints:
      for constraint in constraints:
        n,c = constraint
        pattern[n] = c
    
    pattern = ''.join(pattern)
    cur = self.con.cursor()
    matchingwords = cur.execute("select word from words where word like '" + pattern + "';").fetchall()

    return matchingwords

# end of class methods

def main():

  emptyset = set()
  emptylist = list()

  wordspitter = Randomword(0)
  words = wordspitter.randomwords(3,emptylist,1)
  print("random 3 letter word is ")
  print(words)
  
  wordspitter = Randomword(0)
  constraintlist = [ [ 1, 'I' ] , [ 2, 'X'] ]
  words = wordspitter.randomwords(3,constraintlist,1)
  print("random 3 letter word is ")
  print(words)
  
#  words = wordspitter.randomwords(5,emptylist,1)
#  print("random 5 letter word is ")
#  print(words)
  
#  already_used = set()
#  already_used.add('PUPPY')
#  words = wordspitter.randomwords(5,emptylist,1)
#  print("random 5 letter word is ")
#  print(words)
  
if __name__ == '__main__':
    main()

