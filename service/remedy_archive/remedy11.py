# remedy11.py - подключает вкладку Диагностика
report = []
p = "office_ui.py"
s = open(p, encoding="utf-8").read()

if "import health_ui" not in s:
    if "import fairs_ui\n" in s:
        s = s.replace("import fairs_ui\n", "import fairs_ui\nimport health_ui\n", 1)
        report.append("ПРАВКА 1: OK - импорт health_ui")
    else:
        report.append("ПРАВКА 1: СТОП - не нашёл import fairs_ui")
else:
    report.append("ПРАВКА 1: уже применена")

old_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры", "🧾 Чеки и Финансы", "🎪 Ярмарки"])'
new_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры", "🧾 Чеки и Финансы", "🎪 Ярмарки", "🩺 Диагностика"])'
if old_tabs in s:
    s = s.replace(old_tabs, new_tabs)
    report.append("ПРАВКА 2: OK - 9-я вкладка")
elif new_tabs in s:
    report.append("ПРАВКА 2: уже применена")
else:
    report.append("ПРАВКА 2: СТОП - строка вкладок не найдена")

if "health_ui.render()" not in s:
    s = s.rstrip() + "\n\nwith tab9:\n    health_ui.render()\n"
    report.append("ПРАВКА 3: OK - рендер диагностики")
else:
    report.append("ПРАВКА 3: уже применена")

open(p, "w", encoding="utf-8").write(s)
print("=== ОТЧЁТ REMEDY11 ===")
for r in report:
    print("  " + r)