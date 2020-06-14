#!/usr/bin/env python3

# p words_that_have_a_c_at_n[4][ord('m')-97]
# set(['xylem', 'ogham', 'ishim', 'unarm', 'strum', 'pilum', 'jorum', 'datum', 'linum', 'larum', 'zoism', 'inarm', 'sloom', 'sarum', 'tarim', 'aswim', 'islam', 'sagum', 'smarm', 'nahum', 'broom', 'cloam', 'buxom', 'bosom', 'durum', 'hakim', 'solum', 'unjam', 'axiom', 'oakum', 'orrum', 'plasm', 'rehem', 'skelm', 'assam', 'inkom', 'totem', 'bream', 'sodom', 'gloom', 'odism', 'gorum', 'harim', 'haram', 'genom', 'fanum', 'agram', 'abysm', 'fleam', 'steam', 'madam', 'menam', 'tharm', 'enorm', 'maxim', 'yealm', 'milam', 'ziram', 'begum', 'stumm', 'scrim', 'album', 'golem', 'sclim', 'begem', 'tuism', 'venom', 'aksum', 'herem', 'scram', 'agism', 'tatum', 'annam', 'epsom', 'cecum', 'chirm', 'adeem', 'hiram', 'gloam', 'stulm', 'purim', 'kelim', 'hokum', 'lynam', 'smalm', 'carom', 'inerm', 'apism', 'opium', 'forum', 'sedum', 'ihram', 'haulm', 'coram', 'bynum', 'vroom', 'ceram', 'foram', 'hakam', 'dwaum', 'fromm', 'denim', 'sebum', 'rheum', 'locum', 'bytom', 'thrum', 'whelm', 'kilim', 'wixom', 'dwalm', 'bedim', 'grimm', 'undam', 'odeum', 'kalam', 'gleam', 'degum', 'abohm', 'swarm', 'velum', 'jayem', 'storm', 'fayum', 'egham', 'harem', 'seism', 'yomim', 'abrim', 'deism', 'ledum', 'selim', 'priam', 'joram', 'novum', 'ungum', 'qualm', 'hyrum', 'jugum', 'prism', 'nizam', 'steem', 'ilium', 'occam', 'merom', 'kokum', 'radom', 'filum', 'adsum', 'psalm', 'garum', 'algum', 'yquem', 'imaum', 'sperm', 'abram', 'claim', 'dunam', 'notum', 'colum', 'aurum', 'satem', 'celom', 'retem', 'hilum', 'abeam', 'salem', 'chasm', 'oleum', 'cream', 'porum', 'realm', 'minim', 'vitim', 'besom', 'serum', 'idiom', 'panim', 'husum', 'oxfam', 'spasm', 'basom', 'upham', 'shawm', 'shalm', 'scrum', 'goyim', 'proem', 'charm', 'lebam', 'ileum', 'bloom', 'enzym', 'odium', 'rearm', 'spoom', 'shtum', 'choom', 'alarm', 'groom', 'pashm', 'khoum', 'praam', 'belem', 'onium', 'qeshm', 'modem', 'dream', 'miasm'])

import sys
import random
from puzzlestate import Puzzlestate

initialdirectionlist = [ ( (0,0), (1,0) ),
                  ( (0,0), (0,1) ),
                  ( (0,1), (1,0) ),
                  ( (1,0), (0,1) ),
                  ( (0,2), (1,0) ),
                  ( (2,0), (0,1) ),
                  ( (0,3), (1,0) ),
                  ( (3,0), (0,1) ),
                  ( (0,4), (1,0) ),
                  ( (4,0), (0,1) ) ]

def fill_in(p,locationlist):
  global words_that_have_a_c_at_n
  if locationlist is None:
    # hey, we filled in all the blanks!
    return p
  (startxy,dir) = locationlist[0]
  restoflist = locationlist[1:]
  (x,y) = startxy
  (dx,dy) = dir
  choice_set = set()
  for i in range(5):
    c = p.getchar(x,y)
    if c is None:
      # that means that this location is still unset, so it does not constrain our choices
      pass
    else:
      # OK, there is a character here
      if bool(choice_set):
        # our choice set has already been constrained, so let's constrain it further
        choice_set = choice_set.intersect(words_that_have_a_c_at_n[i][ord(c)-97])
      else:
        # our choice set has not yet been constrained, so let's set the initial group of choices
        choice_set = words_that_have_a_c_at_n[i][ord(c)-97]       
    x = x + dx
    y = y + dy

  # now we have our list of all the legal choices
  if len(choice_set)) == 0:
    return None
  
  # OK! At least once choice. Let's try each.

  choice_list = list(choice_set)
  random.shuffle(choice_list)

  for word in choice_list:
    newp = p.inscribe_word(word,startxy,dir)
    if newp is None:
      print("this shouldn't happen. word={}".format(word))
      p.print()
      sys.exit(4)
    result_p = fill_in(newp,restoflist): 
    if result_p is None:
      pass # OK, try the next word here instead
    else:
      return result_p


  

def main():
  global words_that_have_a_c_at_n
  print("hi")
  if len(sys.argv) != 2:
    print("usage: {} wordlistfile".format(sys.argv[0]))
    sys.exit(1)
  
  wordlistfile = sys.argv[1]  

  wordlist = list()
 
  file1 = open(wordlistfile, 'r') 
  count = 0
  
  words_that_have_a_c_at_n = [[set() for _ in range(26)] for _ in range(5)]

  while True: 
    line = file1.readline().strip()
    if not line: 
      break
    count += 1
    for i in range(5):
      c = ord(line[i]) - 97 # 0 represents A
      words_that_have_a_c_at_n[i][c].add(line)
  file1.close() 

  p = Puzzlestate(5,5)

  # first, let's inscribe a random word at the first location

  firstword = random.sample(words_that_have_a_c_at_n[2][ord('e')-97],1)[0]
  (startxy,dir) = initialdirectionlist.pop()

  newp = p.inscribe_word(firstword,startxy,dir)
  newp.print()
  fill_in(newp,initialdirectionlist)

  print("bye")

if __name__ == "__main__":
    main()

