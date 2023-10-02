# bombPartY
A python/pygame port of the "BombParty" word game, to be run as a standalone.

## Usage
Server and players must have version 2+ of the pygame package installed.

The server for the game is run by
	python3 game_server.py (ip) (port) (mode) (savefile)
ip and port specify where the server will listen for connections from game clients. mode should always be 'new' for now. savefile specifies where the game logs will be stored.

Once the server is running, the players connect by
	python3 game_client.py (ip) (port) (username)
ip and port are the same as that specified by the server, and username is a distinguishing display name, which will automatically be limited to 20 characters.

## Limitations
Currently, the networking code is not sufficient to host on anything other than localhost. This will be fixed in a later version.
