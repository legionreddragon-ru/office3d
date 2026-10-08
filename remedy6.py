# remedy6.py - подключает вкладку Чеки и Финансы
report = []
p2 = "office_ui.py"
s2 = open(p2, encoding="utf-8").read()

if "import receipts_ui" not in s2:
    if "import warehouse_ui\n" in s2:
        s2 = s2.replace("import warehouse_ui\n", "import warehouse_ui\nimport receipts_ui\n", 1)
        report.append("ПРАВКА 1: OK - импорт receipts_ui")
    else:
        report.append("ПРАВКА 1: СТОП - не нашёл import warehouse_ui")
else:
    report.append("ПРАВКА 1: уже применена")

old_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры"])'
new_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры", "🧾 Чеки и Финансы"])'
if old_tabs in s2:
    s2 = s2.replace(old_tabs, new_tabs)
    report.append("ПРАВКА 2: OK - седьмая вкладка")
elif new_tabs in s2:
    report.append("ПРАВКА 2: уже применена")
else:
    report.append("ПРАВКА 2: СТОП - строка вкладок не найдена")

if "receipts_ui.render()" not in s2:
    s2 = s2.rstrip() + "\n\nwith tab7:\n    receipts_ui.render()\n"
    report.append("ПРАВКА 3: OK - вызов вкладки добавлен")
else:
    report.append("ПРАВКА 3: уже применена")

open(p2, "w", encoding="utf-8").write(s2)
print("=== ОТЧЁТ REMEDY6 ===")
for r in report:
    print("  " + r)