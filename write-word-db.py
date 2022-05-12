#!/usr/bin/env python3

import sqlite3
import os

con = sqlite3.connect('words.db')
con.execute('''CREATE TABLE words
               (word text NOT NULL, source integer)''')

sql_ddl = "INSERT INTO words VALUES (?, ?)"

cur = con.cursor()
with open('wordstotry/english1020-category.txt', 'r', encoding="latin-1") as f:
  while True:
    line = f.readline().strip()
    if not line:
      break
    print(f'writing {line}')
    cur.execute(sql_ddl, (line,0))

con.commit()
con.close()


