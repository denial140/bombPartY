#BombPartY v0.3 - a PyGame port of the classic wordgame
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
import json

import user
import game
import chat

def main():
	"""Hosts games of bombparty"""
	
	#License info
	print("bombPartY v0.3 Copyright (C) 2023 Daniel Bassett")
	print("This program comes with ABSOLUTELY NO WARRANTY.")
	print("This is free software, and you are welcome to redistribute it under certain conditions.")
	print("See the GNU General Public License for more details.")
	
	if len(sys.argv) != 5:
		print("Usage:", sys.argv[0], "<host> <port> <new/load> <save name>")
		sys.exit(1)
	host, port, state, save_name = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    
    #Logging
	save_file = open(save_name, "w", encoding="utf-8")
    
    #Initiate networking
	sel = selectors.DefaultSelector()
	networking.open_connection(host, port, sel)

	current_game = game.game()
	game_chat = chat.chatlog()
	
	connections = []
	connection_users = []
	game_update = False
	while True:
		#Connection events
		events = sel.select(timeout=1)
		for key, mask in events:
			if key.data is None: #new connection
				if len(connections) < 10:
					connections.append(networking.accept_wrapper(key.fileobj, sel))
					connection_users.append(user.user(len(connections)-1)) #creates user object for the connection
					connections[-1].to_send = dict(type="text/json", encoding="utf-8", content={'connection_no': len(connections)-1, 'timestamp': time.time_ns(), 'data': 'connection'})
					connections[-1].sendAll()
				else:
					conn, addr = key.fileobj.accept()
					del addr
					conn.close()
					print("Extra connection rejected.")
			
			else: #data transmission attempt
				message = key.data
				decode = False
				try: 
					potential_decode = message.process_events(mask)
					if potential_decode:
						decode = potential_decode
						
				except Exception:
					message.close()
				
				if decode: #data received
					message_type = decode.get('data')
					
					if message_type == 'username': #transmitted username for connection
						username = decode.get('username')
						if len(username) > 20:
							username = username[:20]
						connection_no = int(decode.get('connection_no'))
						connection_users[connection_no].username = username
						json.dump(dict(type="text/json", encoding="utf-8", content={'received_timestamp': time.time_ns(), 'username': decode.get('username'), 'sent_timestamp_claim': decode.get('timestamp')}),save_file, indent=4)
						
						#Send current game and chat data to new user
						connections[connection_no].to_send = current_game.packAll(connection_users[connection_no].seat, connection_users[connection_no].letters)
						connections[connection_no].sendAll()
						connections[connection_no].to_send = game_chat.packAll()
						connections[connection_no].sendAll()
					
					elif message_type == "game_join":
						connection_no = int(decode.get('connection_no'))
						current_game.players.append(connection_users[connection_no]) #this code seems sus
						connection_users[connection_no].playing = True #like 
						connection_users[connection_no].seat = len(current_game.players)-1
												
						game_update = True
					
					elif message_type == "game_start":
						if connection_users[decode.get('connection_no')].seat == 0: #came from right player
							current_game.started = True
							current_game.generatePrompt()
							
							current_game.current_player = 0
							current_game.alive_players = len(current_game.players)
							
							game_update = True
					
					elif message_type == "type":
						connection_no = int(decode.get('connection_no'))
						if connection_users[connection_no].seat == current_game.current_player:
							current_game.players[current_game.current_player].word = decode.get('word')
							current_game.current_entry = decode.get('word')
							game_update = True
					
					elif message_type == "solve":
						connection_no = int(decode.get('connection_no'))
						solve_attempt = decode.get('word')
						
						if connection_users[connection_no].seat == current_game.current_player:
							current_game.current_entry = ""
							
							#check if solve_attempt is successful:
							if current_game.checkForPrompt(solve_attempt):
								if current_game.checkDictionary(solve_attempt):
									if not (solve_attempt in current_game.used_words): #solve_attempt successful
										current_game.players[current_game.current_player].updateLetters(solve_attempt)
										current_game.used_words.append(solve_attempt)
										
										current_game.findNextAlive()
										current_game.generatePrompt()
										
										game_update = True
					
					elif message_type == "chat":
						connection_no = int(decode.get('connection_no'))
						game_chat.messages.append(chat.message(decode.get('message'), connection_users[connection_no].username))
						
						for i in range(len(connections)): #send new chat message to everyone
							connections[i].to_send = game_chat.packAll()
							connections[i].sendAll()
										
		#player dies
		if time.time_ns() > current_game.prompt_start_time + 5000000000:
			if current_game.ended: #Have displayed victory messages long enough; start a new game
				current_game = game.game()
				for i in range(len(connections)):
					connection_users[i].seat = -1
					connection_users[i].lives = 2
					connection_users[i].playing = False
					connection_users[i].word = ""
					connection_users[i].letters = {"A": True, "B": True, "C": True, "D": True, "E": True, "F": True, "G": True, "H": True, "I": True, "J": True, "K": True, "L": True, "M": True, "N": True, "O": True, "P": True, "Q": True, "R": True, "S": True, "T": True, "U": True, "V": True, "W": True, "Y": True}
				
				game_update = True
				
			elif current_game.started:
				current_game.current_entry = ""
				current_game.players[current_game.current_player].lives -= 1
				
				#player out?
				if current_game.players[current_game.current_player].lives == 0: #check for game end
					current_game.alive_players -= 1
					if (len(current_game.players) > 1 and current_game.alive_players == 1) or current_game.alive_players == 0:
						current_game.ended = True
						if len(current_game.players) > 1:
							current_game.findNextAlive() #Set player to the winning player
				
				if not current_game.ended:
					if current_game.findNextAlive(): #Prompt has gone through all live players
						current_game.generatePrompt()
			
				current_game.prompt_start_time = time.time_ns()			
			
				game_update = True
	
		if game_update:
			game_update = False
			for i in range(len(connections)): #send new entrant data to all players
				connections[i].to_send = current_game.packAll(connection_users[i].seat, connection_users[i].letters)
				connections[i].sendAll()
						
					
					
if __name__ == "__main__":
	main()
