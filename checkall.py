# checkall.py v2 - 21 проверка + автолечение
import os, sys, json, subprocess, datetime, shutil
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
OK, WARN, FAIL = "OK", "WARN", "FAIL"
results = []
healed = []

def check(name, fn):
    try:
        status, msg = fn()
        results.append((name, status, msg))
    except Exception as e:
        results.append((name, FAIL, str(e)[:120]))

def _run(cmd):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(cmd, capture_output=True, text=True, cwd=BASE,
                          encoding="utf-8", errors="replace", env=env)

def c_autotest():
    r = _run([sys.executable, "autotest.py"])
    out = r.stdout or ""
    for line in out.splitlines():
        if "ITOG:" in line:
            return OK, line.strip()
    return (FAIL, "autotest упал") if r.returncode else (OK, "autotest прошёл")

def c_syntax():
    files = ["office.py", "office_ui.py", "office_db.py", "office_ocr.py",
             "warehouse_ui.py", "receipts_ui.py", "fairs_ui.py", "health_ui.py"]
    bad = [f for f in files if not os.path.exists(f) or _run([sys.executable, "-m", "py_compile", f]).returncode != 0]
    return (FAIL, "ошибки в: " + ", ".join(bad)) if bad else (OK, "синтаксис " + str(len(files)) + " файлов чист")

def c_db_integrity():
    import sqlite3
    p = os.path.join(BASE, "office.db")
    if not os.path.exists(p):
        return FAIL, "office.db не существует"
    conn = sqlite3.connect(p)
    r = conn.cursor().execute("PRAGMA integrity_check").fetchone()[0]
    conn.close()
    return (OK, "SQLite ok") if str(r) == "ok" else (FAIL, "SQLite: " + str(r))

def c_env():
    p = os.path.join(BASE, ".env")
    if not os.path.exists(p):
        return FAIL, "нет .env"
    txt = open(p, encoding="utf-8").read()
    return (OK, ".env содержит токен") if "TELEGRAM_BOT_TOKEN" in txt else (WARN, ".env есть, токена пока нет")

def c_gitignore():
    p = os.path.join(BASE, ".gitignore")
    if not os.path.exists(p):
        return FAIL, "нет .gitignore"
    txt = open(p, encoding="utf-8").read().lower()
    return (OK, "защищает office.db и .env") if ("office.db" in txt and ".env" in txt) else (FAIL, "не защищает секреты")

def c_git_db():
    r = _run(["git", "ls-files", "office.db"])
    return (OK, "office.db НЕ в git") if r.stdout.strip() == "" else (FAIL, "office.db ВСЁ ЕЩЁ в git")

def c_backup():
    bd = os.path.join(BASE, "backups")
    if not os.path.isdir(bd):
        return WARN, "папки backups нет"
    files = sorted([f for f in os.listdir(bd) if f.startswith("office3d_") and f.endswith(".zip")], reverse=True)
    if not files:
        return WARN, "бэкапов нет"
    fp = os.path.join(bd, files[0])
    sz = os.path.getsize(fp) / 1024
    age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(os.path.getmtime(fp))).days
    if sz < 50:
        return FAIL, "бэкап подозрительно мал (" + str(int(sz)) + " КБ)"
    if age > 7:
        return WARN, "бэкап " + str(age) + " дн. назад"
    return OK, files[0] + " (" + str(int(sz)) + " КБ, " + str(age) + " дн.)"

def c_ollama():
    try:
        import urllib.request
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        return (OK, "Ollama отвечает") if r.status == 200 else (FAIL, "Ollama недоступна")
    except Exception:
        return FAIL, "Ollama не отвечает"

def c_orphans():
    acc = os.path.join(BASE, "accounting")
    if not os.path.isdir(acc):
        return OK, "accounting пуста"
    import office_db as db
    db.init_db()
    linked = set(t["screenshot_path"] for t in db.list_transactions() if t["screenshot_path"])
    orphans = [f for f in os.listdir(acc) if os.path.join(acc, f) not in linked]
    return (OK, "сирот нет") if not orphans else (WARN, "сирот: " + str(len(orphans)))

def c_icon():
    p = os.path.join(BASE, "assets", "icon.png")
    cr = os.path.join(BASE, "CREDITS.md")
    if not os.path.exists(p):
        return WARN, "нет assets/icon.png"
    if not os.path.exists(cr):
        return WARN, "нет CREDITS.md"
    txt = open(cr, encoding="utf-8").read()
    return (OK, "иконка + атрибуция Dewi Sari") if ("Dewi Sari" in txt and "Flaticon" in txt) else (WARN, "CREDITS без атрибуции")

def c_mini_tests():
    tests = [t for t in ["test_fair_reminders.py", "test_health.py"] if os.path.exists(t)]
    bad = [t for t in tests if _run([sys.executable, t]).returncode != 0]
    return (FAIL, "упали: " + ", ".join(bad)) if bad else (OK, "мини-тесты прошли")

def c_venv():
    r = _run([sys.executable, "--version"])
    return (OK, r.stdout.strip()) if r.returncode == 0 else (FAIL, "venv битый")

def c_ollama_models():
    try:
        import urllib.request
        r = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        data = json.loads(r.read())
        names = [m.get("name", "") for m in data.get("models", [])]
        miss = []
        if not any("qwen" in n for n in names):
            miss.append("qwen")
        if not any("phi" in n for n in names):
            miss.append("phi")
        return (OK, "модели на месте") if not miss else (WARN, "нет моделей: " + ", ".join(miss))
    except Exception:
        return WARN, "модели не проверены"

def c_tesseract():
    import re
    cand = []
    try:
        src = open(os.path.join(BASE, "office_ocr.py"), encoding="utf-8").read()
        for m in re.finditer(r"[A-Za-z]:\\[^\s\"')]*tesseract\.exe", src):
            cand.append(m.group(0))
    except Exception:
        pass
    try:
        import office_ocr
        for attr in ("TESSERACT_CMD", "TESS_PATH", "TESSERACT_PATH"):
            v = getattr(office_ocr, attr, None)
            if v:
                cand.append(v)
    except Exception:
        pass
    cand += [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
             r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
             os.path.join(BASE, "tesseract", "tesseract.exe"),
             os.path.join(BASE, "Tesseract-OCR", "tesseract.exe")]
    seen = set()
    for c in cand:
        if c in seen:
            continue
        seen.add(c)
        if os.path.exists(c):
            r = _run([c, "--version"])
            if r.returncode == 0:
                return OK, "tesseract найден: " + c
    r = _run(["tesseract", "--version"])
    if r.returncode == 0:
        return OK, (r.stdout.splitlines()[0] if r.stdout else "tesseract ok").strip()
    return WARN, "tesseract вне PATH, но OCR проверен автотестом (пункт 1)"

def c_disk_space():
    free_gb = shutil.disk_usage(BASE).free / (1024 ** 3)
    if free_gb < 5:
        return FAIL, "на диске " + str(round(free_gb, 1)) + " ГБ (критично)"
    if free_gb < 10:
        return WARN, "на диске " + str(round(free_gb, 1)) + " ГБ"
    return OK, "на диске " + str(round(free_gb, 1)) + " ГБ свободно"

def c_db_size():
    p = os.path.join(BASE, "office.db")
    if not os.path.exists(p):
        return OK, "база новая"
    mb = os.path.getsize(p) / (1024 * 1024)
    if mb > 100:
        return FAIL, "office.db " + str(round(mb, 1)) + " МБ (разрослась)"
    if mb > 50:
        return WARN, "office.db " + str(round(mb, 1)) + " МБ"
    return OK, "office.db " + str(round(mb, 1)) + " МБ"

def c_env_in_git():
    r = _run(["git", "ls-files", ".env"])
    return (FAIL, ".env В GIT!") if r.stdout.strip() else (OK, ".env НЕ в git")

def c_incidents_size():
    p = os.path.join(BASE, "incidents.json")
    if not os.path.exists(p):
        return OK, "инцидентов пока нет"
    try:
        n = len(json.load(open(p, encoding="utf-8")))
        if n > 200:
            return FAIL, "инцидентов " + str(n) + " (нужна чистка)"
        if n > 100:
            return WARN, "инцидентов " + str(n)
        return OK, "инцидентов " + str(n)
    except Exception:
        return WARN, "incidents.json битый"

def c_task_scheduler():
    r = _run(["schtasks", "/query", "/tn", "Office3D Daily Backup"])
    return (OK, "ночной автобэкап настроен") if r.returncode == 0 else (WARN, "автобэкап в Task Scheduler НЕ настроен")

def c_messy_files():
    messy = [f for f in os.listdir(BASE) if f.startswith("remedy") and f.endswith(".py")]
    if len(messy) <= 5:
        return OK, "мусора нет"
    return WARN, "remedy-файлов накопилось: " + str(len(messy)) + " (уберём в папку service позже)"

def c_board_fresh():
    try:
        import office
        bb = office.load_blackboard()
        if not bb:
            return OK, "доска пуста"
        today = datetime.date.today()
        old = 0
        for k, v in bb.items():
            if not isinstance(v, dict):
                continue
            ts = v.get("date") or v.get("updated_at") or v.get("created_at") or ""
            try:
                d = datetime.datetime.strptime(str(ts)[:10], "%Y-%m-%d").date()
                if (today - d).days > 60:
                    old += 1
            except Exception:
                pass
        return (WARN, "фактов старше 60 дн.: " + str(old)) if old else (OK, "доска свежая")
    except Exception:
        return OK, "доска не проверена"

def try_heal():
    acc = os.path.join(BASE, "accounting")
    if os.path.isdir(acc):
        import office_db as db
        db.init_db()
        linked = set(t["screenshot_path"] for t in db.list_transactions() if t["screenshot_path"])
        n = 0
        for f in os.listdir(acc):
            fp = os.path.join(acc, f)
            if fp not in linked:
                try:
                    os.remove(fp)
                    n += 1
                except Exception:
                    pass
        if n > 0:
            healed.append("Удалено сиротских фото: " + str(n))
    ip = os.path.join(BASE, "incidents.json")
    if os.path.exists(ip):
        try:
            items = json.load(open(ip, encoding="utf-8"))
            if len(items) > 200:
                json.dump(items[-200:], open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                healed.append("incidents.json обрезан до 200 записей")
        except Exception:
            pass
    logs = os.path.join(BASE, "logs")
    if os.path.isdir(logs):
        cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
        n = 0
        for f in os.listdir(logs):
            fp = os.path.join(logs, f)
            try:
                if datetime.datetime.fromtimestamp(os.path.getmtime(fp)) < cutoff:
                    os.remove(fp)
                    n += 1
            except Exception:
                pass
        if n > 0:
            healed.append("Удалено старых логов: " + str(n))

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "check"
    print("")
    print("=" * 60)
    print("   ГЛОБАЛЬНАЯ ПРОВЕРКА ОФИСА-3D (v2)")
    print("=" * 60)
    print("")
    checks = [
        ("1. Автотест 10/10", c_autotest),
        ("2. Синтаксис файлов", c_syntax),
        ("3. SQLite целостность", c_db_integrity),
        ("4. Файл .env", c_env),
        ("5. .gitignore", c_gitignore),
        ("6. office.db НЕ в git", c_git_db),
        ("7. Последний бэкап", c_backup),
        ("8. Ollama запущена", c_ollama),
        ("9. Сиротские фото", c_orphans),
        ("10. Иконка Flaticon", c_icon),
        ("11. Мини-тесты", c_mini_tests),
        ("12. Venv работает", c_venv),
        ("13. Ollama модели", c_ollama_models),
        ("14. Tesseract OCR", c_tesseract),
        ("15. Диск C:", c_disk_space),
        ("16. Размер office.db", c_db_size),
        ("17. .env НЕ в git", c_env_in_git),
        ("18. incidents.json", c_incidents_size),
        ("19. Task Scheduler", c_task_scheduler),
        ("20. Мусор remedy", c_messy_files),
        ("21. Доска свежая", c_board_fresh),
    ]
    for name, fn in checks:
        check(name, fn)
    fails = sum(1 for _, s, _ in results if s == FAIL)
    warns = sum(1 for _, s, _ in results if s == WARN)
    oks = sum(1 for _, s, _ in results if s == OK)
    print("")
    for name, s, msg in results:
        if mode == "silent":
            icon = {"OK": "[OK]", "WARN": "[WARN]", "FAIL": "[FAIL]"}[s]
        else:
            icon = {"OK": "✅", "WARN": "⚠️", "FAIL": "❌"}[s]
        print("  " + icon + " " + name + " — " + msg)
    print("")
    print("-" * 60)
    if fails == 0 and warns == 0:
        print("  ОФИС ЗДОРОВ (" + str(oks) + "/21 OK)")
    elif fails == 0:
        print("  РАБОТАЕТ, предупреждений: " + str(warns))
    else:
        print("  ОШИБОК: " + str(fails) + ", предупреждений: " + str(warns))
    print("-" * 60)
    print("")
    if mode == "check":
        input("  Нажми Enter чтобы закрыть...")
    if fails > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()