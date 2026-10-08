# remedy7.py - чинит CSV под русский Excel (точка с запятой + BOM)
report = []
p = "receipts_ui.py"
s = open(p, encoding="utf-8").read()

old_block = '''                csv_lines = ["date,type,category,amount,description"]
                for t in txs:
                    if t["date"][:7] == msel:
                        csv_lines.append(t["date"] + "," + t["type"] + "," + t["category"] + "," + str(t["amount"]) + "," + str(t["description"]).replace(",", ";"))
                st.download_button("⬇️ Скачать CSV", data="\\n".join(csv_lines), file_name="report_" + msel + ".csv", mime="text/csv")'''

new_block = '''                csv_lines = ["date;type;category;amount;description"]
                for t in txs:
                    if t["date"][:7] == msel:
                        safe_desc = str(t["description"]).replace(";", " ").replace(",", " ")
                        amt = str(t["amount"]).replace(".", ",")
                        csv_lines.append(t["date"] + ";" + t["type"] + ";" + t["category"] + ";" + amt + ";" + safe_desc)
                st.download_button("⬇️ Скачать CSV", data="\\ufeff" + "\\n".join(csv_lines), file_name="report_" + msel + ".csv", mime="text/csv")'''

if old_block in s:
    s = s.replace(old_block, new_block)
    open(p, "w", encoding="utf-8").write(s)
    report.append("ПРАВКА: OK - CSV теперь с точкой с запятой и BOM")
elif "date;type;category" in s:
    report.append("ПРАВКА: уже применена")
else:
    report.append("ПРАВКА: СТОП - блок не найден")

print("=== ОТЧЁТ REMEDY7 ===")
for r in report:
    print("  " + r)