# office_db.py - база данных офиса (SQLite)
import sqlite3
import os
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "office.db")

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS printers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        model TEXT,
        nozzle_diameter REAL,
        bed_size TEXT,
        materials TEXT,
        purchase_date TEXT,
        purchase_price REAL,
        resource_hours INTEGER,
        used_hours REAL DEFAULT 0,
        location TEXT,
        status TEXT DEFAULT 'active',
        notes TEXT,
        created_at TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS plastic_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        material TEXT NOT NULL,
        color TEXT,
        weight_grams INTEGER NOT NULL,
        min_weight INTEGER DEFAULT 200,
        location TEXT,
        supplier TEXT,
        printer_id INTEGER,
        purchase_date TEXT,
        created_at TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS finished_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity INTEGER DEFAULT 0,
        material TEXT,
        weight_grams INTEGER,
        cost REAL,
        price REAL,
        location TEXT,
        printer_id INTEGER,
        created_at TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS print_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        printer_id INTEGER,
        plastic_id INTEGER,
        material TEXT,
        weight_used INTEGER,
        purpose TEXT,
        result TEXT,
        photo_path TEXT,
        notes TEXT,
        created_at TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        type TEXT,
        category TEXT,
        amount REAL,
        description TEXT,
        screenshot_path TEXT,
        fair_id INTEGER,
        created_at TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS fairs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT,
        name TEXT,
        location TEXT,
        cost REAL,
        revenue REAL,
        items_sold TEXT,
        notes TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()
    return True

def add_printer(name, model, nozzle, bed, materials, price, resource, location):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO printers (name, model, nozzle_diameter, bed_size, materials, purchase_price, resource_hours, location, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (name, model, nozzle, bed, materials, price, resource, location, now_str()))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def list_printers():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM printers ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def add_printer_hours(printer_id, hours):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE printers SET used_hours = used_hours + ? WHERE id=?", (hours, printer_id))
    conn.commit()
    conn.close()
    return True

def add_plastic(material, color, weight, min_weight, location, supplier, printer_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO plastic_stock (material, color, weight_grams, min_weight, location, supplier, printer_id, purchase_date, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (material, color, weight, min_weight, location, supplier, printer_id, now_str()[:10], now_str()))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def list_plastic():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM plastic_stock ORDER BY material, color")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def use_plastic(plastic_id, grams, purpose, printer_id, result, notes):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT weight_grams, material FROM plastic_stock WHERE id=?", (plastic_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        return False, "пластик не найден"
    if row["weight_grams"] < grams:
        conn.close()
        return False, "недостаточно пластика на складе"
    cur.execute("UPDATE plastic_stock SET weight_grams = weight_grams - ? WHERE id=?", (grams, plastic_id))
    cur.execute(
        "INSERT INTO print_tests (date, printer_id, plastic_id, material, weight_used, purpose, result, notes, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (now_str()[:10], printer_id, plastic_id, row["material"], grams, purpose, result, notes, now_str()))
    conn.commit()
    conn.close()
    return True, "списано " + str(grams) + " г"

def add_product(name, qty, material, weight, cost, price, location, printer_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO finished_products (name, quantity, material, weight_grams, cost, price, location, printer_id, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (name, qty, material, weight, cost, price, location, printer_id, now_str()))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def list_products():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM finished_products ORDER BY name")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def add_transaction(ttype, category, amount, description, screenshot_path):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO transactions (date, type, category, amount, description, screenshot_path, created_at) VALUES (?,?,?,?,?,?,?)",
        (now_str()[:10], ttype, category, amount, description, screenshot_path, now_str()))
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid

def list_transactions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM transactions ORDER BY date DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def delete_transaction(tx_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT screenshot_path FROM transactions WHERE id=?", (tx_id,))
    row = cur.fetchone()
    if row and row["screenshot_path"]:
        try:
            if os.path.exists(row["screenshot_path"]):
                os.remove(row["screenshot_path"])
        except Exception:
            pass
    cur.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return True

def clear_transactions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT screenshot_path FROM transactions")
    for row in cur.fetchall():
        try:
            if row["screenshot_path"] and os.path.exists(row["screenshot_path"]):
                os.remove(row["screenshot_path"])
        except Exception:
            pass
    cur.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    return True

def inventory_report():
    conn = get_conn()
    cur = conn.cursor()
    report = {}
    cur.execute("SELECT material, color, SUM(weight_grams) AS total FROM plastic_stock GROUP BY material, color")
    report["plastic"] = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT name, SUM(quantity) AS qty FROM finished_products GROUP BY name")
    report["products"] = [dict(r) for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) AS n, SUM(weight_used) AS w FROM print_tests")
    row = cur.fetchone()
    report["tests_count"] = row["n"]
    report["tests_weight"] = row["w"]
    conn.close()
    return report

if __name__ == "__main__":
    init_db()
    print("БАЗА СОЗДАНА:", DB_PATH)
    pid = add_printer("Основной", "Bambu Lab P1S Combo", 0.4, "256x256x256", "PLA,PETG,ABS", 68300, 4500, "кабинет")
    print("Добавлен принтер id:", pid)
    plid = add_plastic("PETG", "красный", 1000, 200, "шкаф А", "Ozon", pid)
    print("Добавлен пластик id:", plid)
    ok, msg = use_plastic(plid, 75, "test", pid, "sample", "пробник дракона")
    print("Списание:", ok, msg)
    rep = inventory_report()
    print("ИНВЕНТАРИЗАЦИЯ:", rep)

def delete_transaction(tx_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT screenshot_path FROM transactions WHERE id=?", (tx_id,))
    row = cur.fetchone()
    if row and row["screenshot_path"]:
        try:
            if os.path.exists(row["screenshot_path"]):
                os.remove(row["screenshot_path"])
        except Exception:
            pass
    cur.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return True

def clear_transactions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT screenshot_path FROM transactions")
    for row in cur.fetchall():
        try:
            if row["screenshot_path"] and os.path.exists(row["screenshot_path"]):
                os.remove(row["screenshot_path"])
        except Exception:
            pass
    cur.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    return True