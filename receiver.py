#!/usr/bin/env python3

import socket
import struct


MSG_TYPE = 'd'
MSG_SIZE = 8
UDP_IP = '0.0.0.0'
UDP_PORT = 9000


def receiver():
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.bind((UDP_IP, UDP_PORT))
  while True:
    msg = sock.recv(4096)
    print_msg(msg)


def print_msg(msg):
  count = len(msg) // MSG_SIZE
  data = []
  for i in range(count):
    data.append(struct.unpack('<' + MSG_TYPE, msg[i * MSG_SIZE:(i+1) * MSG_SIZE])[0])
  print(data)


if __name__ == "__main__":
  try: 
    print("CTRL+C for exit")
    receiver()
  except KeyboardInterrupt:
    exit()
