#!/usr/bin/env python3

import PySimpleGUI as sg                        
import os
import sys
import re

base64_white_png = b'iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAIAAABuYg/PAAAACXBIWXMAAC4jAAAuIwF4pT92AAAAKklEQVRIx+3NQQEAAAQEMPTvfFLw2gqsk9SXqUcymUwmk8lkMplMJpPdWgH+A0WvPF3RAAAAAElFTkSuQmCC'
base64_black_png = b'iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAIAAABuYg/PAAAACXBIWXMAAC4jAAAuIwF4pT92AAAAG0lEQVRIx+3BMQEAAADCoPVPbQdvoAAAAIDHAA9UAAHDxkIGAAAAAElFTkSuQmCC'

from puzzlestate import Puzzlestate

def main():
  """create a crossword puzzle bracket interactively"""
  if len(sys.argv) != 4:
    print(f"usage: {sys.argv[0]} nrows ncols outfilename")
    sys.exit(1)
  
  height = int(sys.argv[1])
  width = int(sys.argv[2])
  outfilename = sys.argv[3]
  
  print(f'{height} rows of {width} columns each')
  puzzle = Puzzlestate.blank(height,width)

#  sg.theme('DarkGreen')
  layout = [  [sg.Text(f"Draw a {height} x {width} crossword puzzle", key='-TITLE-')],
              [sg.Text('', size=(80,1), key='-FEEDBACK-')],
              [ [sg.Button(image_data=base64_white_png, key=f'-{rowno},{colno}-', metadata=False) for colno in range(width) ] for rowno in range(height) ],

              [sg.Button('Save'),sg.Button('Quit')] ]
  
  window = sg.Window('Draw a crossword puzzle', layout, resizable=True,
               margins=(50, 50), return_keyboard_events=True, use_default_focus=False)
  
  while True:
    event, values = window.Read()
    if (event == sg.WIN_CLOSED or event is None or
      event == 'Quit' or event.startswith('q')):
      sys.exit(0)
    if event == 'Save':
      puzzle.insert_clue_numbers().writejson(outfilename)
    if bool(re.search(r'^-\d+,\d+-$',cell_row_col := event)):
      youhit = [int(x) for x in re.split(r'[-,]', cell_row_col) if x]
      print(f'You hit row {youhit[0]} column {youhit[1]}')
      puzzle.togglebarrier(youhit[0],youhit[1])
      window[cell_row_col].metadata = not window[cell_row_col].metadata
      window[cell_row_col].update(image_data=base64_black_png if window[cell_row_col].metadata else base64_white_png)


if __name__ == '__main__':
  main()
