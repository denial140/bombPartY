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

import pygame

class message:
	def __init__(self, message, username):
		self.message = message
		self.username = username
	
	def toDisplay(self):
		return self.username + ": " + self.message
		
	def drawText(self, font, surface, y):
		text = self.toDisplay()
		while len(text) > 0:
			i = 0
			while i < len(text) and font.size(text[:i])[0] < 350: #determine the maximum text that will fit on the line
				i += 1
			
			if font.size(text[:i])[0] >= 350:
				i -= 1
				i = text.rfind(" ", 0, i) + 1
			
			text_surface = font.render(text[:i], True, (255,255,255))
			surface.blit(text_surface, (5, y))
			
			y += font.size(text[:i])[1] + 5
			text = text[i:]
		
		return y
			

class chatlog:
	def __init__(self):
		self.messages = []
		self.bottom = True
		self.scrollY = 0
		self.height = 540
	
	def drawHeight(self, font):
		height = 0
		dummy_surface = pygame.Surface((360, 360))
		for msg in self.messages:
			height += msg.drawText(font, dummy_surface, 0) + 5
		return max(height, 540)
	
	def packAll(self):
		chat_dict = {'num_messages': len(self.messages),
					'messages': [self.messages[i].message for i in range(len(self.messages))],
					'usernames': [self.messages[i].username for i in range(len(self.messages))],
					'data': "chat"}
		
		return dict(type="text/json", encoding="utf-8", content = chat_dict)
	
	def depackAll(self, decode, font):
		if decode.get('num_messages') > len(self.messages):
			for i in range(len(self.messages), decode.get('num_messages')):
				self.messages.append(message(decode.get('messages')[i], decode.get('usernames')[i]))
		
		if self.bottom:
			self.height = self.drawHeight(font)
			self.scrollY = self.height - 540
		else:
			self.height = self.drawHeight(font)
