# remedy.py - 4 хирургические правки в office.py
import re

PATH = "office.py"
src = open(PATH, encoding="utf-8").read()
original = src
report = []

# === ПРАВКА 1: заменить весь блок ROLE_ADDONS ===
marker_start = "ROLE_ADDONS = {"
marker_end = "\nCOMPANY_TEMPLATE"
i1 = src.find(marker_start)
i2 = src.find(marker_end)
if i1 < 0 or i2 < 0:
    report.append("ПРАВКА 1: СТОП, не нашёл маркеры ROLE_ADDONS")
else:
    new_roles = """ROLE_ADDONS = {
    "logistic": (
        "\\n\\n⚠️ КРИТИЧЕСКИ ВАЖНОЕ ПРАВИЛО (ЗАПРЕТ ГАЛЛЮЦИНАЦИЙ):"
        "\\n\\nТЫ НЕ ИМЕЕШЬ ПРАВА ВЫДУМЫВАТЬ КАРТОЧКИ ТОВАРОВ!"
        "\\n\\nЕсли в блоке WEB SEARCH RESULTS ниже ты ВИДИШЬ реальные данные (названия, цены, РАЗНЫЕ ссылки, имена продавцов) - ТОЛЬКО ТОГДА выводи их и пиши на Доску."
        "\\n\\nЕсли реальных данных НЕТ - напиши: РЕАЛЬНЫХ ПРЕДЛОЖЕНИЙ В ВЕБ-ПОИСКЕ НЕ НАЙДЕНО, и дай ссылки-кандидаты для ручной проверки директором."
        "\\n\\nПРИЗНАКИ ГАЛЛЮЦИНАЦИИ (ЗАПРЕЩЕНО ВЫВОДИТЬ):"
        "\\n- все карточки с одной и той же ссылкой (ДАЖЕ если бренды разные)"
        "\\n- цены прогрессией (149, 159, 169...)"
        "\\n- продавец без имени, просто 'Продавец'"
        "\\n- рейтинги одинаковые (4.6, 4.6, 4.6...) - это ВЫДУМКА"
        "\\n- отзывы прогрессией (526, 375, 327...)"
        "\\n- одинаковые ссылки для разных товаров (Sunlu PETG и Creality PLA не могут иметь одну ссылку)"
        "\\n\\nЕсли ты видишь эти признаки - НЕ ВЫВОДИ карточки, напиши 'РЕАЛЬНЫХ ПРЕДЛОЖЕНИЙ НЕ НАЙДЕНО'."
    ),
    "smm": (
        "\\n\\n⚠️ КРИТИЧЕСКИ ВАЖНОЕ ПРАВИЛО (ФОРМАТ ОТВЕТА):"
        "\\n\\nТВОЙ ОТВЕТ СОСТОИТ ИЗ 2 ЧАСТЕЙ:"
        "\\n\\nЧАСТЬ 1: ТЕКСТЫ ПОСТОВ. Пиши посты обычным текстом, БЕЗ JSON-блоков внутри постов. Каждый пост: живой язык, УТП (мультицвет без покраски AMS или кастом по фото), цены ТОЛЬКО из базы знаний или с Доски, без выдуманных ссылок на посты VK."
        "\\n\\nЧАСТЬ 2: БЛОК ДЛЯ ДОСКИ. В САМОМ КОНЕЦЕ ответа добавь одной строкой: ```json {\"update\": {\"название_факта\": {\"value\": \"значение\", \"source\": \"https://ссылка-или-слово-база\"}}} ```"
        "\\n\\nЗАПРЕЩЕНО: вставлять JSON внутрь постов; выдумывать ссылки вида wall-193633899_123456789; слово 'скидка' без указания старой цены."
    ),
    "critic": (
        "\\n\\n⚠️ УСИЛЕННАЯ ПРОВЕРКА НА ГАЛЛЮЦИНАЦИИ (ставь ДОРАБОТКА если видишь):"
        "\\n1. все ссылки одинаковые (копипаст)"
        "\\n2. цены прогрессией (149, 159, 169...)"
        "\\n3. рейтинги одинаковые (4.6, 4.6, 4.6...)"
        "\\n4. продавец без имени"
        "\\n5. JSON-блоки внутри текстов постов"
        "\\n6. фейковые ссылки на несуществующие страницы"
        "\\n7. слово 'скидка' без старой цены"
    ),
    "analyst": "\\n\\nОПЕРАЦИОННОЕ ПРАВИЛО: любые даты, места, цены - только со ссылкой на источник или с пометкой ГИПОТЕЗА. Если ничего не найдено - НЕ пиши блок update на Доску вовсе.",
    "financier": "\\n\\nОПЕРАЦИОННОЕ ПРАВИЛО: цифры, рассчитанные из данных компании, можно писать на доску с источником 'база'.",
    "tech": "\\n\\nОПЕРАЦИОННОЕ ПРАВИЛО: граммы, время и себестоимость, рассчитанные из базы, можно писать на доску с источником 'база'."
}"""
    src = src[:i1] + new_roles + src[i2:]
    report.append("ПРАВКА 1: OK - блок ROLE_ADDONS заменён")

# === ПРАВКА 2: увеличить num_ctx по умолчанию ===
old_ask_sig = "def ask(role, text, temperature=0.4, model=None, num_ctx=8192):"
new_ask_sig = "def ask(role, text, temperature=0.4, model=None, num_ctx=16384):"
if old_ask_sig in src:
    src = src.replace(old_ask_sig, new_ask_sig)
    report.append("ПРАВКА 2: OK - num_ctx увеличен до 16384")
else:
    report.append("ПРАВКА 2: пропущено - уже применено ранее")

# === ПРАВКА 3: увеличить timeout ===
old_timeout = '"keep_alive": "5m", "options": {"num_ctx": num_ctx, "temperature": temperature}}, timeout=900)'
new_timeout = '"keep_alive": "5m", "options": {"num_ctx": num_ctx, "temperature": temperature}}, timeout=1800)'
if old_timeout in src:
    src = src.replace(old_timeout, new_timeout)
    report.append("ПРАВКА 3: OK - timeout увеличен до 1800 (30 мин)")
else:
    report.append("ПРАВКА 3: пропущено - уже применено ранее")

# === ПРАВКА 4: добавить функцию check_url_alive и встроить в замок ===
check_fn = """
def check_url_alive(url, timeout=12):
    \"\"\"Проверяет что ссылка реально открывается (HEAD-запрос).\"\"\"
    if not url.startswith("http"):
        return False, "не http"
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code < 400:
            return True, f"status {r.status_code}"
        return False, f"status {r.status_code}"
    except requests.exceptions.Timeout:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:50]

"""

# Вставляем check_url_alive ПЕРЕД функцией update_blackboard_from_text
marker_upd = "def update_blackboard_from_text(text, role="
if marker_upd in src and "def check_url_alive" not in src:
    src = src.replace(marker_upd, check_fn + marker_upd)
    report.append("ПРАВКА 4a: OK - функция check_url_alive добавлена")
else:
    report.append("ПРАВКА 4a: пропущено - уже есть")

# Встраиваем проверку в замок: после строки 'if src.startswith("http"):' и 'tag = "WEB"'
old_lock = '''        if src.startswith("http"):
            tag = "WEB"'''
new_lock = '''        if src.startswith("http"):
            alive, reason = check_url_alive(src)
            if not alive:
                log(f"ДОСКА: факт '{k}' ОТКЛОНЁН (ссылка мёртвая: {reason}): {src}")
                continue
            tag = "WEB"'''
if old_lock in src and "check_url_alive(src)" not in src:
    src = src.replace(old_lock, new_lock)
    report.append("ПРАВКА 4b: OK - замок теперь проверяет ссылки на живость")
else:
    report.append("ПРАВКА 4b: пропущено - уже есть")

# === ФИНАЛ: записываем если хоть одна правка прошла ===
if src != original:
    open(PATH, "w", encoding="utf-8").write(src)
    print("=== ОТЧЁТ REMEDY ===")
    for r in report:
        print("  " + r)
    print(f"Всего строк в новом файле: {len(src.splitlines())}")
else:
    print("НИЧЕГО НЕ ИЗМЕНЕНО")
    for r in report:
        print("  " + r)