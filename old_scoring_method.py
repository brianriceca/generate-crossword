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

