# fairs_ui.py - вкладка Ярмарки + Напоминания
import streamlit as st
import datetime
import office_db as db

def render():
    db.init_db()
    db.migrate_db()
    st.subheader("🎪 Ярмарки и Напоминания")
    t1, t2, t3 = st.tabs(["➕ Новая ярмарка", "📊 История ярмарок", "🔔 Напоминания"])

    with t1:
        st.markdown("#### Ручной ввод ярмарки")
        with st.form("add_fair"):
            d_str = st.date_input("Дата ярмарки", value=datetime.date.today()).isoformat()
            fname = st.text_input("Название*", placeholder="Осенняя ярмарка в ТЦ")
            floc = st.text_input("Место", placeholder="ТЦ Аврора, Самара")
            c1, c2 = st.columns(2)
            cost = c1.number_input("Стоимость участия (руб)", value=0.0, step=100.0)
            revenue = c2.number_input("Доход с ярмарки (руб)", value=0.0, step=100.0)
            items = st.text_input("Что продавалось", placeholder="Драконы красные x5, Кольца x10")
            notes = st.text_area("Примечания", placeholder="Хорошее место, мало людей утром")
            sent = st.form_submit_button("➕ Добавить ярмарку")
            if sent:
                if not fname.strip():
                    st.warning("Введи название")
                else:
                    fid = db.add_fair(d_str, fname.strip(), floc.strip(), cost, revenue, items.strip(), notes.strip())
                    try:
                        d_obj = datetime.datetime.strptime(d_str, "%Y-%m-%d").date()
                        remind1 = (d_obj - datetime.timedelta(days=3)).isoformat()
                        remind2 = (d_obj + datetime.timedelta(days=1)).isoformat()
                        db.add_reminder(remind1, "подготовить пост-анонс к ярмарке '" + fname.strip() + "'", "ярмарка")
                        db.add_reminder(remind2, "посчитать итоги ярмарки '" + fname.strip() + "'", "ярмарка")
                    except Exception:
                        pass
                    st.success("Ярмарка добавлена, id " + str(fid) + ", созданы напоминания за 3 дня и +1 день")
                    st.rerun()

    with t2:
        st.markdown("#### История ярмарок с ROI")
        fairs = db.list_fairs()
        if not fairs:
            st.info("Ярмарок пока нет")
        for f in fairs:
            cost = f["cost"] or 0.0
            revenue = f["revenue"] or 0.0
            profit = revenue - cost
            roi = (profit / cost * 100) if cost > 0 else None
            roi_text = str(round(roi, 1)) + "%" if roi is not None else "—"
            icon = "🟢" if profit > 0 else ("🔴" if profit < 0 else "⚪")
            c1, c2 = st.columns([6, 1])
            with c1:
                with st.container(border=True):
                    st.markdown(icon + " **" + str(f["name"]) + "** — " + str(f["date"]) + ", " + str(f["location"]))
                    st.caption("Расход: " + str(cost) + "₽ | Доход: " + str(revenue) + "₽ | Прибыль: " + str(profit) + "₽ | **ROI: " + roi_text + "**")
                    if f["items_sold"]:
                        st.markdown("Товары: " + str(f["items_sold"]))
                    if f["notes"]:
                        st.markdown("Заметки: " + str(f["notes"]))
            if c2.button("🗑", key="fdel" + str(f["id"])):
                db.delete_fair(f["id"])
                st.rerun()

    with t3:
        st.markdown("#### Активные напоминания")
        reminders = db.list_reminders("open")
        if not reminders:
            st.info("Напоминаний нет")
        for r in reminders:
            try:
                d_obj = datetime.datetime.strptime(r["date"], "%Y-%m-%d").date()
                days = (d_obj - datetime.date.today()).days
                days_text = "сегодня" if days == 0 else ("вчера" if days == -1 else ("завтра" if days == 1 else (str(days) + " дн.")))
            except Exception:
                days_text = "?"
            c1, c2, c3 = st.columns([6, 1, 1])
            c1.markdown("🔔 **" + str(r["date"]) + "** (" + days_text + ") — " + str(r["text"]) + " _" + str(r["category"] or "") + "_")
            if c2.button("✅", key="rdone" + str(r["id"])):
                db.mark_reminder_done(r["id"])
                st.rerun()
            if c3.button("🗑", key="rdel" + str(r["id"])):
                db.delete_reminder(r["id"])
                st.rerun()
        st.markdown("#### ➕ Создать напоминание вручную")
        with st.form("add_reminder"):
            rd_str = st.date_input("Дата", value=datetime.date.today()).isoformat()
            rtext = st.text_input("Текст*", placeholder="позвонить клиенту")
            rcat = st.text_input("Категория", placeholder="клиент")
            sent = st.form_submit_button("➕ Добавить")
            if sent:
                if not rtext.strip():
                    st.warning("Введи текст")
                else:
                    db.add_reminder(rd_str, rtext.strip(), rcat.strip())
                    st.success("Напоминание создано")
                    st.rerun()