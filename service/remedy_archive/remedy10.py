# remedy10.py - подключение fairs_ui + миграция + напоминания при старте
report = []
p = "office_ui.py"
s = open(p, encoding="utf-8").read()

if "import fairs_ui" not in s:
    if "import receipts_ui\n" in s:
        s = s.replace("import receipts_ui\n", "import receipts_ui\nimport fairs_ui\n", 1)
        report.append("ПРАВКА 1: OK - импорт fairs_ui")
    else:
        report.append("ПРАВКА 1: СТОП - не нашёл import receipts_ui")
else:
    report.append("ПРАВКА 1: уже применена")

old_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры", "🧾 Чеки и Финансы"])'
new_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры", "🧾 Чеки и Финансы", "🎪 Ярмарки"])'
if old_tabs in s:
    s = s.replace(old_tabs, new_tabs)
    report.append("ПРАВКА 2: OK - 8-я вкладка")
elif new_tabs in s:
    report.append("ПРАВКА 2: уже применена")
else:
    report.append("ПРАВКА 2: СТОП - строка вкладок не найдена")

if "fairs_ui.render()" not in s:
    s = s.rstrip() + "\n\nwith tab8:\n    fairs_ui.render()\n"
    report.append("ПРАВКА 3: OK - рендер fairs_ui")
else:
    report.append("ПРАВКА 3: уже применена")

migrate_block = """
try:
    import office_db as _db
    _db.init_db()
    _db.migrate_db()
    _pending = _db.pending_reminders(7)
    if _pending:
        import streamlit as _st
        for _r in _pending:
            _st.warning("🔔 Напоминание на " + str(_r["date"]) + ": " + str(_r["text"]))
except Exception as _e:
    pass
"""
if "migrate_db()" not in s:
    if "import office\n" in s:
        s = s.replace("import office\n", "import office\n" + migrate_block, 1)
        report.append("ПРАВКА 4: OK - миграция + напоминания при старте")
    else:
        report.append("ПРАВКА 4: СТОП - не нашёл import office")
else:
    report.append("ПРАВКА 4: уже применена")

open(p, "w", encoding="utf-8").write(s)
print("=== ОТЧЁТ REMEDY10 ===")
for r in report:
    print("  " + r)