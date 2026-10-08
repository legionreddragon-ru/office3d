# warehouse_ui.py - вкладка Склад и Принтеры
import streamlit as st
import office_db as db

def render():
    db.init_db()
    st.subheader("🏭 Склад и Принтеры")
    t1, t2, t3 = st.tabs(["🖨 Принтеры", "🧵 Пластик", "📦 Изделия и инвентаризация"])

    with t1:
        st.markdown("#### ➕ Добавить принтер")
        with st.form("add_printer"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Название*", placeholder="Основной")
            model = c2.text_input("Модель", placeholder="Bambu Lab P1S Combo")
            c3, c4 = st.columns(2)
            nozzle = c3.number_input("Сопло (мм)", value=0.4, step=0.1, format="%.1f")
            bed = c4.text_input("Стол (мм)", placeholder="256x256x256")
            mats = st.text_input("Материалы через запятую", placeholder="PLA,PETG,ABS")
            c5, c6 = st.columns(2)
            price = c5.number_input("Цена покупки (руб)", value=0, step=1000)
            resource = c6.number_input("Ресурс (часов)", value=4500, step=100)
            loc = st.text_input("Где стоит", placeholder="кабинет")
            sent = st.form_submit_button("➕ Добавить принтер")
            if sent:
                if not name.strip():
                    st.warning("Введи название")
                else:
                    pid = db.add_printer(name.strip(), model.strip(), nozzle, bed.strip(), mats.strip(), price, resource, loc.strip())
                    st.success("Принтер добавлен, id " + str(pid))
                    st.rerun()
        st.markdown("#### 🖨 Парк принтеров")
        printers = db.list_printers()
        if not printers:
            st.info("Принтеров пока нет. Добавь первый выше.")
        for p in printers:
            pct = 0.0
            if p["resource_hours"]:
                pct = round((p["used_hours"] or 0) / p["resource_hours"] * 100, 1)
            with st.container(border=True):
                st.markdown("### 🖨 " + str(p["name"]) + " — " + str(p["model"]))
                st.caption("Материалы: " + str(p["materials"]) + " | Стол: " + str(p["bed_size"]) + " | Сопло: " + str(p["nozzle_diameter"]) + " мм | Где: " + str(p["location"]))
                st.progress(min(pct, 100.0) / 100.0)
                st.markdown("Ресурс: " + str(p["used_hours"]) + " ч из " + str(p["resource_hours"]) + " ч (" + str(pct) + "%)")
                h = st.number_input("Наработка за сессию (часов)", min_value=0.0, step=0.5, key="h" + str(p["id"]))
                if st.button("⏱ Списать часы", key="hb" + str(p["id"])):
                    if h > 0:
                        db.add_printer_hours(p["id"], h)
                        st.rerun()

    with t2:
        st.markdown("#### ➕ Добавить пластик")
        with st.form("add_plastic"):
            c1, c2 = st.columns(2)
            mat = c1.selectbox("Материал", ["PETG", "PLA", "ABS", "ASA", "TPU", "PA", "PC"])
            color = c2.text_input("Цвет", placeholder="красный")
            c3, c4 = st.columns(2)
            weight = c3.number_input("Вес (г)", value=1000, step=100)
            minw = c4.number_input("Порог тревоги (г)", value=200, step=50)
            loc = st.text_input("Где лежит", placeholder="шкаф А")
            sup = st.text_input("Поставщик", placeholder="Ozon")
            printers = db.list_printers()
            pnames = ["не привязан"] + [p["name"] for p in printers]
            psel = st.selectbox("Привязать к принтеру", pnames)
            sent = st.form_submit_button("➕ Добавить пластик")
            if sent:
                pid_sel = None
                if psel != "не привязан":
                    for p in printers:
                        if p["name"] == psel:
                            pid_sel = p["id"]
                db.add_plastic(mat, color.strip(), int(weight), int(minw), loc.strip(), sup.strip(), pid_sel)
                st.success("Пластик добавлен")
                st.rerun()
        st.markdown("#### 🧵 Остатки пластика")
        rows = db.list_plastic()
        if not rows:
            st.info("Склад пуст")
        for r in rows:
            icon = "⚠️" if r["weight_grams"] <= r["min_weight"] else "✅"
            st.markdown(icon + " **" + str(r["material"]) + " " + str(r["color"]) + ":** " + str(r["weight_grams"]) + " г (порог " + str(r["min_weight"]) + ") — " + str(r["location"]))
        st.markdown("#### ✂️ Списать пластик (пробник / печать / брак)")
        rows2 = db.list_plastic()
        if rows2:
            with st.form("use_plastic"):
                opts = {}
                for r in rows2:
                    label = "[" + str(r["id"]) + "] " + str(r["material"]) + " " + str(r["color"]) + " (" + str(r["weight_grams"]) + " г)"
                    opts[label] = r["id"]
                sel = st.selectbox("Какой пластик", list(opts.keys()))
                g = st.number_input("Сколько грамм", min_value=1, step=5, value=75)
                purpose = st.selectbox("Цель", ["пробник", "изделие", "брак", "образец"])
                note = st.text_input("Примечание", placeholder="пробник дракона")
                sent = st.form_submit_button("✂️ Списать")
                if sent:
                    ok, msg = db.use_plastic(opts[sel], int(g), purpose, None, purpose, note.strip())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
        else:
            st.info("Сначала добавь пластик на склад")

    with t3:
        st.markdown("#### ➕ Добавить изделия")
        with st.form("add_product"):
            c1, c2 = st.columns(2)
            pname = c1.text_input("Название*", placeholder="Дракон красный")
            qty = c2.number_input("Количество", value=1, step=1)
            c3, c4 = st.columns(2)
            pmat = c3.text_input("Материал", placeholder="PETG")
            pweight = c4.number_input("Вес 1 шт (г)", value=75, step=5)
            c5, c6 = st.columns(2)
            pcost = c5.number_input("Себестоимость (руб)", value=394.0, step=1.0)
            pprice = c6.number_input("Цена (руб)", value=550.0, step=10.0)
            ploc = st.text_input("Где", placeholder="витрина")
            sent = st.form_submit_button("➕ Добавить изделие")
            if sent:
                if not pname.strip():
                    st.warning("Введи название")
                else:
                    db.add_product(pname.strip(), int(qty), pmat.strip(), int(pweight), pcost, pprice, ploc.strip(), None)
                    st.success("Изделие добавлено")
                    st.rerun()
        if st.button("📦 Показать инвентаризацию"):
            rep = db.inventory_report()
            st.markdown("##### Пластик")
            if rep["plastic"]:
                for row in rep["plastic"]:
                    st.markdown("- " + str(row["material"]) + " " + str(row["color"]) + ": " + str(row["total"]) + " г")
            else:
                st.markdown("- пусто")
            st.markdown("##### Изделия")
            if rep["products"]:
                for row in rep["products"]:
                    st.markdown("- " + str(row["name"]) + ": " + str(row["qty"]) + " шт")
            else:
                st.markdown("- пусто")
            st.markdown("##### Пробники и пробы")
            st.markdown("- печатей: " + str(rep["tests_count"]) + ", потрачено пластика: " + str(rep["tests_weight"] or 0) + " г")