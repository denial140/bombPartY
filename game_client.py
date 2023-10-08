#BombPartY v0.3.1 - a PyGame port of the classic wordgame
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

import sys
import networking
import selectors
import pygame
import time

import user
import game
import chat

FPS = 60
letter_list = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'Y']

pygame.init()
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEWHEEL]) 

def main():
	"""Plays games of bombparty"""

	#License info
	print("bombPartY v0.3.1 Copyright (C) 2023 Daniel Bassett")
	print("This program comes with ABSOLUTELY NO WARRANTY.")
	print("This is free software, and you are welcome to redistribute it under certain conditions.")
	print("See the GNU General Public License for more details.")

	if len(sys.argv) != 4:
		print("Usage:", sys.argv[0], "<host> <port> <username>")
		sys.exit(1)
	host, port, username = sys.argv[1], int(sys.argv[2]), sys.argv[3][:20] #TODO: sanitise input
	username = sys.argv[3]
    
	#Initiate connection
	sel = selectors.DefaultSelector()
	msg = networking.start_connection(host, port, sel)
    
	#Send file validation (TODO)
	
	me = False
	
	current_game = game.game()
	game_chat = chat.chatlog()
	
	#REMOVE, DEBUGGING ONLY
	#me.playing = True
	#me = user.player(username)
	#current_game = game.game()
	
	#Initialise window
	screen = pygame.display.set_mode((1440, 720))
	pygame.display.set_caption("bombPartY") #Window title
	screen.fill((181,131,90))
	clock = pygame.time.Clock()
	
	
	join_rect = pygame.Rect(620, 600, 100, 32) #join game button
	
	prompt_rect = pygame.Rect(220, 500, 640, 32) #display current prompt
	
	answer_rect = pygame.Rect(220, 600, 640, 32) #Display currently typed answer
	
	player_rect = pygame.Rect(0, 0, 1000, 360) #Display player list
	
	letter_rect = pygame.Rect(1000,0,80,720) #Display player's letters
	
	chat_rect = pygame.Rect(1080, 0, 360, 540) #Display chat messages
	chat_message_rect = pygame.Rect(1080, 540, 360, 180) #Display currently typed message
	pygame.draw.rect(screen, pygame.Color(90,65,45), chat_rect)
	pygame.draw.rect(screen, pygame.Color(45,35,25), chat_message_rect)
	
	pygame.display.flip()
	
	#Set up text
	base_font = pygame.font.Font(None, 32)
	chat_font = pygame.font.Font(None, 32)
	
	#Main loop
	running = True
	screen_update = True
	connecting_drawn = False
	while running:
		#Networking updates
		decodes = msg.readAll()
		for decode in decodes:
			message_type = decode.get('data')
			print(message_type)
						
			if message_type == "connection": #received connection number
				connection_no = decode.get('connection_no')
				me = user.user(connection_no)
				me.chat_message.username = username
						
				msg.to_send = dict(type="text/json", encoding="utf-8", content={'username': username, 'timestamp': time.time_ns(), 'data': 'username', 'connection_no': connection_no})
				msg.write()
					
			elif message_type == "full":
				#print("this should happen") #it isn't happening for god knows what reason. it's showing up as sending.
				current_game.depackAll(decode, me)
				screen_update = True
						
			elif message_type == "chat":
				game_chat.depackAll(decode, chat_font)
				screen_update = True
			
			elif message_type == "game_start":
				if me.playing:
					me.chatting = False
		
		msg.sendAll()
	
		#Handle quit, typing etc.
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			
			if me:
				if event.type == pygame.KEYDOWN:
					if me.chatting or not me.playing: #chat entry
						if event.key == pygame.K_BACKSPACE:
							me.chat_message.message = me.chat_message.message[:-1]
							screen_update = True
						
						elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER: #send message
							msg.to_send = dict(type="text/json", encoding="utf-8", content={'connection_no': me.connection_no, 'message': me.chat_message.message, 'data': "chat"})
							msg.write()
							me.chat_message.message = ""
							screen_update = True
						
						elif len(me.chat_message.message) < 100: #TODO: sanitise input
							me.chat_message.message += event.unicode
							screen_update = True
					
					elif current_game.current_player == me.seat: #word entry
						if event.key == pygame.K_BACKSPACE:
							me.word = me.word[:-1]
							msg.to_send = dict(type="text/json", encoding="utf-8", content={'connection_no': me.connection_no, 'word': me.word, 'data': "type"})
							msg.write()
							
							screen_update = True
						
						elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
							#TODO: add game stuff?
							msg.to_send = dict(type="text/json", encoding="utf-8", content={'connection_no': me.connection_no, 'word': me.word, 'data': "solve"})
							msg.write()
							me.word = ""
							screen_update = True
						
						elif len(me.word) < 30 and pygame.K_a <= event.key and event.key <= pygame.K_z: #TODO: better sanitising e.g. to stop ctrl+C stuff giving funny characters
							me.word += event.unicode
							me.word = me.word.upper()
							msg.to_send = dict(type="text/json", encoding="utf-8", content={'connection_no': me.connection_no, 'word': me.word, 'data': "type"})
							msg.write()
							
							screen_update = True
				
				elif event.type == pygame.MOUSEBUTTONDOWN:
					mouseX, mouseY = event.pos
					if current_game.started:
						if me.playing:
							if chat_message_rect.collidepoint(mouseX, mouseY):
								me.chatting = True
								
							elif answer_rect.collidepoint(mouseX, mouseY):
								me.chatting = False
							
					else:
						if not me.playing:
							if join_rect.collidepoint(mouseX, mouseY):
								me.playing = True
								msg.to_send = dict(type="text/json", encoding="utf-8", content={'connection_no': me.connection_no, 'data': 'game_join'})
								msg.write()
						elif me.seat == 0:
							if join_rect.collidepoint(mouseX, mouseY):
								msg.to_send = dict(type="text/json", encoding="utf-8", content={'connection_no': me.connection_no, 'data': 'game_start'})
								msg.write()
				
				elif event.type == pygame.MOUSEWHEEL:
					game_chat.scrollY -= 10*event.y #scroll by the given amount
					if event.y > 0: #No longer snap to the bottom
						game_chat.bottom = False
						
					if game_chat.scrollY < 0: #prevent scrolling off the top of chat
						game_chat.scrollY = 0 
					
					elif game_chat.scrollY > game_chat.height - 540:
						game_chat.scrollY = game_chat.height - 540
						game_chat.bottom = True #snap to the bottom
					
					screen_update = True
		
		if me:
			#Update screen
			if screen_update:
				screen_update = False
				
				if current_game.started:
					if not current_game.ended:
						pygame.draw.rect(screen, pygame.Color(181,131,90), prompt_rect)
						prompt_surface = base_font.render("Quick! Type an English word containing " + current_game.prompt, True, (255,255,255))
						screen.blit(prompt_surface, (prompt_rect.x, prompt_rect.y))
					
						if current_game.current_player == me.seat:
							#Draw answer entry rectangle
							pygame.draw.rect(screen, pygame.Color(45,35,25), answer_rect)
							answer_surface = base_font.render(me.word, True, (255,255,255))
							screen.blit(answer_surface, (answer_rect.x+20,answer_rect.y+5))
						else:
							pygame.draw.rect(screen, pygame.Color(181,131,90), answer_rect)
							answer_surface = base_font.render(me.word, True, (255,255,255))
							screen.blit(answer_surface, (answer_rect.x+20,answer_rect.y+5))
					
					else:
						pygame.draw.rect(screen, pygame.Color(181,131,90), prompt_rect)
						pygame.draw.rect(screen, pygame.Color(181,131,90), answer_rect)
						if current_game.current_player == me.seat:
							prompt_surface = base_font.render("Congratulations! You have won.", True, (255,255,255))
						else:
							prompt_surface = base_font.render("Unlucky! The winner is: " + str(current_game.players[current_game.current_player].username), True, (255,255,255))
						
						screen.blit(prompt_surface, (prompt_rect.x, prompt_rect.y))
							
				elif not me.playing:
					#Draw join button
					pygame.draw.rect(screen, pygame.Color(45,35,25), join_rect)
					join_surface = base_font.render("Join!", True, (255,255,255))
					screen.blit(join_surface, (join_rect.x+10, join_rect.y+5))
					
					pygame.draw.rect(screen, pygame.Color(181,131,90), prompt_rect)
				
				else:
					pygame.draw.rect(screen, pygame.Color(181,131,90), prompt_rect) #
				
					#Waiting to play
					if me.seat == 0:
						#print(len(current_game.players))
						pygame.draw.rect(screen, pygame.Color(45,35,25), join_rect)
						join_surface = base_font.render("Start!", True, (255,255,255))
						screen.blit(join_surface, (join_rect.x+10, join_rect.y+5))
					else:
						pygame.draw.rect(screen, pygame.Color(181, 131, 90), join_rect)
				
				#Draw previous chat messages
				chat_surface_full = pygame.Surface((360, game_chat.height))
				pygame.draw.rect(chat_surface_full, pygame.Color(90,65,45), (pygame.Rect(0,0, chat_rect.w, chat_rect.h)))
				y = 0
				
				for chatMsg in game_chat.messages: #Draws the full chat history
					y = chatMsg.drawText(chat_font, chat_surface_full, y) + 5
				
				chat_display_rect = pygame.Rect(0, game_chat.scrollY, 360,540) #Selects the part of the chat for the player's current scrolling value
				chat_surface_display = chat_surface_full.subsurface(chat_display_rect) 
				
				screen.blit(chat_surface_display, (chat_rect.x, chat_rect.y))
				
				#Draw current chat message
				chat_message_surface = pygame.Surface((360, 180))
				pygame.draw.rect(chat_message_surface, pygame.Color(45,35,25), pygame.Rect(0,0, chat_message_rect.w, chat_message_rect.h)) #why is this not doing anything
				me.chat_message.drawText(chat_font, chat_message_surface, 5)
				screen.blit(chat_message_surface, (chat_message_rect.x, chat_message_rect.y))
				
				#Draw players remaining letters
				pygame.draw.rect(screen, pygame.Color(181,131,90), letter_rect)
				for i in range(24):
					letter_surface = base_font.render(letter_list[i], True, (255,255,255))
					x = 1000
					if i >= 12:
						x += 40
						
					if me.letters[letter_list[i]]:
						screen.blit(letter_surface, (x, 40*(i%12)))
				
				#List entrant names
				pygame.draw.rect(screen, pygame.Color(181,131,90), player_rect)
				for i in range(len(current_game.players)):
					player_string = str(i)+" "+current_game.players[i].username+" "+str(current_game.players[i].lives)
					if i == current_game.current_player:
						player_string += " < " + current_game.current_entry
					entrant_surface = base_font.render(player_string, True, (255,255,255))
					screen.blit(entrant_surface, (0,32*i))
				
				pygame.display.flip()
		

		if not connecting_drawn:
			connecting_surface = base_font.render("Connecting...", True, (255,255,255))
			screen.blit(connecting_surface, (0,0))
			connecting_drawn = True
		
		#New frame			
		clock.tick(FPS)
	

if __name__ == "__main__":
	main()
