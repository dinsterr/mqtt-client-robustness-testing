#!/usr/bin/env python

# Adapted from https://gist.github.com/sivachandran/1969859

import socket
import threading
import select

terminate_all = False


class ClientSocketThread(threading.Thread):
	def __init__(self, client_socket: socket.socket, target_host: str, target_port: int):
		threading.Thread.__init__(self)
		self.__clientSocket = client_socket
		self.__targetHost = target_host
		self.__targetPort = target_port
		
	def run(self):
		print("Client Thread started")
		
		self.__clientSocket.setblocking(False)
		
		target_host_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		target_host_socket.connect((self.__targetHost, self.__targetPort))
		target_host_socket.setblocking(False)
		
		client_data = bytes()
		target_host_data = bytes()
		terminate = False
		while not terminate and not terminate_all:
			inputs = [self.__clientSocket, target_host_socket]
			outputs = []
			
			if len(client_data) > 0:
				outputs.append(self.__clientSocket)
				
			if len(target_host_data) > 0:
				outputs.append(target_host_socket)
			
			try:
				inputs_ready, outputs_ready, errors_ready = select.select(inputs, outputs, [], 1.0)
			except Exception as e:
				print(e)
				break

			data = None
			for inp in inputs_ready:
				if inp == self.__clientSocket:
					try:
						data = self.__clientSocket.recv(4096)
					except Exception as e:
						print(e)
					
					if data is not None:
						if len(data) > 0:
							target_host_data += data
						else:
							terminate = True
				elif inp == target_host_socket:
					try:
						data = target_host_socket.recv(4096)
					except Exception as e:
						print(e)
						
					if data is not None:
						if len(data) > 0:
							client_data += data
						else:
							terminate = True
						
			for out in outputs_ready:
				if out == self.__clientSocket and len(client_data) > 0:
					bytes_written = self.__clientSocket.send(client_data)
					if bytes_written > 0:
						client_data = client_data[bytes_written:]
				elif out == target_host_socket and len(target_host_data) > 0:
					bytes_written = target_host_socket.send(target_host_data)
					if bytes_written > 0:
						target_host_data = target_host_data[bytes_written:]
		
		self.__clientSocket.close()
		target_host_socket.close()
		print("Client Thread terminated")


def proxy_socket(local_host: str, local_port: int, target_host: str, target_port: int):
	global terminate_all

	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind((local_host, local_port))
	server_socket.listen(5)

	while True:
		try:
			print("\nWaiting for client...")
			client_socket, address = server_socket.accept()
		except KeyboardInterrupt:
			terminate_all = True
			print("\nTerminating...")
			break
		print("Client Thread starting...")
		ClientSocketThread(client_socket, target_host, target_port).start()

	server_socket.close()
	print("Proxy Sockets closed")
