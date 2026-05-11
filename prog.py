import os
import sqlite3
import csv

main_folder = os.getcwd()
log_path = os.path.join(main_folder, "errors.log")
results = {
    "files": 0,
    "rows": 0,
    "added": 0,
    "duplicates": 0,
    "errors": 0,
    "sqlite.errors": 0
}

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

def empty_check(s):
    for a in range(len(s)-2): #Что бы не проверял external_id
        if not str(s[a]).strip():
            return True
    return False

def create_result(result, folder):
    result_path = os.path.join(folder, "result.log")
    with open(result_path, 'w', encoding='utf-8') as result_file:
        result_file.write("Обработано файлов: " + str(result["files"]) + "\n")
        result_file.write("Всего строк: " + str(result["rows"]) + "\n")
        result_file.write("Добавлено: " + str(result["added"]) + "\n")
        result_file.write("Дублей: " + str(result["duplicates"]) + "\n")
        result_file.write("Ошибок: " + str(result["errors"]) + "\n")
        result_file.write("Ошибок SQLite3: " + str(result["sqlite.errors"]) + "\n")

def get_db():
    conn = sqlite3.connect('payments.db')
    conn.row_factory = sqlite3.Row
    return conn

csv_files = [f for f in os.listdir(os.path.join(main_folder, "tests_csv")) if f.endswith(".csv")]

with open(log_path, 'w', encoding='utf-8') as log_file, get_db() as db:
    db.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        payment_date TEXT,
        source TEXT,
        payer TEXT,
        account_number INTEGER,
        amount REAL,
        external_id TEXT,
        UNIQUE(payment_date, payer, account_number, amount)
    )
    """)

    #Это цикл файлов
    for filename in csv_files:
        results["files"] += 1
        with open(os.path.join(main_folder, "tests_csv", filename), 'r', encoding='utf-8-sig') as file:
            csv_reader = csv.reader(file, delimiter=',')
            row_number = 1

            headers = next(csv_reader)
            column_map = {name: i for i, name in enumerate(headers)}

            #Это цикл строк
            for row in csv_reader:
                temp_array = row

                results["rows"] += 1

                # Это цикл слов
                for j in range(len(temp_array)):
                    temp_array[j] = clean_value(temp_array[j])

                # Почему не сделать просто словарь? Потому что я буквально выше вызываю значения по индексу. Если менять главную переменную здесь на словарь, то придётся переписывать всё под новую логику.
                if empty_check(temp_array):
                    msg = f"[{filename} | строка {row_number}] Отсутствуют критические значения: {temp_array}"
                    log_file.write(msg + "\n")
                    results["errors"] += 1

                elif not check_value(temp_array[column_map["amount"]]):
                    msg = f"[{filename} | строка {row_number}] Неверный тип данных в ячейке: {temp_array[column_map["amount"]]}"
                    log_file.write(msg + "\n")
                    results["errors"] += 1

                else:
                    try:
                        changes_before = db.total_changes
                        db.execute("""
                            INSERT OR IGNORE INTO payments
                            (payment_date, source, payer, account_number, amount, external_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (temp_array[column_map["payment_date"]],
                              temp_array[column_map["source"]],
                              temp_array[column_map["payer"]],
                              temp_array[column_map["account_number"]],
                              temp_array[column_map["amount"]],
                              temp_array[column_map["external_id"]] if "external_id" in column_map else None))

                        if db.total_changes == changes_before:
                            msg = f"[{filename} | строка {row_number}] Дубликат пропущен: {temp_array}"
                            log_file.write(msg + "\n")
                            results["duplicates"] += 1
                            continue

                        results["added"] += 1

                    except sqlite3.Error as e:
                        results["sqlite.errors"] += 1
                        log_file.write(f"[{filename} | строка {row_number}] SQLite ошибка: {e}\n")

                row_number += 1
    db.commit()

create_result(results, main_folder)