import os
import sqlite3
import sqlite3 as sql
import csv
import re

mainfolder = os.getcwd()
os.chdir('tests_csv')

def filter_csv(file):
    if ".csv" in file:
        return True
    else:
        return False

def clean_value(s):
    s = s.strip()

    num_candidate = s.replace(' ', '')

    try:
        return int(num_candidate)
    except ValueError:
        pass

    try:
        return float(num_candidate)
    except ValueError:
        pass

    return ' '.join(s.split())

csv_files = list(filter(filter_csv, os.listdir()))

os.chdir('..')
print(os.getcwd())

def get_db():
    conn = sql.connect('data.db')
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as db:
    db.execute("""
    CREATE TABLE IF NOT EXISTS data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_date TEXT,
        source TEXT,
        payer TEXT,
        account_number INTEGER,
        amount INTEGER,
        external_id TEXT
    )
    """)

for i in range (len(csv_files)):
    with open(mainfolder+"\\tests_csv\\"+csv_files[i], 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file, delimiter=',')
        print(i+1)

        #Это цикл строк
        for row in csv_reader:
            if "external_id" in row:
                continue
            else:
                temp_array = row
                spacebarcheck = 0
                #Это цикл слов
                for j in range (len(temp_array)):
                    temp_array[j] = clean_value(temp_array[j])

                print(temp_array)

input()