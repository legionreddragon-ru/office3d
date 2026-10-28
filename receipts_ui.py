# receipts_ui.py v7 - Чеки и Финансы (очистка загрузчика через смену ключа)
import streamlit as st
import os
import hashlib
import office_db as db
import office_ocr

BASE = os.path.dirname(os.path.abspath(__file__))
ACC_DIR = os.path.join(BASE, "accounting")

def render():
    os.makedirs(ACC_DIR, exist_ok=True)
    db.init_db()
    if "upload_counter" not in st.session_state:
        st.session_state["upload_counter"] = 0

    st.subheader("🧾 Чеки и Финансы")

    if "flash_success" in st.session_state:
        st.success(st.session_state["flash_success"])
        del st.session_state["flash_success"]
    if "flash_warning" in st.session_state:
        st.warning(st.session_state["flash_warning"])
        del st.session_state["flash_warning"]

    t1, t2 = st.tabs(["📥 Новая операция", "📊 Операции и отчёты"])

    with t1:
        st.markdown("#### Шаг 1. Чек или скрин (необязательно)")
        st.caption("Если есть чек/скрин — загрузи. Если наличка или оплата без чека — пропусти этот шаг.")
        upl = st.file_uploader("PNG или JPG (можно пропустить)", type=["png", "jpg", "jpeg"], key="upload_receipt_" + str(st.session_state["upload_counter"]))
        fpath = None
        if upl is not None:
            digest = hashlib.md5(upl.getvalue()).hexdigest()[:10]
            safe_name = upl.name.replace(" ", "_")
            fname = digest + "_" + safe_name
            fpath = os.path.join(ACC_DIR, fname)
            if not os.path.exists(fpath):
                with open(fpath, "wb") as f:
                    f.write(upl.getvalue())
                st.session_state["flash_success"] = "Файл сохранён: accounting/" + fname
            else:
                st.info("Такой файл уже есть в accounting (не дублируем)")
            st.image(fpath, width=400)
            st.markdown("#### Шаг 2. Распознанный текст (подсказка)")
            with st.spinner("Распознаю..."):
                text = office_ocr.recognize_image(fpath)
            st.text_area("Текст с чека", value=text, height=200)
            amounts = office_ocr.find_amounts(text)
            if amounts:
                st.markdown("Найдены суммы со знаком рубля: " + ", ".join([a.strip() for a in amounts[:5]]))
        else:
            st.info("Чек не загружен — введи сумму и описание вручную в шаге 3")

        st.markdown("#### Шаг 3. Введи операцию")
        with st.form("add_tx"):
            c1, c2 = st.columns(2)
            ttype = c1.selectbox("Тип", ["расход", "доход"])
            cat = c2.selectbox("Категория", ["материалы", "аренда", "ремонт", "обслуживание", "ярмарка", "реклама", "зарплата", "налоги", "прочее"])
            amount = st.number_input("Сумма (руб)", min_value=0.0, step=1.0, format="%.2f")
            desc = st.text_input("Описание*", placeholder="PETG 2 катушки Ozon / Наличка от клиента")
            sent = st.form_submit_button("💾 Записать в базу")
            if sent:
                if amount <= 0:
                    st.session_state["flash_warning"] = "Введи сумму больше нуля"
                    st.rerun()
                elif not desc.strip():
                    st.session_state["flash_warning"] = "Введи описание — потом не вспомнишь на что ушли деньги"
                    st.rerun()
                else:
                    tid = db.add_transaction(ttype, cat, amount, desc.strip(), fpath)
                    st.session_state["flash_success"] = "Операция записана, id " + str(tid)
                    st.session_state["upload_counter"] = st.session_state["upload_counter"] + 1
                    st.rerun()

        if st.button("🧹 Очистить загруженный файл"):
            st.session_state["upload_counter"] = st.session_state["upload_counter"] + 1
            st.rerun()

    with t2:
        st.markdown("#### Последние операции")
        txs = db.list_transactions()
        if not txs:
            st.info("Операций пока нет")
        for t in txs[:15]:
            sign = "-" if t["type"] == "расход" else "+"
            has_photo = "📎" if t["screenshot_path"] else "—"
            c1, c2 = st.columns([6, 1])
            c1.markdown(sign + " **" + str(t["amount"]) + " руб** | " + str(t["date"]) + " | " + str(t["category"]) + " | " + str(t["description"]) + " " + has_photo)
            if c2.button("🗑 Удалить", key="del" + str(t["id"])):
                db.delete_transaction(t["id"])
                st.session_state["flash_success"] = "Операция удалена вместе со скрином"
                st.rerun()
        if txs:
            conf = st.checkbox("Подтверждаю полную очистку всех операций")
            if st.button("🧹 Удалить ВСЕ операции"):
                if conf:
                    db.clear_transactions()
                    st.session_state["flash_success"] = "Все операции удалены"
                    st.rerun()
                else:
                    st.warning("Сначала поставь галочку подтверждения")

        st.markdown("#### 🧹 Очистка сиротских фото")
        st.caption("Удаляет файлы из accounting, которые не привязаны ни к одной операции")
        if st.button("Найти и удалить сиротские фото"):
            conn = db.get_conn()
            cur = conn.cursor()
            cur.execute("SELECT screenshot_path FROM transactions WHERE screenshot_path IS NOT NULL")
            linked = set()
            for row in cur.fetchall():
                linked.add(row["screenshot_path"])
            conn.close()
            orphans = 0
            for fname in os.listdir(ACC_DIR):
                fpath_check = os.path.join(ACC_DIR, fname)
                if fpath_check not in linked:
                    try:
                        os.remove(fpath_check)
                        orphans += 1
                    except Exception:
                        pass
            st.session_state["flash_success"] = "Удалено сиротских фото: " + str(orphans)
            st.rerun()

        st.markdown("#### 📊 Отчёт за месяц")
        months = sorted(set([t["date"][:7] for t in txs]), reverse=True)
        if months:
            msel = st.selectbox("Месяц", months)
            if st.button("Построить отчёт"):
                inc = 0.0
                exp = 0.0
                cats = {}
                for t in txs:
                    if t["date"][:7] != msel:
                        continue
                    if t["type"] == "доход":
                        inc += t["amount"]
                    else:
                        exp += t["amount"]
                    key = t["type"] + " / " + t["category"]
                    cats[key] = cats.get(key, 0.0) + t["amount"]
                lines = []
                lines.append("# Отчёт за " + msel)
                lines.append("")
                lines.append("- Доходы: " + str(round(inc, 2)) + " руб")
                lines.append("- Расходы: " + str(round(exp, 2)) + " руб")
                lines.append("- Прибыль: " + str(round(inc - exp, 2)) + " руб")
                lines.append("")
                lines.append("## По категориям")
                for k in sorted(cats.keys()):
                    lines.append("- " + k + ": " + str(round(cats[k], 2)) + " руб")
                st.markdown("\n".join(lines))
                csv_lines = ["дата;тип;категория;сумма;описание"]
                for t in txs:
                    if t["date"][:7] == msel:
                        safe_desc = str(t["description"]).replace(";", " ").replace(",", " ")
                        amt = str(t["amount"]).replace(".", ",")
                        csv_lines.append(t["date"] + ";" + t["type"] + ";" + t["category"] + ";" + amt + ";" + safe_desc)
                st.download_button("⬇️ Скачать CSV", data="\ufeff" + "\n".join(csv_lines), file_name="report_" + msel + ".csv", mime="text/csv")
        else:
            st.info("Данных для отчёта пока нет")