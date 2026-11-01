# remedy12.py - иконка: убрать эмодзи из заголовка + указание автора + CREDITS.md
import os
report = []
p = "office_ui.py"
s = open(p, encoding="utf-8").read()

old_title = 'st.title("🏭 ОФИС-3D — панель управления виртуальным офисом")'
new_title = 'st.title("ОФИС-3D — панель управления виртуальным офисом")'
if old_title in s:
    s = s.replace(old_title, new_title)
    report.append("ПРАВКА 1: OK - эмодзи убран из заголовка")
elif new_title in s:
    report.append("ПРАВКА 1: уже применена")
else:
    report.append("ПРАВКА 1: СТОП - заголовок не найден")

old_sb = 'st.image(_ICON_PATH, width=140)\n        st.markdown("---")'
new_sb = 'st.image(_ICON_PATH, width=140)\n        st.caption("Иконка: Dewi Sari / Flaticon (free license)")\n        st.markdown("---")'
if old_sb in s:
    s = s.replace(old_sb, new_sb)
    report.append("ПРАВКА 2: OK - указание автора в сайдбаре")
elif "Dewi Sari" in s:
    report.append("ПРАВКА 2: уже применена")
else:
    report.append("ПРАВКА 2: СТОП - блок сайдбара не найден")

open(p, "w", encoding="utf-8").write(s)

if not os.path.exists("CREDITS.md"):
    with open("CREDITS.md", "w", encoding="utf-8") as f:
        f.write("# CREDITS (указания авторства бесплатных материалов)\n\n")
        f.write("## Иконки\n")
        f.write("- Иконка офиса (3D-принтер): автор Dewi Sari, источник Flaticon, бесплатная лицензия с указанием авторства.\n")
        f.write("  Ссылка: https://www.flaticon.com/free-icons/3d-printer\n")
        f.write("  Где используется: интерфейс офиса (вкладка браузера и сайдбар), ярлык на рабочем столе, будущие инструкции для клиентов.\n")
    report.append("ПРАВКА 3: OK - CREDITS.md создан")
else:
    report.append("ПРАВКА 3: CREDITS.md уже есть")

print("=== ОТЧЁТ REMEDY12 ===")
for r in report:
    print("  " + r)