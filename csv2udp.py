#!/usr/bin/env python3

import struct
import socket
import json
import os
import sys
import csv
import time

help = """

""" + sys.argv[0] + """ - Matteo Ragni 2019

Usage: 

  python """ + sys.argv[0] + """ configuration.json

Read a CSV file and sends each line as an UDP packet. The configuration
file is in json format and requires the following keys:

{
  "socket": {
    "ip_address": "127.0.0.1",  -> Endpoint for the udp packet
    "port": "5555",             -> Endpoint port for the udp packet
    "frequency": "0"            -> Frequency in (Hz) for sending the packet 
                                   (1e-12Hz ... 2000Hz)
  },
  "data": {
    "path": "data.csv",         -> path of the csv origin file to be parsed and send
    "delimiter": ",",           -> data delimiter for the csv file (csv: ',', tsv: '\\t')
    "header": "0",              -> number of header line to skip. 0 to skip none
    "type": "float",            -> type of data to send. As for now it can be only 
                                   "float" (4byte) or "double" (8byte)
    "length": "0"               -> length of the packet to send. Set to zero for dynamic
                                   size. It skip packet if length is set and read line is not 
                                   consistent
  }
}

For frequency: please note that for Windows (I cannot test it) probably the minimum
frequency will be 1/15ms. Check here: https://stackoverflow.com/a/55247488/2319299

"""

class TimedSection(object):
    start = None

    def __init__(self, frequency: float):
      self.timing = (1.0/frequency) * 1e9
      self.tic = 0
      self.old_tic = 0
      self.toc = 0
      self.wait = self.timing
      self.current_frequency = 0.0

    def __enter__(self):
      self.old_tic = self.tic
      self.tic = time.time_ns()
      return self.current_frequency

    def __exit__(self, type, value, traceback):
      self.current_frequency = 1.0 / ((self.toc - self.old_tic + self.wait) * 1e-9)
      self.toc = time.time_ns()
      self.wait = self.timing - (self.toc - self.tic)
      if self.wait > 0:
        time.sleep(self.wait * 1e-9)




class ConfigurationProvider:

  def __init__(self, file_path: str):
    self.ip_address = "127.0.0.1"
    self.port = "5555"
    self.frequency = 0

    self.csv = "data.csv"
    self.length = 1
    self.type = "float"
    self.delimiter = ","
    self.type_id = "f"
    self.header = 0

    self.valid = True

    if not os.path.exists(file_path):
      print("ERROR: Configuration file not found")
      self.valid = false
      return

    with open(file_path) as config:
      try:
        json_config = json.load(config)
      except json.decoder.JSONDecodeError as err:
        print("ERROR: JSON parsing: {}".format(err))
        self.valid = False
        return

      try:
        current_dir = ''
        current_attr = ''
        for attr in ['ip_address', 'port', 'frequency']:
          current_dir = 'socket'
          current_attr = attr
          self.__setattr__(attr, json_config[current_dir][attr])
        for attr in ['csv', 'length', 'type', 'delimiter', 'header']:
          current_dir = 'data'
          current_attr = attr
          self.__setattr__(attr, json_config[current_dir][attr])
      except AttributeError:
        print("ERROR: cannot find attribute {}/{}"
          .format((current_dir, current_attr, getattr(self, current_attr))))
        self.valid = False
        return

      try:
        self.port = int(self.port)
        self.frequency = float(self.frequency)
        self.length = int(self.length)
        self.header = int(self.header)
      except ValueError:
        print("ERROR: Cannot parse socket/port, socket/frequency, data/length or data/header")
        self.valid = False
        return

      if self.frequency < 1e-12 or self.frequency > 2000:
        print("ERROR: Invalid frequency value required")
        self.valid = False
        return

      type_id_selector = {
        "float": "f",
        "double": "d"
      }
      try:
        self.type_id = type_id_selector[self.type]
      except AttributeError:
        print("ERROR: Data type not supported, supported only 'float' or 'double'")
        self.valid =False
        return

      if not os.path.exists(self.csv):
        print("ERROR: CSV file {} not found".format(self.csv))
        self.valid = False
        return

  def __str__(self):
    delimiter_type = {
      "\t": "\\t",
      "\n": "\\n"
    }
    try:
      delimiter = delimiter_type[self.delimiter]
    except KeyError:
      delimiter = self.delimiter
    
    data_len = self.length
    if data_len == 0:
      data_len = "dynamic"
    
    return """
    {} - Matteo Ragni 2019
    Current Config:
      SOCKET: 
        {}:{} with frequency {}Hz
      DATA: 
        file {}
        composed by vector of {} of {} elements delimited by "{}"
        {} initial line to skip
    """.format(sys.argv[0],
      self.ip_address, self.port, self.frequency,
      self.csv, self.type, data_len, delimiter, self.header)

class SocketProvider:
  def __init__(self, config: ConfigurationProvider):
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    self.ip = config.ip_address
    self.port = config.port
    self.type_id = config.type_id
    self.length = config.length

    if self.length == 0:
      self.packer = self.dynamic_pack
    else:
      self.pack_format = '<' + (self.type_id * self.length)
      self.packer = self.static_pack

  def sender(self, data):
    try:
      msg = self.packer(data)
      return self.sock.sendto(msg, (self.ip, self.port))
    except Exception as err:
      print("WARNING: Data sending: {}".format(err))
      return 0

  def dynamic_pack(self, data: list):
    pack_format = '<' + (self.type_id * len(data))
    return struct.pack(pack_format, *data)

  def static_pack(self, data: list):
    return struct.pack(self.pack_format, *data)
    
  def __enter__(self):
    return self.sender

  def __exit__(self, *args):
     pass

class DataProvider:
  def __init__(self, config: ConfigurationProvider):
    self.csv = config.csv
    self.delimiter = config.delimiter
    self.header = config.header
    self.sync = TimedSection(config.frequency)

  def loop(self, sender):
    with open(self.csv, newline='') as f:
      fr = csv.reader(f, delimiter=self.delimiter)
      try:
        for _ in range(self.header):
          next(fr)
        while True:
          with self.sync as current_frequency:
            row = [float(x) for x in next(fr)]
            sender(row)
      except StopIteration:
        print("All data sent")
      except csv.Error as err:
        print("ERROR: csv reading error: {}".format(err)) 




if __name__ == '__main__':
  if len(sys.argv) != 2:
    print(help)
    exit()
  
  config = ConfigurationProvider(sys.argv[1])
  if config.valid:
    print(config)
  else:
    exit()

with SocketProvider(config) as sender:
  reader = DataProvider(config)
  reader.loop(sender)


