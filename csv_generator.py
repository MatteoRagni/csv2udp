#!/usr/bin/env python3

import csv
import random

FILE = "database2.csv"
HEADERS = 3
ROWS = 200
COLS = 10
DYNAMIC = True


with open(FILE, "w") as f:
  fw = csv.writer(f, delimiter='\t')
  for i in range(HEADERS):
    fw.writerow("HEADER {}".format(i + 1))
  for i in range(ROWS):
    if DYNAMIC:
      fw.writerow([float(i + x) for x in range(random.choice(range(2,COLS)))])
    else:
      fw.writerow([float(i + x) for x in range(COLS)])
