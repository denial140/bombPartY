#BombPartY v0.1 - a PyGame port of the classic wordgame
#Copyright (C) 2023 Daniel Bassett

#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <https://www.gnu.org/licenses/>.

import chat

class user:
	def __init__(self, connection_no):
		self.connection_no = connection_no
		self.username = ""
		self.playing = False
		
		self.chat_message = chat.message("", "")
		self.chatting = True

		self.lives = 2
		self.letters = {"A": True, "B": True, "C": True, "D": True, "E": True, "F": True, "G": True, "H": True, "I": True, "J": True, "K": True, "L": True, "M": True, "N": True, "O": True, "P": True, "Q": True, "R": True, "S": True, "T": True, "U": True, "V": True, "W": True, "Y": True} #True if still to be used
		
		self.seat = -1
		
		self.word = ""
		self.recent = ""
		
		self.prompt_received = 0 #stores time that the prompt was received
	
	def updateLetters(self, word):
		for letter in word:
			if letter == "X" or letter == "Z":
				continue
			self.letters[letter] = False
		
		flip = True
		for letter in self.letters:
			if self.letters[letter]:
				flip = False
				break
		
		if flip:
			for letter in self.letters:
				self.letters[letter] = True
			
			if self.lives < 3:
				self.lives += 1
