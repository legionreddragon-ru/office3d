# remedy5.py - чинит office.py и подключает вкладку Склад
report = []

p1 = "office.py"
s1 = open(p1, encoding="utf-8").read()
old_line = r'if low.count("\sum") > 2 or low.count("\frac") > 2:'
new_line = r'if low.count("\\sum") > 2 or low.count("\\frac") > 2:'
if old_line in s1:
    s1 = s1.replace(old_line, new_line)
    open(p1, "w", encoding="utf-8").write(s1)
    report.append("ПРАВКА 1: OK - office.py исправлен")
elif new_line in s1:
    report.append("ПРАВКА 1: уже применена")
else:
    report.append("ПРАВКА 1: СТОП - строка не найдена")

p2 = "office_ui.py"
s2 = open(p2, encoding="utf-8").read()
if "import warehouse_ui" not in s2:
    if "import office\n" in s2:
        s2 = s2.replace("import office\n", "import office\nimport warehouse_ui\n", 1)
        report.append("ПРАВКА 2: OK - импорт добавлен")
    else:
        report.append("ПРАВКА 2: СТОП - не нашёл import office")
else:
    report.append("ПРАВКА 2: уже применена")

old_tabs = 'tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База"])'
new_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры"])'
if old_tabs in s2:
    s2 = s2.replace(old_tabs, new_tabs)
    report.append("ПРАВКА 3: OK - шестая вкладка добавлена")
elif new_tabs in s2:
    report.append("ПРАВКА 3: уже применена")
else:
    report.append("ПРАВКА 3: СТОП - строка вкладок не найдена")

if "warehouse_ui.render()" not in s2:
    s2 = s2.rstrip() + "\n\nwith tab6:\n    warehouse_ui.render()\n"
    report.append("ПРАВКА 4: OK - вызов вкладки добавлен в конец")
else:
    report.append("ПРАВКА 4: уже применена")

open(p2, "w", encoding="utf-8").write(s2)
print("=== ОТЧЁТ REMEDY5 ===")
for r in report:
    print("  " + r)