# office_ui.py v12 (стабильная версия со всеми пресетами и кэшированием)
import streamlit as st
import os, glob, datetime, time, json
import office

st.set_page_config(page_title="ОФИС-3D", page_icon="🏢", layout="wide")

# 🔒 ЗАМОК
def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets.get("password", ""):
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("🔒 Пароль офиса", type="password", on_change=password_entered, key="password")
        return False
    if not st.session_state["password_correct"]:
        st.text_input("😕 Неверный пароль", type="password", on_change=password_entered, key="password")
        return False
    return True

if not check_password():
    st.stop()

def rerun():
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

st.title("🏢 ОФИС-3D — панель управления виртуальным офисом")

ROLES = office.ROLES
TIMINGS = os.path.join(office.BASE, "logs", "timings.jsonl")

# ==========================================
# 🎭 ПРЕДУСТАНОВКИ РОЛЕЙ (восстановлены полностью)
# ==========================================
ROLE_DEFAULTS = {
    "director":   {"fast": False, "web": False, "desc": "исполнительный директор, оркестратор"},
    "marketer":   {"fast": False, "web": False, "desc": "маркетинг, УТП, ниша"},
    "smm":        {"fast": False, "web": False, "desc": "VK и соцсети, творческие задачи"},
    "sales":      {"fast": False, "web": False, "desc": "продажи, возражения"},
    "analyst":    {"fast": True,  "web": True,  "desc": "анализ рынка, ярмарки, отчёты"},
    "financier":  {"fast": False, "web": False, "desc": "финансист-бухгалтер, точные цифры"},
    "lawyer":     {"fast": False, "web": False, "desc": "юрист, РФ"},
    "steward":    {"fast": False, "web": False, "desc": "дворецкий, жильё"},
    "engineer":   {"fast": True,  "web": False, "desc": "инженер, техника"},
    "logistic":   {"fast": True,  "web": True,  "desc": "закупки, поставщики"},
    "tech":       {"fast": True,  "web": False, "desc": "технолог 3D-печати"},
    "crm":        {"fast": True,  "web": False, "desc": "постоянные клиенты"},
}

def meta(r):
    d = ROLES.get(r, {})
    return d.get("emoji", "🤖"), d.get("name", r), d.get("duty", ROLE_DEFAULTS.get(r, {}).get("desc", ""))

def fmt_sec(s):
    m, ss = divmod(int(round(s)), 60)
    return f"{m} мин {ss:02d} сек"

def log_timing(role, sec):
    os.makedirs(os.path.dirname(TIMINGS), exist_ok=True)
    with open(TIMINGS, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": datetime.datetime.now().isoformat(), "role": role, "sec": round(sec, 1)}, ensure_ascii=False) + "\n")

@st.cache_data(ttl=60)
def journal_lines():
    j = os.path.join(office.BASE, "logs", "journal.md")
    if not os.path.exists(j):
        return []
    with open(j, encoding="utf-8") as f:
        return [l for l in f.read().splitlines() if l.strip()]

def show_board():
    bb = office.load_blackboard()
    if bb:
        st.markdown("#### 📋 Доска объявлений сейчас:")
        for k, v in bb.items():
            st.markdown(f"📌 **{k}:** `{v}`")
    else:
        st.info("📋 Доска пока пуста.")

@st.cache_data(ttl=60)
def get_reports():
    return sorted(glob.glob(os.path.join(office.BASE, "reports", "*.md")), reverse=True)

reports = get_reports()

with st.sidebar:
    st.header("⚙️ Состояние")
    try:
        import requests as _rq
        _rq.get(office.OLLAMA + "/api/tags", timeout=3)
        st.success("🧠 Ollama: НА СВЯЗИ")
    except:
        st.error("🧠 Ollama: НЕ ЗАПУЩЕН")
    st.write(f"Основная: {office.MODEL}")
    st.write(f"Быстрая: {office.FAST_MODEL}")
    st.caption("Офис локальный, данные не уходят.")

    st.divider()
    st.subheader("📋 Доска объявлений")
    bb_data = office.load_blackboard()
    if bb_data:
        for k, v in bb_data.items():
            st.markdown(f"📌 **{k}:** `{v}`")
    else:
        st.info("Доска пуста. Сотрудники запишут сюда факты во время работы.")

    with st.expander("➕ Прикрепить факт вручную"):
        fk = st.text_input("Название факта", key="bb_key", placeholder="Например: Цена PLA")
        fv = st.text_input("Значение", key="bb_val", placeholder="Например: 1200 руб/кг")
        if st.button("📌 Прикрепить", key="bb_add"):
            if fk.strip() and fv.strip():
                bb = office.load_blackboard()
                bb[fk.strip()] = fv.strip()
                office.save_blackboard(bb)
                st.success("Прикреплено!")
                st.cache_data.clear()
                rerun()
            else:
                st.warning("Заполни оба поля.")

    if st.button("🧹 Очистить доску", key="bb_clear"):
        office.save_blackboard({})
        st.cache_data.clear()
        rerun()

m1, m2, m3 = st.columns(3)
m1.metric("📚 Отчётов", len(reports))
m2.metric("✅ Задач в журнале", len(journal_lines()))
m3.metric("👥 Сотрудников", len([r for r in ROLES if r != "critic"]))

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧭 Через Павла", "📝 Прямая задача", "👥 Команда", "📚 Отчёты", "🧠 База"])

# ==========================================
# 🎯 ВСЕ 5 ПРЕСЕТОВ (восстановлены полностью)
# ==========================================
PRESETS = [
    ("🧮 Пересчёт цен", "financier", "Пересчитай цены Медвежонка/Машинки/Ракеты по формуле v2 из базы знаний. Таблица: себестоимость, маржа, полки цен ярмарка/онлайн. Итоговые цены запиши на Доску."),
    ("📅 Календарь ярмарок", "analyst", "Составь 10 поисковых запросов для ручного поиска ярмарок Самары октябрь-декабрь 2026. Тематика: игрушки, подарки, новогодние. Найденные даты и места запиши на Доску. Без выдуманных ярмарок."),
    ("🎬 Контент-план VK", "smm", "Контент-план для VK СамПластик на 4 недели: 3 поста в неделю, рубрики процесс/готовое/обучение/юмор/продажа, черновики. Смотри на Доску для дат."),
    ("📦 Закупка пластика", "logistic", "5-7 поисковых запросов для мониторинга цен PETG/PLA 1 кг на AliExpress/Ozon/Яндекс.Маркет. Чек-лист проверки предложения. Найденные цены запиши на Доску. Без выдуманных цен."),
    ("🤝 Анонс постоянным", "crm", "Сообщение постоянным клиентам: новая коллекция Драконы-элементали, скидка 10% своим, призыв заказать. Смотри на Доску для актуальных цен."),
]

with tab1:
    st.subheader("🧭 Поручить директору Павлу (он сам распределит задачи)")
    st.info("Павел проанализирует задачу, разобьёт на 2-5 подзадач и распределит их по сотрудникам. Каждый получит правильный режим автоматически. Сотрудники будут читать Доску и писать на неё. Время: 3-15 минут.")
    task = st.text_area("Задача для Павла", height=130, placeholder="Например: подготовить СамПластик к новогодней ярмарке через месяц...")
    use_web = st.checkbox("🌐 Разрешить веб-поиск для всей цепочки")
    if st.button("🚀 Передать Павлу", type="primary"):
        if not task.strip():
            st.warning("Введите задачу.")
        else:
            t0 = time.perf_counter()
            progress = st.empty()
            def callback(i, total, role, mode, t):
                e, n, _ = meta(role)
                progress.info(f"🔄 Шаг {i}/{total}: {e} {n} ({mode}) — {t[:60]}...")
            with st.spinner("🧭 Павел анализирует задачу и составляет план..."):
                result, path, results = office.dispatch_task(task, use_web, callback)
            elapsed = time.perf_counter() - t0
            log_timing("director_dispatch", elapsed)
            st.success(f"Готово! Отчёт: {os.path.basename(path)} | ⏱ {fmt_sec(elapsed)} | Шагов: {len(results)}")
            st.markdown("### Результат")
            st.markdown(result)
            show_board()

with tab2:
    st.subheader("📝 Прямая задача сотруднику")
    cols = st.columns(3)
    for i, (label, role, text) in enumerate(PRESETS):
        if cols[i % 3].button(label, key=f"p{i}"):
            st.session_state["task_role"] = role
            st.session_state["task_text"] = text
    roles = [r for r in ROLES if r != "critic"]
    default_role = st.session_state.get("task_role", roles[0])
    idx = roles.index(default_role) if default_role in roles else 0
    role = st.selectbox("Кому поручить", roles, index=idx,
                        format_func=lambda r: f"{meta(r)[0]} {meta(r)[1]} — {meta(r)[2]}")
    
    defaults = ROLE_DEFAULTS.get(role, {"fast": False, "web": False})
    
    task = st.text_area("Текст задачи", height=130, key="task_text")
    use_web = st.checkbox("🌐 Поискать в интернете", value=defaults["web"])
    fast = st.checkbox("⚡ Быстрый режим (phi3:mini, без критика)", value=defaults["fast"])
    
    if st.button("🚀 Выдать задачу", type="primary"):
        if not task.strip():
            st.warning("Введите текст задачи.")
        else:
            t0 = time.perf_counter()
            spin = f"""⚡ {meta(role)[0]} {meta(role)[1]} работает в быстром режиме...""" if fast else f"""{meta(role)[0]} {meta(role)[1]} думает, 🧐 Вероника проверяет..."""
            with st.spinner(spin):
                result, path, critic = office.run_single_task(role, task, use_web, fast)
            elapsed = time.perf_counter() - t0
            log_timing(role, elapsed)
            st.success(f"Готово! Отчёт: {os.path.basename(path)} | ⏱ {fmt_sec(elapsed)}")
            st.markdown("### Результат")
            st.markdown(result)
            if critic:
                with st.expander("🧐 Комментарий критика"):
                    st.text(critic)
            show_board()

with tab3:
    st.subheader("Наша команда")
    st.info("Настройки каждой роли зашиты в систему: Павел сам выбирает режим (FAST/FULL) при диспетчеризации. Для прямой задачи — предустановленные режимы подставляются автоматически.")
    keys = [r for r in ROLES if r != "critic"]
    for i in range(0, len(keys), 4):
        cols = st.columns(4)
        for c, r in zip(cols, keys[i:i+4]):
            e, n, duty = meta(r)
            d = ROLE_DEFAULTS.get(r, {})
            with c.container(border=True):
                st.markdown(f"### {e} {n}")
                st.caption(duty)
                mode_badge = "⚡ FAST" if d.get("fast") else "🎯 FULL"
                web_badge = "🌐 web" if d.get("web") else "📚 база"
                st.markdown(f"**{mode_badge}** {web_badge}")

with tab4:
    st.subheader("Архив отчётов")
    if reports:
        sel = st.selectbox("Выберите отчёт", reports, format_func=lambda p: os.path.basename(p))
        with open(sel, encoding="utf-8") as f:
            st.markdown(f.read())
    else:
        st.info("Отчётов пока нет.")

with tab5:
    st.subheader("База знаний")
    comp = os.path.join(office.BASE, "knowledge", "company.md")
    txt = st.text_area("Данные компании", open(comp, encoding="utf-8").read() if os.path.exists(comp) else "", height=280)
    if st.button("💾 Сохранить базу"):
        with open(comp, "w", encoding="utf-8") as f:
            f.write(txt)
        st.success("Сохранено.")