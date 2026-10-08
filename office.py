# office.py - ОФИС-3D v13 (анти-галлюцинации + проверка старта)
import json, os, re, sys, time, datetime, urllib.parse
import requests

BASE = os.path.dirname(os.path.abspath(__file__))
VERSION = "13"

DEFAULT_ROLES = {
    "director": {"prompt": "Ты - исполнительный директор офиса. Получив задачу от директора компании, разбей её на 2-5 подзадач для сотрудников. Для каждой подзадачи укажи: роль, текст задачи, режим (FAST для списков/структур/черновиков, FULL для творческих/финансовых/юридических задач). Отвечай СТРОГО в JSON-формате: {\"plan\": [{\"role\": \"marketer\", \"task\": \"текст\", \"mode\": \"FULL\"}, ...], \"final_task\": \"итоговая задача для сводки\"}. Без пояснений, только JSON."},
    "marketer": {"prompt": "Ты - маркетолог СамПластик. УТП: мультицвет без покраски (AMS), кастом по фото. Без выдуманных фактов и цен. Смотри на ДОСКУ ОБЪЯВЛЕНИЙ перед ответом."},
    "sales": {"prompt": "Ты - менеджер по продажам СамПластик. Ответы вежливо и с цифрами из базы знаний. Опирайся на ДОСКУ ОБЪЯВЛЕНИЙ."},
    "analyst": {"prompt": "Ты - аналитик СамПластик. Таблицы, вилки цен, ссылки, гипотезы помечай ГИПОТЕЗА. Если нашел цену или дату - ОБЯЗАТЕЛЬНО запиши её на ДОСКУ с источником."},
    "tech": {"prompt": "Ты - технолог 3D-печати на Bambu Lab P1S Combo. Настройки, дефекты, материалы. Смотри на ДОСКУ для цен пластика."},
    "logistic": {"prompt": "Ты - закупщик СамПластик. Пластик оптом, поставщики, доставка. Найденные цены ОБЯЗАТЕЛЬНО записывай на ДОСКУ с прямой ссылкой на товар."},
    "critic": {"prompt": "Ты - строгий редактор-контролёр. ВЕРДИКТ: ОК или ВЕРДИКТ: ДОРАБОТКА + комментарии. Проверяй: выдуманные цифры, цифры без источников, логические дыры."},
    "smm": {"prompt": "Ты - SMM-менеджер группы VK СамПластик. Живой язык, без выдуманных цен. Смотри на ДОСКУ для цен и дат ярмарок."},
    "financier": {"prompt": "Ты - финансист Галина Ивановна. Формула v2, налоги, вычеты. Только цифры из базы знаний и ДОСКИ. Любая цифра без источника запрещена."},
    "lawyer": {"prompt": "Ты - юрист Михаил. РФ: ЗоЗПП, НК, ЖК, пособия. Номера статей, шаги. Завершай фразой: Это информационная справка, а не юридическая консультация."},
    "steward": {"prompt": "Ты - дворецкий Степан. Квартира/дом: регламенты, инвентарь, ремонты. Чек-листы и сроки."},
    "engineer": {"prompt": "Ты - инженер Тимур. Диагностика, регламенты, безопасность. Газ и высоковольтная электрика - только специалист с допуском."},
    "crm": {"prompt": "Ты - менеджер Ольга. Постоянные клиенты, окружение, напоминания. Тон тёплый, без спама."}
}

ROLE_ADDONS = {
    "logistic": '''

⚠️ КРИТИЧЕСКИ ВАЖНОЕ ПРАВИЛО (ЗАПРЕТ ГАЛЛЮЦИНАЦИЙ):

ТЫ НЕ ИМЕЕШЬ ПРАВА ВЫДУМЫВАТЬ КАРТОЧКИ ТОВАРОВ!

Если в блоке WEB SEARCH RESULTS ниже ты ВИДИШЬ реальные данные (названия, цены, РАЗНЫЕ ссылки, имена продавцов) - ТОЛЬКО ТОГДА выводи их и пиши на Доску.

Если реальных данных НЕТ - напиши: РЕАЛЬНЫХ ПРЕДЛОЖЕНИЙ В ВЕБ-ПОИСКЕ НЕ НАЙДЕНО, и дай ссылки-кандидаты для ручной проверки директором.

ПРИЗНАКИ ГАЛЛЮЦИНАЦИИ (ЗАПРЕЩЕНО ВЫВОДИТЬ):
- все карточки с одной и той же ссылкой (ДАЖЕ если бренды разные)
- цены прогрессией (149, 159, 169...)
- продавец без имени, просто "Продавец"
- рейтинги одинаковые (4.6, 4.6, 4.6...) - это ВЫДУМКА
- отзывы прогрессией (526, 375, 327...)
- одинаковые ссылки для разных товаров (Sunlu PETG и Creality PLA не могут иметь одну ссылку)

Если ты видишь эти признаки - НЕ ВЫВОДИ карточки, напиши "РЕАЛЬНЫХ ПРЕДЛОЖЕНИЙ НЕ НАЙДЕНО".
''',
    "smm": '''

⚠️ КРИТИЧЕСКИ ВАЖНОЕ ПРАВИЛО (ФОРМАТ ОТВЕТА):

ТВОЙ ОТВЕТ СОСТОИТ ИЗ 2 ЧАСТЕЙ:

ЧАСТЬ 1: ТЕКСТЫ ПОСТОВ. Пиши посты обычным текстом, БЕЗ JSON-блоков внутри постов. Каждый пост: живой язык, УТП (мультицвет без покраски AMS или кастом по фото), цены ТОЛЬКО из базы знаний или с Доски, без выдуманных ссылок на посты VK.

ЧАСТЬ 2: БЛОК ДЛЯ ДОСКИ. В САМОМ КОНЕЦЕ ответа добавь одной строкой: ```json {"update": {"название_факта": {"value": "значение", "source": "https://ссылка-или-слово-база"}}} ```

ЗАПРЕЩЕНО: вставлять JSON внутрь постов; выдумывать ссылки вида wall-193633899_123456789; слово "скидка" без указания старой цены.
''',
    "critic": '''

⚠️ УСИЛЕННАЯ ПРОВЕРКА НА ГАЛЛЮЦИНАЦИИ (ставь ДОРАБОТКА если видишь):
1. все ссылки одинаковые (копипаст)
2. цены прогрессией (149, 159, 169...)
3. рейтинги одинаковые (4.6, 4.6, 4.6...)
4. продавец без имени
5. JSON-блоки внутри текстов постов
6. фейковые ссылки на несуществующие страницы
7. слово "скидка" без старой цены
''',
    "analyst": "\n\nОПЕРАЦИОННОЕ ПРАВИЛО: любые даты, места, цены - только со ссылкой на источник или с пометкой ГИПОТЕЗА. Если ничего не найдено - НЕ пиши блок update на Доску вовсе.",
    "financier": "\n\nОПЕРАЦИОННОЕ ПРАВИЛО: цифры, рассчитанные из данных компании, можно писать на доску с источником 'база'.",
    "tech": "\n\nОПЕРАЦИОННОЕ ПРАВИЛО: граммы, время и себестоимость, рассчитанные из базы, можно писать на доску с источником 'база'."
}

COMPANY_TEMPLATE = "# О КОМПАНИИ\n- Бренд/название:\n- Принтер друга (модель, сопло, стол):\n- Материалы (какой пластик сейчас):\n- Текущие товары и цены:\n- Себестоимость (пластик/грамм, электричество, час работы):\n- Каналы продаж (Avito/VK/ярмарки):\n- Целевая аудитория:\n- Главная цель на 3 месяца:\n"

def bootstrap():
    for d in ("reports", "logs", "knowledge"):
        os.makedirs(os.path.join(BASE, d), exist_ok=True)
    cfg = os.path.join(BASE, "config.json")
    if not os.path.exists(cfg):
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump({"ollama_url": "http://127.0.0.1:11434", "model": "qwen2.5:7b",
                       "fast_model": "phi3:mini", "roles": DEFAULT_ROLES}, f, ensure_ascii=False, indent=2)
    comp = os.path.join(BASE, "knowledge", "company.md")
    if not os.path.exists(comp):
        with open(comp, "w", encoding="utf-8") as f:
            f.write(COMPANY_TEMPLATE)
    less = os.path.join(BASE, "knowledge", "lessons.md")
    if not os.path.exists(less):
        open(less, "w", encoding="utf-8").write("")
    plog = os.path.join(BASE, "logs", "price_log.md")
    if not os.path.exists(plog):
        with open(plog, "w", encoding="utf-8") as f:
            f.write("# История цен пластика\n")
    bb = os.path.join(BASE, "blackboard.json")
    if not os.path.exists(bb):
        with open(bb, "w", encoding="utf-8") as f:
            f.write("{}")

bootstrap()
CFG = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
ROLES = CFG.get("roles", DEFAULT_ROLES)
OLLAMA = CFG.get("ollama_url", "http://127.0.0.1:11434")
MODEL = CFG.get("model", "qwen2.5:7b")
FAST_MODEL = CFG.get("fast_model", "phi3:mini")

print(f"ОФИС-3D: загружена версия {VERSION}")

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    line = f"[{now()}] {msg}"
    print(line)
    with open(os.path.join(BASE, "logs", "office.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_txt(rel, limit):
    p = os.path.join(BASE, rel)
    if not os.path.exists(p):
        return ""
    with open(p, encoding="utf-8") as f:
        return f.read()[:limit]

BB_FILE = os.path.join(BASE, "blackboard.json")
BASE_ALLOWED_ROLES = ("financier", "tech")
META_JUNK = ("не найдено", "нет данных", "не нашел", "не нашёл", "уточнить", "no data", "цен с прямой ссылкой не найдено", "реальных предложений")

def load_blackboard():
    try:
        if os.path.exists(BB_FILE):
            with open(BB_FILE, encoding="utf-8") as f:
                raw = json.load(f)
            out = {}
            for k, v in raw.items():
                if isinstance(v, dict):
                    out[k] = v
                else:
                    out[k] = {"value": str(v), "source": "старый формат", "tag": "OLD", "date": ""}
            return out
    except Exception:
        pass
    return {}

def save_blackboard(data):
    with open(BB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_url_alive(url, timeout=12):
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
        return False, str(e)[:50]


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

def update_blackboard_from_text(text, role=""):
    m = re.search(r"```(?:json)?\s*({.*?\"update\".*?})\s*```", text, re.IGNORECASE | re.DOTALL)
    if not m:
        m = re.search(r'({\s*"update"\s*:\s*{.*?"value".*?"source".*?}\s*})', text, re.IGNORECASE | re.DOTALL)
    if not m:
        return
    try:
        data = json.loads(m.group(1))
    except Exception:
        return
    upd = data.get("update")
    if not isinstance(upd, dict):
        return
    bb = load_blackboard()
    added = []
    for k, v in upd.items():
        if isinstance(v, dict):
            val = str(v.get("value", "")).strip()
            src = str(v.get("source", "")).strip()
        else:
            val = str(v).strip()
            src = ""
        if not val:
            continue
        low = val.lower()
        if any(j in low for j in META_JUNK):
            log(f"ДОСКА: факт '{k}' ОТКЛОНЁН (это отговорка, а не факт): {val}")
            continue
        if src.startswith("http"):
            alive, reason = check_url_alive(src)
            if not alive:
                log(f"ДОСКА: факт '{k}' ОТКЛОНЁН (ссылка мёртвая: {reason}): {src}")
                continue
            tag = "WEB"
        elif src.lower() in ("база", "base", "company.md", "калькулятор"):
            if role in BASE_ALLOWED_ROLES:
                tag = "BASE"
            else:
                log(f"ДОСКА: факт '{k}' ОТКЛОНЁН (роль {role} не имеет права писать источник 'база')")
                continue
        else:
            log(f"ДОСКА: факт '{k}' ОТКЛОНЁН (нет прямой ссылки или слова 'база'). Значение было: {val}")
            continue
        bb[k] = {"value": val, "source": src, "tag": tag, "date": now()}
        added.append(k)
    if added:
        save_blackboard(bb)
        log(f"ДОСКА обновлена: {added}")

def deduplicate_lessons():
    less_file = os.path.join(BASE, "knowledge", "lessons.md")
    if not os.path.exists(less_file):
        return
    with open(less_file, encoding="utf-8") as f:
        lines = f.read().splitlines()
    seen = set()
    unique_lines = []
    for line in lines:
        ls = line.strip()
        if ls and ls not in seen:
            seen.add(ls)
            unique_lines.append(line)
    if len(unique_lines) < len(lines):
        with open(less_file, "w", encoding="utf-8") as f:
            f.write("\n".join(unique_lines))
        log(f"Убрано {len(lines) - len(unique_lines)} дубликатов из lessons.md")

deduplicate_lessons()

def system_for(role):
    base = ROLES.get(role, {}).get("prompt", DEFAULT_ROLES.get(role, {}).get("prompt", ""))
    base += ROLE_ADDONS.get(role, "")
    know = read_txt(os.path.join("knowledge", "company.md"), 4000)
    lessons = read_txt(os.path.join("knowledge", "lessons.md"), 2000)
    if know:
        base += "\n\nДАННЫЕ КОМПАНИИ:\n" + know
    if lessons:
        base += "\n\nУРОКИ ПРОШЛОГО:\n" + lessons
    bb = load_blackboard()
    if bb:
        pretty = {k: v.get("value", "") for k, v in bb.items()}
        base += f"\n\n📋 ТЕКУЩИЕ ФАКТЫ НА ДОСКЕ ОБЪЯВЛЕНИЙ (ИСПОЛЬЗУЙ ИХ!):\n{json.dumps(pretty, ensure_ascii=False)}"
    base += ("\n\n⚠️ ПРАВИЛО ДОСКИ: если ты НАШЁЛ важный факт, добавь в САМЫЙ КОНЕЦ ответа одной строкой блок вида: "
             "```json {\"update\": {\"название_факта\": {\"value\": \"значение\", \"source\": \"https://прямая-ссылка\"}}} ``` "
             "Источник - ТОЛЬКО прямая ссылка или слово 'база' (только для финансиста и технолога). "
             "Если НИЧЕГО не нашёл - НЕ пиши блок update вовсе. Факт без источника система отклонит как подделку.")
    return base

def ask(role, text, temperature=0.4, model=None, num_ctx=8192):
    msgs = [{"role": "system", "content": system_for(role)}, {"role": "user", "content": text}]
    try:
        r = requests.post(OLLAMA + "/api/chat", json={
            "model": model or MODEL, "messages": msgs, "stream": False,
            "keep_alive": "5m", "options": {"num_ctx": num_ctx, "temperature": temperature}}, timeout=1800)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise SystemExit("НЕ МОГУ соединиться с Ollama.")
    return r.json()["message"]["content"]

def _clean_href(href):
    if "uddg=" in href:
        q = urllib.parse.urlparse(href).query
        real = urllib.parse.parse_qs(q).get("uddg", [""])[0]
        if real:
            return urllib.parse.unquote(real)
    return href

def _ddg_lib(query, n):
    try:
        from ddgs import DDGS
    except ImportError:
        log("Веб-поиск: библиотека ddgs не установлена")
        return []
    try:
        with DDGS() as d:
            rows = list(d.text(query, max_results=n, region="ru-ru"))
        if rows:
            log("Веб-поиск: сработала библиотека (region=ru-ru)")
            return [{"i": i+1, "title": r.get("title",""), "url": r.get("href",""),
                     "snippet": r.get("body","")} for i, r in enumerate(rows)]
    except Exception as e:
        log(f"Веб-поиск: библиотека не смогла ({e})")
    return []

def _ddg_html(query, n):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
    for endpoint in ("https://html.duckduckgo.com/html/?q=", "https://lite.duckduckgo.com/lite/?q="):
        try:
            url = endpoint + urllib.parse.quote(query + " Россия")
            r = requests.get(url, headers=headers, timeout=15)
            r.raise_for_status()
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(r.text, "html.parser")
            out = []
            for a in soup.select("a.result__a, a.result-link, table a"):
                href = a.get("href", "")
                if not href.startswith("http"):
                    continue
                href = _clean_href(href)
                if not href.startswith("http"):
                    continue
                title = a.get_text(" ", strip=True)
                snip = ""
                par = a.find_parent(["div", "tr"])
                if par:
                    snip = par.get_text(" ", strip=True)[:300]
                out.append({"i": len(out)+1, "title": title, "url": href, "snippet": snip})
                if len(out) >= n:
                    break
            if out:
                log(f"Веб-поиск: сработал запасной канал {endpoint.split('/')[2]}")
                return out
        except Exception as e:
            log(f"Веб-поиск: канал {endpoint.split('/')[2]} не смог ({e})")
    return []

def web_search(query, n=5):
    rows = _ddg_lib(query, n)
    if rows:
        return rows
    rows = _ddg_html(query, n)
    if rows:
        return rows
    log("Веб-поиск: ВСЕ каналы молчат")
    return []

def fetch_page(url, limit=8000):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer","header"]):
            t.decompose()
        return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:limit]
    except Exception as e:
        return f"(страницу загрузить не удалось: {e})"

def gather_sources(query, role=""):
    if role == "logistic":
        review_query = "лучший PETG PLA пластик для 3D принтера 2026 рейтинг обзор"
        log("Фёдор: ищу обзоры пластика")
        review_rows = web_search(review_query, n=5)
        marketplace_queries = [
            "PETG пластик 1 кг купить Ozon",
            "PLA пластик 1 кг купить Wildberries",
            "PETG PLA пластик AliExpress Россия"
        ]
        blob = "WEB SEARCH RESULTS (обзоры и рейтинги пластика):\n"
        if review_rows:
            for s in review_rows:
                blob += f"\n[ИСТОЧНИК {s['i']}] {s['title']} - {s['url']}\n{s['snippet']}\n"
                time.sleep(1)
            for s in review_rows[:2]:
                blob += f"\n[ТЕКСТ ОБЗОРА {s['i']}]:\n" + fetch_page(s["url"]) + "\n"
                time.sleep(1)
        else:
            blob += "(обзоров не найдено)\n"
        blob += "\n\nССЫЛКИ ДЛЯ РУЧНОЙ ПРОВЕРКИ (директор сам проверит цены):\n"
        for mq in marketplace_queries:
            rows = web_search(mq, n=2)
            if rows:
                blob += f"\nПоиск '{mq}':\n"
                for s in rows:
                    blob += f"  - {s['title']}: {s['url']}\n"
            time.sleep(1)
        blob += ("\n\nИНСТРУКЦИЯ: выведи марки пластика из обзоров с ценами если они там реально указаны; "
                 "дай список ссылок для ручной проверки. НЕ ВЫДУМЫВАЙ карточки товаров. "
                 "Если реальных данных нет - напиши РЕАЛЬНЫХ ПРЕДЛОЖЕНИЙ В ВЕБ-ПОИСКЕ НЕ НАЙДЕНО.")
        return blob
    rows = web_search(query, n=7)
    if not rows:
        return ("(ВЕБ-ПОИСК СЕЙЧАС НЕ ВЫДАЛ ДАННЫХ.\n"
                "Отвечай ТОЛЬКО по базе знаний и ДОСКЕ; всё, чего не хватает, помечай 'уточнить у директора'.\n"
                "ЗАПРЕЩЕНО выдавать цифры из базы за найденные в интернете. Блок update на Доску НЕ пиши.)")
    blob = ""
    for s in rows:
        blob += f"\n[ИСТОЧНИК {s['i']}] {s['title']} - {s['url']}\n{s['snippet']}\n"
        time.sleep(1)
    for s in rows[:3]:
        blob += f"\n[ИСТОЧНИК {s['i']}, ТЕКСТ СТРАНИЦЫ]:\n" + fetch_page(s["url"]) + "\n"
        time.sleep(1)
    blob += ("\n\nИНСТРУКЦИЯ: если среди источников НЕТ прямой ссылки на товар с ценой - напиши прямо: "
             "ЦЕН С ПРЯМОЙ ССЫЛКОЙ НЕ НАЙДЕНО, и дай ссылки-кандидаты. Не подставляй цифры из базы и НЕ пиши блок update.")
    return blob

def save_report(name, text):
    fn = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M") + "_" + re.sub(r"\W+", "_", name)[:30] + ".md"
    p = os.path.join(BASE, "reports", fn)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    log("Отчёт сохранён: " + p)
    return p

def journal(entry):
    with open(os.path.join(BASE, "logs", "journal.md"), "a", encoding="utf-8") as f:
        f.write(f"- [{now()}] {entry}\n")

def parse_plan(text):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m:
        text = m.group(1).strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        text = m.group(0)
    try:
        return json.loads(text)
    except Exception:
        return None

def dispatch_task(main_task, use_web=False, callback=None):
    log(f"ДИСПЕТЧЕРИЗАЦИЯ: {main_task}")
    plan_prompt = f"""ЗАДАЧА ОТ ДИРЕКТОРА КОМПАНИИ: {main_task}

Составь план из 2-5 подзадач для сотрудников офиса.
Режим FAST - для простых задач (списки, структуры, черновики).
Режим FULL - для творческих, финансовых, юридических задач.

Возможные роли: marketer, smm, sales, analyst, financier, lawyer, steward, engineer, logistic, tech, crm.

Ответь СТРОГО в JSON без пояснений:
{{"plan": [{{"role": "...", "task": "...", "mode": "FAST|FULL"}}], "final_task": "итоговая сводка"}}"""
    plan_text = ask("director", plan_prompt, model=MODEL, num_ctx=8192)
    plan = parse_plan(plan_text)
    if not plan or "plan" not in plan:
        log("Павел не смог составить план, работаю как обычный сотрудник.")
        return run_single_task("director", main_task, use_web)
    results = []
    total_steps = len(plan["plan"])
    for i, step in enumerate(plan["plan"], 1):
        role = step.get("role", "director")
        task = step.get("task", "")
        mode = step.get("mode", "FULL").upper()
        fast = (mode == "FAST")
        if role not in ROLES:
            log(f"  Шаг {i}/{total_steps}: неизвестная роль {role}, пропускаю")
            continue
        log(f"  Шаг {i}/{total_steps}: {role} ({mode}) -> {task[:60]}")
        if callback:
            callback(i, total_steps, role, mode, task)
        context = ""
        if use_web:
            context = "ДАННЫЕ ВЕБ-ПОИСКА:\n" + gather_sources(task, role=role)
        prev_results = "\n".join([f"[{r['role']}]: {r['result'][:300]}" for r in results])
        full_task = task
        if prev_results:
            full_task += f"\n\nРЕЗУЛЬТАТЫ ПРЕДЫДУЩИХ ШАГОВ:\n{prev_results}"
        try:
            result = ask(role, context + "\nЗАДАЧА: " + full_task,
                         model=(FAST_MODEL if fast else MODEL),
                         num_ctx=(4096 if fast else 8192))
            update_blackboard_from_text(result, role)
            if not fast:
                cr = ask("critic", f"ЗАДАЧА: {task}\n\nОТВЕТ:\n{result}\n\nВЕРДИКТ: ОК или ДОРАБОТКА + комментарии.",
                         model=MODEL, num_ctx=8192)
                if "ДОРАБОТКА" in cr.upper()[:40]:
                    result = ask(role, context + f"\nЗАДАЧА: {task}\nВЕРСИЯ 1:\n{result}\nКРИТИКА:\n{cr}\nСделай улучшенную версию.",
                                 model=(FAST_MODEL if fast else MODEL), num_ctx=(4096 if fast else 8192))
                    update_blackboard_from_text(result, role)
            results.append({"role": role, "task": task, "result": result, "mode": mode})
        except Exception as e:
            log(f"    Ошибка: {e}")
            results.append({"role": role, "task": task, "result": f"ОШИБКА: {e}", "mode": mode})
    final_task = plan.get("final_task", "Сведи все результаты в итоговый отчёт.")
    summary_context = "\n\n".join([
        f"=== {r['role']} ({r['mode']}) ===\nЗадача: {r['task']}\nРезультат: {r['result']}"
        for r in results
    ])
    summary = ask("director",
                  f"ИСХОДНАЯ ЗАДАЧА: {main_task}\n\n{summary_context}\n\n{final_task}\nСведи результаты в итоговый отчёт с выводами.",
                  model=MODEL, num_ctx=8192)
    report_parts = [f"# ЗАДАЧА (через диспетчеризацию): {main_task}\n"]
    report_parts.append(f"## План от Павла ({total_steps} шагов):\n")
    for i, step in enumerate(plan["plan"], 1):
        report_parts.append(f"{i}. **{step['role']}** ({step.get('mode','FULL')}): {step['task']}\n")
    report_parts.append("\n## Результаты по шагам:\n")
    for i, r in enumerate(results, 1):
        report_parts.append(f"### Шаг {i}: {r['role']} ({r['mode']})\n**Задача:** {r['task']}\n\n{r['result']}\n")
    report_parts.append(f"\n## Итог от Павла:\n\n{summary}\n")
    full_report = "\n".join(report_parts)
    path = save_report(main_task, full_report)
    journal(f"director (dispatch): задача '{main_task[:50]}' -> {os.path.basename(path)} ({total_steps} шагов)")
    return full_report, path, results

def run_single_task(role, task, use_web=False, fast=False):
    context = ""
    if use_web:
        context = "ДАННЫЕ ВЕБ-ПОИСКА:\n" + gather_sources(task, role=role)
    draft = ask(role, context + "\nЗАДАЧА: " + task,
                model=(FAST_MODEL if fast else MODEL),
                num_ctx=(4096 if fast else 8192))
    update_blackboard_from_text(draft, role)
    critic = ask("critic", f"ЗАДАЧА: {task}\n\nОТВЕТ:\n{draft}\n\nВЕРДИКТ: ОК или ДОРАБОТКА + комментарии.",
                 model=(FAST_MODEL if fast else MODEL), num_ctx=(4096 if fast else 8192))
    if "ДОРАБОТКА" in critic.upper()[:40]:
        draft = ask(role, context + f"\nЗАДАЧА: {task}\nВЕРСИЯ 1:\n{draft}\nКРИТИКА:\n{critic}\nСделай улучшенную версию.",
                    model=(FAST_MODEL if fast else MODEL), num_ctx=(4096 if fast else 8192))
        update_blackboard_from_text(draft, role)
    final = f"# ЗАДАЧА: {task}\n\nРОЛЬ: {role}\n\n{draft}\n\n---\nКритик: пройден\n"
    path = save_report(task, final)
    journal(f"{role}: задача '{task[:50]}' -> {os.path.basename(path)}")
    return draft, path, critic

def main():
    if len(sys.argv) < 2:
        print("Команды:\n  python office.py dispatch \"задача\" [--web]\n  python office.py task РОЛЬ \"текст\" [--web] [--fast]\n  python office.py lesson \"текст\"")
        return
    cmd = sys.argv[1]
    if cmd == "lesson":
        with open(os.path.join(BASE, "knowledge", "lessons.md"), "a", encoding="utf-8") as f:
            f.write(f"- [{now()}] {sys.argv[2]}\n")
        log("Урок записан.")
        return
    if cmd == "dispatch":
        task = sys.argv[2]
        use_web = "--web" in sys.argv
        result, path, _ = dispatch_task(task, use_web)
        print("\n===== ИТОГ =====\n")
        print(result)
        print("\nОтчёт:", path)
        return
    if cmd == "task":
        role, task = sys.argv[2], sys.argv[3]
        use_web = "--web" in sys.argv
        fast = "--fast" in sys.argv
        result, path, critic = run_single_task(role, task, use_web, fast)
        print("\n===== РЕЗУЛЬТАТ =====\n")
        print(result)
        print("\nОтчёт:", path)
        return

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log("ОШИБКА: " + str(e))
        print("Ошибка:", e)
