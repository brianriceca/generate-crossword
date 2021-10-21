#!/usr/bin/env python3

import random
import time
import json
import copy
import sys
import os
import re


class Randomword:

  WORDLISTDIR="/Users/brice/generate-crossword/wordstotry/"

  categories = {}

  def __init__(self,seed=0):
    if seed == 0:
      random.seed(int(time.time()))
    else:
      random.seed(seed)
    self.words = dict()

    filenamepattern = re.compile(r"^(.*)-")

    for fname in os.listdir(Randomword.WORDLISTDIR):
      if fname.endswith('-category.txt'):
        m = filenamepattern.match(fname)
        if m:
          category = m.group(1)
          if category not in self.words:
            self.words[category] = list()
          with open(os.path.join(Randomword.WORDLISTDIR, fname), 'r', encoding="latin-1") as f:
            while True:
              line = f.readline().strip()
              if not line:
                break
              self.words[category].append(line)
        f.close()


  def randomwords(self, desired_length, constraints, ababness, category):

    if category not in self.words:
      sys.exit('unknown category {}'.category)
  
    pattern = list('.' * desired_length)
    if constraints:
      for constraint in constraints:
        n,c = constraint
        pattern[n] = c
    
    pattern = ''.join(pattern)
    r = re.compile('^' + pattern + '$')
    print(pattern)
      
    filtered_result = [ x for x in self.words[category] if r.match(x) ]
    if filtered_result is None:
      return None
    random.shuffle(filtered_result)
    print('-----------------------')
    return filtered_result

# end of class methods

#def main():
#
#  emptyset = set()
#  emptylist = list()
#
#  wordspitter = Randomword(0)
#  words = wordspitter.randomwords(3,emptylist,1.0)
#  print("random 3 letter word is ")
#  print(words)
#  
#  wordspitter = Randomword(0)
#  constraintlist = [ [ 1, 'I' ] ]
#  words = wordspitter.randomwords(3,constraintlist,1.0)
#  print("random 3 letter word is ")
#  print(words)
#  
#  words = wordspitter.randomwords(5,emptylist,1.0)
#  print("random 5 letter word is ")
#  print(words)
#  
#  already_used = set()
#  already_used.add('PUPPY')
#  words = wordspitter.randomwords(5,emptylist,1.0)
#  print("random 5 letter word is ")
#  print(words)
#  
#if __name__ == '__main__':
#    main()
#
