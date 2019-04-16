# CSV2UDP

Read a Comma separated value file and sends each line as a UDP packet.
The software is able to send static or dynamic length row, accordingly to a 
configuration file. It requires python3 and should be cross platform, even
if not tested yet on windows.

There are no additional requirements.

 * `udp2csv.py`: the sender script
 * `receiver.py`: a receiver script for testing
 * `csv_generator.py`: a generator for csv files

Matteo Ragni 2019

### Usage 

```
python csv2upd.py configuration.json
```

### Configuration file

Read a CSV file and sends each line as an UDP packet. The configuration
file is in json format and requires the following keys:

```
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
```

### Timing on Window 

For frequency: please note that for Windows (I cannot test it) probably the minimum
frequency will be 1/15ms. Check here: https://stackoverflow.com/a/55247488/2319299
