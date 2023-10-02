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

"""Module containing the structure used for a socket. Transfers json files."""

import socket
import selectors
import sys
import struct
import json

def start_connection(host, port, selector):
    """Connects the client to the server."""
    addr = (host, port)
    print("starting connection to", addr)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setblocking(False)
    sock.connect_ex(addr)
    events = selectors.EVENT_WRITE | selectors.EVENT_READ
    message = Message(selector, sock, addr)
    selector.register(sock, events, data=message)
    #print("Connected successfully.")
    return message

def open_connection(host, port, selector):
    """Opens the server to client connections."""
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Avoid bind() exception: OSError: [Errno 48] Address already in use
    lsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lsock.bind((host, port))
    lsock.listen()
    print("listening on", (host, port))
    lsock.setblocking(False)
    selector.register(lsock, selectors.EVENT_READ, data=None)

def accept_wrapper(sock, selector):
    """Accept connections from client, add to selector."""
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    message = Message(selector, conn, addr)
    selector.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=message)
    return message

class Message:
    """Class that handles the sending and receiving of json messages. Data of a socket."""
    def __init__(self, selector, sock, addr):
        self.selector = selector
        self.sock = sock
        self.addr = addr
        self._recv_buffer = b""
        self._send_buffer = b""

        self._jsonheader_len = None
        self.jsonheader = None
        self.received = None

        self.to_send = {}

    def _read(self):
        try:
            #print("attempting to read data")
            data = self.sock.recv(4096)
            #print("successfully read data")
        except BlockingIOError:
            print("might be blocking issue (read)")
            pass
        else:
            if data:
                self._recv_buffer += data
                print(data)
            else:
                raise RuntimeError("Peer closed.")

    def _write(self):
        if self._send_buffer:
            print("sending", repr(self._send_buffer))
            try:
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                print("might be blocking issue (write)")
                pass
            else:
                self._send_buffer = self._send_buffer[sent:]

    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        return json.loads(json_bytes.decode(encoding))

    def _create_message(self, *, content_bytes, content_type, content_encoding):
        jsonheader = {
            "byteorder": sys.byteorder,
            "content-type": content_type,
            "content-encoding": content_encoding,
            "content-length": len(content_bytes),
        }
        jsonheader_bytes = self._json_encode(jsonheader, "utf-8")
        message_hdr = struct.pack(">H", len(jsonheader_bytes))
        message = message_hdr + jsonheader_bytes + content_bytes
        return message

    def process_events(self, mask):
        """Check if the socket should be read or written to."""
        if mask & selectors.EVENT_READ:
            move = self.read()
            return move
        if mask & selectors.EVENT_WRITE:
            self.write()

    def read(self):
        """Reading process."""
        self._read()

        if self._jsonheader_len is None:
            self.process_protoheader()

        if self._jsonheader_len is not None:
            if self.jsonheader is None:
                self.process_jsonheader()

        if self.jsonheader:
            if self.received is None:
                move = self.process_content()
                return move
        return None

    def write(self):
        """Writing process."""
        if self.to_send:
            self.queue_message()

        self._write()

    def queue_message(self):
        """Package messages to be sent and move them to the buffer."""
        content = self.to_send["content"]
        content_type = self.to_send["type"]
        content_encoding = self.to_send["encoding"]
        if content_type == "text/json":
            req = {
                "content_bytes": self._json_encode(content, content_encoding),
                "content_type": content_type,
                "content_encoding": content_encoding,
            }

        message = self._create_message(**req)
        self._send_buffer += message
        self.to_send = None

    def process_protoheader(self):
        """Process the protoheader, which contains the length of the jsonheader."""
        protoheader_len = 2

        if len(self._recv_buffer) >= protoheader_len:
            self._jsonheader_len = struct.unpack(
                ">H", self._recv_buffer[:protoheader_len]
            )[0]
            self._recv_buffer = self._recv_buffer[protoheader_len:]

    def process_jsonheader(self):
        """Process the jsonheader, which contains the length of the content."""
        jsonheader_len = self._jsonheader_len
        if len(self._recv_buffer) >= jsonheader_len:
            self.jsonheader = self._json_decode(
                self._recv_buffer[:jsonheader_len], "utf-8"
            )
            self._recv_buffer = self._recv_buffer[jsonheader_len:]
        for required_header in ("byteorder", "content-length", "content-type", "content-encoding"):
            if required_header not in self.jsonheader:
                raise ValueError(f'Missing required header "{required_header}".')

    def process_content(self):
        """Process the actual content of the message."""
        content_len = self.jsonheader["content-length"]
        if not len(self._recv_buffer) >= content_len:
            return
        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]

        if self.jsonheader["content-type"] == "text/json":
            encoding = self.jsonheader["content-encoding"]
            self.received = self._json_decode(data, encoding)
            print("received response", repr(self.received))
            move = self.received
            self._jsonheader_len = None
            self.jsonheader = None
            self.received = None
            return move
        return None

    def close(self):
        """Close the connection."""
        print("closing connection to", self.addr)
        try:
            self.selector.unregister(self.sock)
        except Exception as err:
            print(
                "error: selector.unregister() exception for",
                f"{self.addr}: {repr(err)}",
            )

        try:
            self.sock.close()
        except OSError as err:
            print(
                "error: socket.close() exception for",
                f"{self.addr}: {repr(err)}",
            )
        finally:
            self.sock = None

    def nothing_to_send(self):
        """Checks whether the message is sending anything."""
        if self.to_send:
            return False
        elif self._send_buffer:
            return False
        return True
        
    def readAll(self):
        decodes = []
        events = self.selector.select(timeout=1)
        for key, mask in events:
            message = key.data
            decode = False
            try: 
                potential_decode = message.process_events(mask)
                if potential_decode:
                    decode = potential_decode

            except Exception:
                message.close()
            
            if decode:
                decodes.append(decode)
                
        return decodes
    
    def sendAll(self):
        while not self.nothing_to_send:
            self.readAll()
    
    
