# remedy4.py - 3 правки: num_ctx, мягкий замок, детектор бессвязицы
import re

PATH = "office.py"
src = open(PATH, encoding="utf-8").read()
original = src
report = []

# === ПРАВКА 1: вернуть num_ctx на 8192 ===
old_ctx = "def ask(role, text, temperature=0.4, model=None, num_ctx=16384):"
new_ctx = "def ask(role, text, temperature=0.4, model=None, num_ctx=8192):"
if old_ctx in src:
    src = src.replace(old_ctx, new_ctx)
    report.append("ПРАВКА 1: OK - num_ctx возвращён на 8192 (экономит видеопамять)")
elif new_ctx in src:
    report.append("ПРАВКА 1: уже применена ранее")
else:
    report.append("ПРАВКА 1: СТОП - не нашёл сигнатуру ask()")

# === ПРАВКА 2: смягчить check_url_alive ===
old_check = '''def check_url_alive(url, timeout=12):
    """Проверяет что ссылка реально открывается (HEAD-запрос)."""
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
        return False, str(e)[:50]'''

new_check = '''def check_url_alive(url, timeout=12):
    """Проверяет что ссылка реально открывается (GET с ограничением размера).
    HEAD не используем - маркетплейсы Ozon/WB/Ali блокируют HEAD-запросы."""
    if not url.startswith("http"):
        return False, "не http"
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True, stream=True,
                         headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        # Читаем только первые 1КБ чтобы не грузить всю страницу
        _ = r.raw.read(1024)
        if r.status_code < 400:
            return True, f"status {r.status_code}"
        # 403/429 для маркетплейсов - это нормально, принимаем как живую
        if r.status_code in (403, 429) and any(d in url for d in ["ozon.ru", "wildberries.ru", "aliexpress", "market.yandex"]):
            return True, f"status {r.status_code} (marketplace block, accepted)"
        return False, f"status {r.status_code}"
    except requests.exceptions.Timeout:
        return False, "timeout"
    except Exception as e:
        return False, str(e)[:50]'''

if old_check in src:
    src = src.replace(old_check, new_check)
    report.append("ПРАВКА 2: OK - замок теперь использует GET и пропускает 403 для маркетплейсов")
elif "marketplace block, accepted" in src:
    report.append("ПРАВКА 2: уже применена ранее")
else:
    report.append("ПРАВКА 2: СТОП - не нашёл функцию check_url_alive")

# === ПРАВКА 3: детектор бессвязицы ===
# Добавляем проверку в update_blackboard_from_text: если в тексте ответа есть признаки галлюцинозного срыва,
# пропускаем обновление доски и пишем предупреждение в лог.
detector_code = '''
def detect_gibberish(text):
    """Ловит признаки галлюцинозного срыва модели: медицинские термины, формулы,
    обрывки английского в русском тексте, математические символы в бытовых постах."""
    if not text:
        return False, ""
    low = text.lower()
    # Медицинские/научные термины в ответе про пластик/посты
    medical_terms = ["cerebellum", "parkinson", "synaptic", "depression", "lesion",
                     "пуркинье", "мозжечок", "дофамин", "нейро", "патогенетич"]
    for t in medical_terms:
        if t in low:
            return True, f"медицинский термин: {t}"
    # Много математических формул в бытовом ответе
    if low.count("\\sum") > 2 or low.count("\\frac") > 2:
        return True, "много математических формул"
    # Смесь русского и английского в длинном тексте (признак сбоя)
    ru_chars = sum(1 for c in text if 'а' <= c.lower() <= 'я')
    en_chars = sum(1 for c in text if 'a' <= c.lower() <= 'z')
    if len(text) > 1000 and ru_chars > 200 and en_chars > 200 and en_chars / (ru_chars + en_chars) > 0.4:
        return True, "смесь русского и английского (признак сбоя модели)"
    return False, ""

'''

# Вставляем detector перед update_blackboard_from_text
marker_upd = "def update_blackboard_from_text(text, role="
if marker_upd in src and "def detect_gibberish" not in src:
    src = src.replace(marker_upd, detector_code + marker_upd)
    report.append("ПРАВКА 3a: OK - функция detect_gibberish добавлена")
else:
    report.append("ПРАВКА 3a: пропущено - уже есть")

# Встраиваем вызов детектора в начало update_blackboard_from_text
old_upd_start = '''def update_blackboard_from_text(text, role=""):
    m = re.search(r"```(?:json)?\\s*({.*?\\"update\\".*?})\\s*```", text, re.IGNORECASE | re.DOTALL)'''
new_upd_start = '''def update_blackboard_from_text(text, role=""):
    # Детектор бессвязицы: если модель выдала галлюцинозный срыв, не пишем на доску
    is_gibberish, reason = detect_gibberish(text)
    if is_gibberish:
        log(f"ДОСКА: обновление отклонено (детектор бессвязицы: {reason})")
        return
    m = re.search(r"```(?:json)?\\s*({.*?\\"update\\".*?})\\s*```", text, re.IGNORECASE | re.DOTALL)'''
if old_upd_start in src and "detect_gibberish(text)" not in src:
    src = src.replace(old_upd_start, new_upd_start)
    report.append("ПРАВКА 3b: OK - детектор встроен в замок")
else:
    report.append("ПРАВКА 3b: пропущено - уже есть")

# === ФИНАЛ ===
if src != original:
    open(PATH, "w", encoding="utf-8").write(src)
    print("=== ОТЧЁТ REMEDY4 ===")
    for r in report:
        print("  " + r)
    print(f"Всего строк: {len(src.splitlines())}")
else:
    print("НИЧЕГО НЕ ИЗМЕНЕНО")
    for r in report:
        print("  " + r)