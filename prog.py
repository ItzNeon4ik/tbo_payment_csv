import os
import sqlite3
import sqlite3 as sql
import csv

mainfolder = os.getcwd()
os.chdir('tests_csv')
log_path = mainfolder + "\\error_log.txt"
results = {
    "files": 0,
    "rows": 0,
    "added": 0,
    "dublicates": 0,
    "errors": 0
}


def filter_csv(current_file):
    if ".csv" in current_file:
        return True
    else:
        return False

def clean_value(s):
    s = s.strip()

    num_candidate = s.replace(' ', '')
    num_candidate = num_candidate.replace(',', '.')

    try:
        return int(num_candidate)
    except ValueError:
        pass

    try:
        return float(num_candidate)
    except ValueError:
        pass

    return ' '.join(s.split())

def check_value(s):
    if not isinstance(s, (int, float)):
        return False
    elif s <= 0:
        return False
    else:
        return True

def create_result(result, folder):
    result_path = folder + "\\result.txt"
    with open(result_path, 'w', encoding='utf-8') as result_file:
        result_file.write("Обработано файлов: " + str(result["files"]) + "\n")
        result_file.write("Всего строк: " + str(result["rows"]) + "\n")
        result_file.write("Добавлено: " + str(result["added"]) + "\n")
        result_file.write("Дублей: " + str(result["dublicates"]) + "\n")
        result_file.write("Ошибок: " + str(result["errors"]) + "\n")

csv_files = list(filter(filter_csv, os.listdir()))

os.chdir('..')
print(os.getcwd())

def get_db():
    conn = sql.connect('payments.db')
    conn.row_factory = sqlite3.Row
    return conn

with open(log_path, 'w', encoding='utf-8') as log_file, get_db() as db:
    db.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_date TEXT,
        source TEXT,
        payer TEXT,
        account_number INTEGER,
        amount INTEGER,
        external_id TEXT,
        UNIQUE(payment_date, payer, account_number, amount)
    )
    """)

    #Это цикл файлов
    for i in range (len(csv_files)):
        results["files"] += 1
        with open(mainfolder+"\\tests_csv\\"+csv_files[i], 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file, delimiter=',')
            row_number = 0
            #Это цикл строк
            for row in csv_reader:
                temp_array = row
                results["rows"] += 1

                # Это цикл слов
                for j in range(len(temp_array)):
                    temp_array[j] = clean_value(temp_array[j])

                if "" in temp_array and temp_array[len(temp_array)-1] != "":
                    msg = f"[{csv_files[i]} | строка {row_number}] Отсутствуют критические значения: {temp_array}"
                    log_file.write(msg + "\n")
                    results["errors"] += 1

                elif not check_value(temp_array[4]) and row_number != 0:
                    msg = f"[{csv_files[i]} | строка {row_number}] Неверный тип данных в ячейке: {temp_array[4]}"
                    log_file.write(msg + "\n")
                    results["errors"] += 1

                else:
                    if row_number != 0:
                        changes_before = db.total_changes
                        db.execute("""
                            INSERT OR IGNORE INTO payments
                            (payment_date, source, payer, account_number, amount, external_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (temp_array[0], temp_array[1], temp_array[2], temp_array[3], temp_array[4], temp_array[5] if len(temp_array) > 5 else None))
                        results["added"] += 1

                        if db.total_changes == changes_before:
                            msg = f"[{csv_files[i]} | строка {row_number}] Дубликат пропущен: {temp_array}"
                            log_file.write(msg + "\n")
                            results["dublicates"] += 1

                row_number += 1

create_result(results, mainfolder)