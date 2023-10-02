#BombPartY v0.2.1 - a PyGame port of the classic wordgame
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

import random
import json
import time

import user

class game:
	def __init__(self):
		self.started = False
		self.ended = False
		self.end_time = 0
		
		self.players = []
		self.alive_players = 0
		
		self.prompt = ""
		self.prompt_start_player = 0
		self.prompt_start_time = 0
		self.current_player = 0
		
		self.current_entry = ""
		
		self.used_words = []
		self.dictionary = []
		
		dictionary_stream = open("dictionary/english_small.txt","r")
		for word in dictionary_stream:
			self.dictionary.append(word[:-1]) #Removes EOL character
		dictionary_stream.close()
		
		self.prompt_difficulty = 0
	
	#Generate prompt
	def generatePrompt(self):
		if self.prompt_difficulty == 0: #Standard
			wordNumber = len(self.dictionary)
			while wordNumber == len(self.dictionary) or self.dictionary[wordNumber] in self.used_words:
				wordNumber = random.randrange(0, len(self.dictionary))
	
			wordLength = len(self.dictionary[wordNumber])
			promptLength = random.randint(2,3)
			promptStart = random.randrange(0, wordLength-promptLength)
			
			self.prompt = self.dictionary[wordNumber][promptStart:promptStart+promptLength]
			
		self.prompt_start_time = time.time_ns()
		self.prompt_start_player = self.current_player
		
	#Check validity of user entry	
	def checkForPrompt(self, word):
		found = False
		for i in range(len(word) - len(self.prompt)+1):
			if word[i:i+len(self.prompt)] == self.prompt:
				found = True
		return found
	
	def checkDictionary(self, word):
		lower = 0
		upper = len(self.dictionary)
		
		#Checks if word is in dictionary by binary search
		while upper - lower > 1:
			if word < self.dictionary[(upper+lower)>>1]:
				upper = (upper+lower)>>1
			else:
				lower = (upper+lower)>>1
		
		return word == self.dictionary[lower]
	
	def findNextAlive(self):
		#Sets the current player to the next alive player
		#Returns True if a new prompt is needed.
		wrapped = (len(self.players) == 1)
		self.current_player = (self.current_player + 1) % len(self.players) #move at least one player
		if self.current_player == self.prompt_start_player:
			wrapped = True
		
		while self.players[self.current_player].lives == 0: #skip to the next if that player is dead
			self.current_player = (self.current_player + 1) % len(self.players)
			if self.current_player == self.prompt_start_player:
				wrapped = True
		
		return wrapped
	
	#Network helper functions
	def packAll(self, seatNum, letters): #packs into json for transfer to player in seat seatNum
		game_dict = {'started': self.started, 
					'ended': self.ended,
					'num_players': len(self.players), 
					'player_lives': [self.players[i].lives for i in range(len(self.players))],
					'player_usernames': [self.players[i].username for i in range(len(self.players))],
					'current_player': self.current_player,
					'prompt': self.prompt,
					'used_words': self.used_words,
					'timestamp': time.time_ns(),
					'data': "full",
					'your_seat': seatNum,
					'your_letters': letters,
					'current_entry': self.current_entry}
		
		return dict(type="text/json", encoding="utf-8", content = game_dict)
	
	def depackAll(self, decode, player):
		self.started = decode.get('started')
		self.ended = decode.get('ended')
		self.current_player = decode.get('current_player')
		self.prompt = decode.get('prompt')
		self.used_words = decode.get('used_words')
		self.current_entry = decode.get('current_entry')
		player.seat = decode.get('your_seat')
		player.letters = decode.get('your_letters')
		if decode.get('num_players') > len(self.players): #add new players
			for i in range(len(self.players), decode.get('num_players')):
				self.players.append(user.user(-1))
				self.players[-1].playing = True
				self.players[-1].username = decode.get('player_usernames')[i]
				
		for i in range(len(self.players)): #update lives
			self.players[i].lives = decode.get('player_lives')[i]
			
		
