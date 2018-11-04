#!/usr/local/bin/python3

'''
Geometry:
	
	  0 1 2 ... width-1
   0
   1
   2
   ...
   height-1
'''

class puzzlestate:
	def __init__(self,height,width):
		self.height = height
		self.width = width
		self.layout = []
		for x in range(height):	
			for y in range(width):
				self.layout[y][x] = None
		self.wordsused = []
	def getheight():
		return self.height
	def getwidth():
		return self.width
  def getwordsused():
    return self.wordsused


