# service_ui.py - вкладка Сервис (самообслуживание офиса)
import streamlit as st
import os
import datetime
import checkall
import office_db as db

BASE = os.path.dirname(os.path.abspath(__file__))
FLASH_KEY = "flash_service"

def render():
    db.init_db()
    db.migrate_db()
    st.subheader("🔧 Сервис — самообслуживание офиса")
    if FLASH_KEY in st.session_state:
        msg = st.session_state.pop(FLASH_KEY)
        st.success(msg)
    st.markdown("### 🩺 Блок 1: Лечение")
    st.caption("Запускает диагностику 21 пункт, лечит типичные косяки, отчитывается.")
    if st.button("🔍 Провести диагностику и лечение", key="btn_heal"):
        checks = []
        for name, fn in [
            ("1. Автотест", checkall.c_autotest),
            ("2. Синтаксис", checkall.c_syntax),
            ("3. SQLite", checkall.c_db_integrity),
            ("4. .env", checkall.c_env),
            ("5. .gitignore", checkall.c_gitignore),
            ("6. office.db вне git", checkall.c_git_db),
            ("7. Бэкап", checkall.c_backup),
            ("8. Ollama", checkall.c_ollama),
            ("9. Сироты", checkall.c_orphans),
            ("10. Иконка", checkall.c_icon),
            ("11. Мини-тесты", checkall.c_mini_tests),
            ("12. Venv", checkall.c_venv),
            ("13. Ollama модели", checkall.c_ollama_models),
            ("14. Tesseract", checkall.c_tesseract),
            ("15. Диск", checkall.c_disk_space),
            ("16. Размер базы", checkall.c_db_size),
            ("17. .env вне git", checkall.c_env_in_git),
            ("18. Инциденты", checkall.c_incidents_size),
            ("19. Планировщик", checkall.c_task_scheduler),
            ("20. Мусор", checkall.c_messy_files),
            ("21. Доска", checkall.c_board_fresh),
        ]:
            try:
                status, msg = fn()
            except Exception as e:
                status, msg = "FAIL", str(e)[:120]
            checks.append((name, status, msg))
        fails = [c for c in checks if c[1] == "FAIL"]
        healed_before = list(checkall.healed)
        if fails:
            checkall.healed.clear()
            checkall.try_heal()
            healed_after = list(checkall.healed)
            healed_now = [h for h in healed_after if h not in healed_before]
        else:
            healed_now = []
        lines = []
        for name, status, msg in checks:
            icon = {"OK": "✅", "WARN": "⚠️", "FAIL": "❌"}[status]
            lines.append(icon + " " + name + " — " + msg)
        if healed_now:
            lines.append("")
            lines.append("🔧 Вылечено:")
            for h in healed_now:
                lines.append("  • " + h)
        st.session_state["service_report"] = lines
        n_ok = sum(1 for c in checks if c[1] == "OK")
        st.session_state[FLASH_KEY] = "Диагностика завершена: " + str(n_ok) + "/21 OK"
        st.rerun()
    if "service_report" in st.session_state:
        st.markdown("\n".join(st.session_state["service_report"]))
    st.divider()
    st.caption("Следующие блоки появятся позже: Бэкапы • Доктор CSV • Ревью кода • Пакет для ремонта")