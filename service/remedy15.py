# remedy15.py - подключает вкладку Сервис
report = []
p = "office_ui.py"
s = open(p, encoding="utf-8").read()

if "import service_ui" not in s:
    if "import health_ui\n" in s:
        s = s.replace("import health_ui\n", "import health_ui\nimport service_ui\n", 1)
        report.append("ПРАВКА 1: OK - импорт service_ui")
    else:
        report.append("ПРАВКА 1: СТОП - не нашёл import health_ui")
else:
    report.append("ПРАВКА 1: уже применена")

old_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры", "🧾 Чеки и Финансы", "🎪 Ярмарки", "🩺 Диагностика"])'
new_tabs = 'tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База", "🏭 Склад и Принтеры", "🧾 Чеки и Финансы", "🎪 Ярмарки", "🩺 Диагностика", "🔧 Сервис"])'
if old_tabs in s:
    s = s.replace(old_tabs, new_tabs)
    report.append("ПРАВКА 2: OK - 10-я вкладка")
elif new_tabs in s:
    report.append("ПРАВКА 2: уже применена")
else:
    report.append("ПРАВКА 2: СТОП - строка вкладок не найдена")

if "service_ui.render()" not in s:
    s = s.rstrip() + "\n\nwith tab10:\n    service_ui.render()\n"
    report.append("ПРАВКА 3: OK - рендер Сервиса")
else:
    report.append("ПРАВКА 3: уже применена")

open(p, "w", encoding="utf-8").write(s)
print("=== ОТЧЁТ REMEDY15 ===")
for r in report:
    print("  " + r)