# remedy9.py - защита от дублей фото + удаление операций (идемпотентный)
report = []

p1 = "office_db.py"
s1 = open(p1, encoding="utf-8").read()
if "def delete_transaction" not in s1:
    marker = "def inventory_report():"
    funcs = '''def delete_transaction(tx_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT screenshot_path FROM transactions WHERE id=?", (tx_id,))
    row = cur.fetchone()
    if row and row["screenshot_path"]:
        try:
            if os.path.exists(row["screenshot_path"]):
                os.remove(row["screenshot_path"])
        except Exception:
            pass
    cur.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()
    return True

def clear_transactions():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT screenshot_path FROM transactions")
    for row in cur.fetchall():
        try:
            if row["screenshot_path"] and os.path.exists(row["screenshot_path"]):
                os.remove(row["screenshot_path"])
        except Exception:
            pass
    cur.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    return True

'''
    if marker in s1:
        s1 = s1.replace(marker, funcs + marker, 1)
        open(p1, "w", encoding="utf-8").write(s1)
        report.append("ПРАВКА 1: OK - удаление операций добавлено в базу")
    else:
        report.append("ПРАВКА 1: СТОП - не нашёл inventory_report")
else:
    report.append("ПРАВКА 1: уже применена")

p2 = "receipts_ui.py"
s2 = open(p2, encoding="utf-8").read()
if "import hashlib" not in s2:
    s2 = s2.replace("import office_ocr\n", "import office_ocr\nimport hashlib\n", 1)
    report.append("ПРАВКА 2: OK - импорт hashlib")
else:
    report.append("ПРАВКА 2: уже применена")

s2 = s2.replace('            file_key = "saved_" + upl.name + "_" + str(upl.size)\n', '')
start = s2.find("if file_key not in st.session_state:")
end_marker = 'st.info("Файл уже сохранён ранее (не дублируем)")'
end = s2.find(end_marker)
if start >= 0 and end >= 0:
    end = end + len(end_marker)
    new_save = '''            digest = hashlib.md5(upl.getvalue()).hexdigest()[:10]
            safe_name = upl.name.replace(" ", "_")
            fname = digest + "_" + safe_name
            fpath = os.path.join(ACC_DIR, fname)
            if not os.path.exists(fpath):
                with open(fpath, "wb") as f:
                    f.write(upl.getvalue())
                st.success("Файл сохранён: accounting/" + fname)
            else:
                st.info("Такой файл уже есть в accounting (не дублируем)")'''
    s2 = s2[:start] + new_save + s2[end:]
    report.append("ПРАВКА 3: OK - сохранение по отпечатку содержимого")
elif "digest = hashlib.md5" in s2:
    report.append("ПРАВКА 3: уже применена")
else:
    report.append("ПРАВКА 3: СТОП - блок сохранения не найден")

old_loop = '''        for t in txs[:15]:
            sign = "-" if t["type"] == "расход" else "+"
            st.markdown(sign + " **" + str(t["amount"]) + " руб** | " + str(t["date"]) + " | " + str(t["category"]) + " | " + str(t["description"]))'''
new_loop = '''        for t in txs[:15]:
            sign = "-" if t["type"] == "расход" else "+"
            c1, c2 = st.columns([6, 1])
            c1.markdown(sign + " **" + str(t["amount"]) + " руб** | " + str(t["date"]) + " | " + str(t["category"]) + " | " + str(t["description"]))
            if c2.button("🗑 Удалить", key="del" + str(t["id"])):
                db.delete_transaction(t["id"])
                st.rerun()
        if txs:
            conf = st.checkbox("Подтверждаю полную очистку всех операций")
            if st.button("🧹 Удалить ВСЕ операции"):
                if conf:
                    db.clear_transactions()
                    st.success("Все операции удалены")
                    st.rerun()
                else:
                    st.warning("Сначала поставь галочку подтверждения")'''
if old_loop in s2:
    s2 = s2.replace(old_loop, new_loop)
    report.append("ПРАВКА 4: OK - кнопки удаления операций")
elif "Удалить ВСЕ операции" in s2:
    report.append("ПРАВКА 4: уже применена")
else:
    report.append("ПРАВКА 4: СТОП - блок списка операций не найден")

open(p2, "w", encoding="utf-8").write(s2)
print("=== ОТЧЁТ REMEDY9 ===")
for r in report:
    print("  " + r)