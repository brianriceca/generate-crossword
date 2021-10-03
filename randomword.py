#!/usr/bin/env python3

import random
import time
import json
import copy
import sys
import os


class Randomword:

  WORDLISTDIR="/Users/brice/generate-crossword/wordstotry/"

  def __init__(self,seed=0):
    if seed == 0:
      random.seed(int(time.time()))
    else:
      random.seed(seed)
    self.words_of_length_n = [list() for _ in range(20)]

    for fname in os.listdir(Randomword.WORDLISTDIR):
      with open(os.path.join(Randomword.WORDLISTDIR, fname), 'r') as f:
        while True:
          line = f.readline().strip()
          if not line:
            break
          self.words_of_length_n[len(line)].append(line)
      f.close()


  def randomwords(self, desired_length, constraints, ababness):

    candidates =  [ x for x in self.words_of_length_n[desired_length] ]

    if constraints:
      matching_words = list()
      for constraint in constraints:
        n,c = constraint
        for candidate in candidates:
          if candidate[n] != c:
            continue
          matching_words.append(candidate)
      return matching_words
    else:
      return candidates

def main():

  emptyset = set()
  emptylist = list()

  wordspitter = Randomword(0)
  words = wordspitter.randomwords(3,emptyset,emptylist,1.0)
  print("random 3 letter word is ")
  print(words)
  
  wordspitter = Randomword(0)
  constraintlist = [ [ 1, 'I' ] ]
  words = wordspitter.randomwords(3,emptyset,constraintlist,1.0)
  print("random 3 letter word is ")
  print(words)
  
  wordspitter = Randomword(0)
  words = wordspitter.randomwords(5,emptyset,emptylist,1.0)
  print("random 5 letter word is ")
  print(words)
  
  wordspitter = Randomword(0)
  already_used = set()
  already_used.add('PUPPY')
  words = wordspitter.randomwords(5,already_used,emptylist,1.0)
  print("random 5 letter word is ")
  print(words)
  
if __name__ == '__main__':
    main()

