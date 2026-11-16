# remedy14.py - русификация меню Streamlit
# Заменяет английское гамбургер-меню на две русские кнопки в сайдбаре
report = []
p = "office_ui.py"
s = open(p, encoding="utf-8").read()

MARKER_CSS = "/* OFFICE-RU-MENU */"

css_block = """
# " + MARKER_CSS + "
st.markdown(\"\"\"
<style>
#MainMenu, [data-testid="stMainMenu"],
[data-testid="stHeader"] [data-testid="stHeaderToolbar"],
header[data-testid="stHeader"] div[role="button"],
.stAppDeployButton, [data-testid="stAppDeployButton"],
[data-testid="stAppFooter"], footer {
    visibility: hidden;
    height: 0;
}
</style>
\"\"\", unsafe_allow_html=True)
"""

if MARKER_CSS in s:
    report.append("ПРАВКА 1 (CSS скрытие меню): уже применена")
elif "st.set_page_config" in s:
    s = s.replace(
        "st.set_page_config(page_title=",
        css_block + "\nst.set_page_config(page_title=",
        1
    )
    report.append("ПРАВКА 1 (CSS скрытие меню): OK")
else:
    report.append("ПРАВКА 1 (CSS скрытие меню): СТОП - не найден st.set_page_config")

MARKER_BTN = "# OFFICE-RU-BUTTONS"

btn_block = """
    " + MARKER_BTN + "
    st.markdown("#### 🛠 Инструменты")
    _c1, _c2 = st.columns(2)
    if _c1.button("🔄 Обновить", use_container_width=True, key="btn_ru_rerun"):
        st.rerun()
    if _c2.button("🧹 Кэш", use_container_width=True, key="btn_ru_cache"):
        st.cache_data.clear()
        try:
            st.cache_resource.clear()
        except Exception:
            pass
        st.success("Кэш очищен")
    st.caption("Печать страницы: Ctrl+P")
    st.divider()
"""

if MARKER_BTN in s:
    report.append("ПРАВКА 2 (русские кнопки): уже применена")
elif "with st.sidebar:" in s:
    s = s.replace(
        "with st.sidebar:",
        "with st.sidebar:" + btn_block,
        1
    )
    report.append("ПРАВКА 2 (русские кнопки): OK")
else:
    report.append("ПРАВКА 2 (русские кнопки): СТОП - не найден сайдбар")

open(p, "w", encoding="utf-8").write(s)
print("=== ОТЧЁТ REMEDY14 ===")
for r in report:
    print("  " + r)