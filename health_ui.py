# health_ui.py - вкладка Диагностика (иммунная система офиса)
import streamlit as st
import os
import json
import shutil
import datetime
import office_db as db

BASE = os.path.dirname(os.path.abspath(__file__))
INC_FILE = os.path.join(BASE, "incidents.json")

def now_str():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_incidents():
    if not os.path.exists(INC_FILE):
        return []
    try:
        with open(INC_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_incidents(items):
    with open(INC_FILE, "w", encoding="utf-8") as f:
        json.dump(items[-200:], f, ensure_ascii=False, indent=1)

def next_id(items):
    day = datetime.date.today().isoformat().replace("-", "")
    ids = set(i["id"] for i in items)
    n = 1
    while True:
        cand = "INC-" + day + "-" + str(n).zfill(3)
        if cand not in ids:
            return cand
        n += 1

def run_checks():
    finds = []
    try:
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("PRAGMA integrity_check")
        res = cur.fetchone()
        conn.close()
        ok = res is not None and str(res[0]) == "ok"
    except Exception:
        ok = False
    if not ok:
        finds.append(("db_integrity", "CRITICAL", "база SQLite повреждена", "восстановить из бэкапа через restore.bat"))
    acc = os.path.join(BASE, "accounting")
    linked = set()
    for t in db.list_transactions():
        if t["screenshot_path"]:
            linked.add(t["screenshot_path"])
    orphans = 0
    if os.path.isdir(acc):
        for fn in os.listdir(acc):
            if os.path.join(acc, fn) not in linked:
                orphans += 1
    if orphans > 0:
        finds.append(("orphan_photos", "WARNING", "сиротских фото в accounting: " + str(orphans), "кнопка очистки во вкладке Чеки и Финансы"))
    free_gb = shutil.disk_usage(BASE).free / (1024 ** 3)
    if free_gb < 10:
        finds.append(("disk_space", "WARNING", "свободно на диске меньше 10 ГБ: " + str(round(free_gb, 1)), "почистить загрузки и старые бэкапы"))
    try:
        import urllib.request
        req = urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3)
        ollama_ok = req.status == 200
    except Exception:
        ollama_ok = False
    if not ollama_ok:
        finds.append(("ollama_down", "CRITICAL", "Ollama не отвечает на localhost:11434", "запустить Ollama или перезагрузить ПК"))
    overdue = 0
    today = datetime.date.today()
    for r in db.list_reminders("open"):
        try:
            d = datetime.datetime.strptime(r["date"], "%Y-%m-%d").date()
            if d < today:
                overdue += 1
        except Exception:
            pass
    if overdue > 0:
        finds.append(("reminders_overdue", "WARNING", "просроченных напоминаний: " + str(overdue), "закрыть или перенести во вкладке Ярмарки"))
    low = [p for p in db.list_plastic() if p["weight_grams"] <= p["min_weight"]]
    if low:
        names = ", ".join(p["material"] + " " + str(p["color"]) for p in low)
        finds.append(("plastic_low", "WARNING", "пластик на пороге запаса: " + names, "закупка через Фёдора"))
    for p in db.list_printers():
        if p["resource_hours"]:
            pct = (p["used_hours"] or 0) / p["resource_hours"] * 100
            if pct >= 90:
                finds.append(("printer_wear", "WARNING", "принтер " + str(p["name"]) + " выработал " + str(round(pct, 1)) + "% ресурса", "сервис или замена сопла"))
    try:
        import office
        bb = office.load_blackboard()
        old = 0
        for k, v in bb.items():
            if not isinstance(v, dict):
                continue
            ts = v.get("updated_at") or v.get("created_at") or v.get("date") or ""
            if ts:
                try:
                    d = datetime.datetime.strptime(str(ts)[:10], "%Y-%m-%d").date()
                    if (today - d).days > 30:
                        old += 1
                except Exception:
                    pass
        if old > 0:
            finds.append(("board_stale", "INFO", "фактов на Доске старше 30 дней: " + str(old), "проверить актуальность цен и ссылок"))
    except Exception:
        pass
    return finds

def render():
    db.init_db()
    db.migrate_db()
    st.subheader("🩺 Диагностика офиса")
    if st.button("🩺 Провести диагностику"):
        finds = run_checks()
        items = load_incidents()
        open_types = set(i["type"] for i in items if i["status"] == "OPEN")
        added = 0
        for ftype, sev, symptom, action in finds:
            if ftype in open_types:
                continue
            items.append({
                "id": next_id(items),
                "timestamp": now_str(),
                "type": ftype,
                "severity": sev,
                "symptom": symptom,
                "suggested_action": action,
                "status": "OPEN",
            })
            added += 1
        save_incidents(items)
        st.session_state["flash_health"] = "Диагностика завершена: проблем найдено " + str(len(finds)) + ", новых инцидентов " + str(added)
        st.rerun()
    if "flash_health" in st.session_state:
        st.success(st.session_state.pop("flash_health"))
    items = load_incidents()
    opens = [i for i in items if i["status"] == "OPEN"]
    st.markdown("#### Открытые инциденты: " + str(len(opens)))
    if not opens:
        st.info("Открытых инцидентов нет. Офис здоров.")
    for i in opens:
        icon = "🔴" if i["severity"] == "CRITICAL" else ("🟡" if i["severity"] == "WARNING" else "⚪")
        c1, c2 = st.columns([6, 1])
        c1.markdown(icon + " **" + i["id"] + "** [" + i["severity"] + "] " + i["type"] + ": " + i["symptom"] + " → _" + i["suggested_action"] + "_")
        if c2.button("✅", key="heal" + i["id"]):
            for x in items:
                if x["id"] == i["id"]:
                    x["status"] = "HEALED"
            save_incidents(items)
            st.rerun()
    healed = [i for i in items if i["status"] == "HEALED"]
    if healed:
        with st.expander("История вылеченных (" + str(len(healed)) + ")"):
            for i in healed[-10:]:
                st.markdown("- " + i["id"] + " " + i["type"] + ": " + i["symptom"])