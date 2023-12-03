#!/usr/bin/env python3

l = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

def stick_back_in_deck(l):
  oldfirst = l.pop(0)
  l.insert(int(len(l)/2+0.5),oldfirst)

print(l)
stick_back_in_deck(l)
print(l)

l2 = [ 'Q', 'R' ]
print(l2)
stick_back_in_deck(l2)
print(l2)
