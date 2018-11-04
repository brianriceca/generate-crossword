#!/usr/local/bin/python3

def solve(puzzlestate, wordlist):

    if not wordlist:
      return True
    for i, tryword in enumerate(wordlist):
      rest_of_wordlist = [wordlist[x] for x in range(len(wordlist)) if x != i ]
      for tryloc in possible_word_starts(puzzlestate,tryword):
        if legal_word(puzzlestate,tryword,tryloc):
          puzzlestate2 = copy(puzzlestate)
          inscribe_word(puzzlestate2,tryword,tryloc)
          if solve(puzzlestate2,rest_of_wordlist):
            return True
    return False

