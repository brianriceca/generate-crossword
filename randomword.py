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


  def randomword(self,desired_length,desired_ababness=1.0):
    return self.words_of_length_n[desired_length][random.randint(0,len(self.words_of_length_n[desired_length]))-1]
    pass

def main():
  wordspitter = Randomword(0)
  print("random 3 letter word is {}".format(wordspitter.randomword(3)))
  print("random 5 letter word is {}".format(wordspitter.randomword(5)))

if __name__ == '__main__':
    main()

