# checkall.py - глобальная проверка офиса (расширяется со временем)
import os, sys, json, subprocess, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
OK, WARN, FAIL = "OK", "WARN", "FAIL"
results = []

def check(name, fn):
    try:
        status, msg = fn()
        results.append((name, status, msg))
    except Exception as e:
        results.append((name, FAIL, str(e)[:120]))

# === 1. Автотест 10/10 ===
def c_autotest():
    r = subprocess.run([sys.executable, "autotest.py"], capture_output=True, text=True)
    if r.returncode == 0:
        for line in r.stdout.splitlines():
            if "ITOG:" in line:
                return OK, line.strip()
        return OK, "autotest 10/10"
    return FAIL, "autotest упал"

# === 2. Синтаксис всех ключевых файлов ===
def c_syntax():
    files = ["office.py","office_ui.py","office_db.py","office_ocr.py",
             "warehouse_ui.py","receipts_ui.py","fairs_ui.py","health_ui.py"]
    bad = []
    for f in files:
        if not os.path.exists(f):
            bad.append(f + " (нет)")
            continue
        r = subprocess.run([sys.executable, "-m", "py_compile", f], capture_output=True)
        if r.returncode != 0:
            bad.append(f)
    if not bad:
        return OK, "синтаксис всех " + str(len(files)) + " файлов чист"
    return FAIL, "ошибки в: " + ", ".join(bad)

# === 3. Целостность базы ===
def c_db_integrity():
    import sqlite3
    db_path = os.path.join(BASE, "office.db")
    if not os.path.exists(db_path):
        return FAIL, "office.db не существует"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    res = cur.fetchone()[0]
    conn.close()
    if str(res) == "ok":
        return OK, "SQLite PRAGMA integrity_check: ok"
    return FAIL, "SQLite повреждена: " + str(res)

# === 4. Секреты на месте ===
def c_env():
    p = os.path.join(BASE, ".env")
    if not os.path.exists(p):
        return FAIL, "нет файла .env"
    txt = open(p, encoding="utf-8").read()
    if "TELEGRAM_BOT_TOKEN" in txt:
        return OK, ".env содержит токен"
    return WARN, ".env есть, но токена пока нет"

# === 5. .gitignore защищает office.db ===
def c_gitignore():
    p = os.path.join(BASE, ".gitignore")
    if not os.path.exists(p):
        return FAIL, "нет .gitignore"
    txt = open(p, encoding="utf-8").read().lower()
    if "office.db" in txt and ".env" in txt:
        return OK, ".gitignore защищает office.db и .env"
    return FAIL, ".gitignore не защищает секреты"

# === 6. office.db не отслеживается git ===
def c_git_db():
    r = subprocess.run(["git", "ls-files", "office.db"], capture_output=True, text=True)
    if r.stdout.strip() == "":
        return OK, "office.db НЕ в git"
    return FAIL, "office.db ВСЁ ЕЩЁ в git!"

# === 7. Последний бэкап свежий ===
def c_backup():
    bd = os.path.join(BASE, "backups")
    if not os.path.isdir(bd):
        return WARN, "папки backups нет (запусти backup.bat)"
    files = [f for f in os.listdir(bd) if f.startswith("office3d_") and f.endswith(".zip")]
    if not files:
        return WARN, "бэкапов нет (запусти backup.bat)"
    files.sort(reverse=True)
    fp = os.path.join(bd, files[0])
    size_kb = os.path.getsize(fp) / 1024
    age_days = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(fp))).days
    if size_kb < 50:
        return FAIL, "последний бэкап подозрительно мал (" + str(int(size_kb)) + " КБ)"
    if age_days > 7:
        return WARN, "последний бэкап " + str(age_days) + " дн. назад (" + files[0] + ")"
    return OK, "бэкап свежий: " + files[0] + " (" + str(int(size_kb)) + " КБ, " + str(age_days) + " дн.)"

# === 8. Ollama запущена ===
def c_ollama():
    try:
        import urllib.request
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        if r.status == 200:
            return OK, "Ollama отвечает"
    except Exception:
        return FAIL, "Ollama не отвечает (запусти)"
    return FAIL, "Ollama недоступна"

# === 9. Сиротские фото ===
def c_orphans():
    acc = os.path.join(BASE, "accounting")
    if not os.path.isdir(acc):
        return OK, "accounting пуста"
    import office_db as db
    db.init_db()
    linked = set(t["screenshot_path"] for t in db.list_transactions() if t["screenshot_path"])
    orphans = [f for f in os.listdir(acc) if os.path.join(acc, f) not in linked]
    if not orphans:
        return OK, "сиротских фото нет"
    return WARN, "сиротских фото: " + str(len(orphans)) + " (кнопка очистки в Чеках)"

# === 10. Иконка Flaticon на месте ===
def c_icon():
    p = os.path.join(BASE, "assets", "icon.png")
    cr = os.path.join(BASE, "CREDITS.md")
    if not os.path.exists(p):
        return WARN, "нет assets/icon.png"
    if not os.path.exists(cr):
        return WARN, "нет CREDITS.md"
    txt = open(cr, encoding="utf-8").read()
    if "Dewi Sari" in txt and "Flaticon" in txt:
        return OK, "иконка + CREDITS.md (Dewi Sari / Flaticon)"
    return WARN, "CREDITS.md без атрибуции"

# === 11. Мини-тесты ===
def c_mini_tests():
    tests = ["test_fair_reminders.py", "test_health.py"]
    bad = []
    for t in tests:
        if not os.path.exists(t):
            continue
        r = subprocess.run([sys.executable, t], capture_output=True, text=True)
        if r.returncode != 0:
            bad.append(t)
    if not bad:
        return OK, "мини-тесты прошли"
    return FAIL, "мини-тесты упали: " + ", ".join(bad)

def main():
    print("")
    print("=" * 60)
    print("   ГЛОБАЛЬНАЯ ПРОВЕРКА ОФИСА-3D")
    print("=" * 60)
    print("")
    check("1. Автотест (математика+UI)", c_autotest)
    check("2. Синтаксис ключевых файлов", c_syntax)
    check("3. Целостность SQLite", c_db_integrity)
    check("4. Файл .env", c_env)
    check("5. .gitignore защищает секреты", c_gitignore)
    check("6. office.db НЕ в git", c_git_db)
    check("7. Последний бэкап", c_backup)
    check("8. Ollama", c_ollama)
    check("9. Сиротские фото", c_orphans)
    check("10. Иконка Flaticon", c_icon)
    check("11. Мини-тесты", c_mini_tests)
    fails = sum(1 for _, s, _ in results if s == FAIL)
    warns = sum(1 for _, s, _ in results if s == WARN)
    oks = sum(1 for _, s, _ in results if s == OK)
    print("")
    for name, s, msg in results:
        icon = {"OK":"✅", "WARN":"⚠️", "FAIL":"❌"}[s]
        print("  " + icon + " " + name + " — " + msg)
    print("")
    print("-" * 60)
    if fails == 0 and warns == 0:
        print("  🏆 ИТОГ: ОФИС ЗДОРОВ (" + str(oks) + "/" + str(len(results)) + " OK)")
    elif fails == 0:
        print("  ⚠️  ИТОГ: РАБОТАЕТ, но есть " + str(warns) + " предупреждений")
    else:
        print("  ❌ ИТОГ: " + str(fails) + " ошибок, " + str(warns) + " предупреждений")
    print("-" * 60)
    print("")
    input("  Нажми Enter чтобы закрыть...")
    if fails > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()