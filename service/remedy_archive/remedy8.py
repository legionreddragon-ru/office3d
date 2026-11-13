# remedy8.py - русская шапка CSV и гарантия точки с запятой (идемпотентный)
report = []
p = "receipts_ui.py"
s = open(p, encoding="utf-8").read()

if "дата;тип;категория" in s:
    report.append("ПРАВКА: уже применена")
else:
    start = s.find("csv_lines = [")
    btn = s.find("st.download_button(", start)
    end = s.find("\n", btn)
    if start >= 0 and btn > start and end > btn:
        new_block = '''csv_lines = ["дата;тип;категория;сумма;описание"]
                for t in txs:
                    if t["date"][:7] == msel:
                        safe_desc = str(t["description"]).replace(";", " ").replace(",", " ")
                        amt = str(t["amount"]).replace(".", ",")
                        csv_lines.append(t["date"] + ";" + t["type"] + ";" + t["category"] + ";" + amt + ";" + safe_desc)
                st.download_button("⬇️ Скачать CSV", data="\\ufeff" + "\\n".join(csv_lines), file_name="report_" + msel + ".csv", mime="text/csv")'''
        s = s[:start] + new_block + s[end:]
        open(p, "w", encoding="utf-8").write(s)
        report.append("ПРАВКА: OK - шапка русская, разделитель точка с запятой, BOM на месте")
    else:
        report.append("ПРАВКА: СТОП - блок CSV не найден")

print("=== ОТЧЁТ REMEDY8 ===")
for r in report:
    print("  " + r)