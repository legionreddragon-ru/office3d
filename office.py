# office.py - ОФИС-3D v4 (авто-диспетчеризация через директора + быстрый режим)
import json, os, re, sys, time, datetime
import requests

BASE = os.path.dirname(os.path.abspath(__file__))

DEFAULT_ROLES = {
    "director": {"prompt": "Ты - исполнительный директор офиса. Получив задачу от директора компании, разбей её на 2-5 подзадач для сотрудников. Для каждой подзадачи укажи: роль, текст задачи, режим (FAST для списков/структур/черновиков, FULL для творческих/финансовых/юридических задач). Отвечай СТРОГО в JSON-формате: {\"plan\": [{\"role\": \"marketer\", \"task\": \"текст\", \"mode\": \"FULL\"}, ...], \"final_task\": \"итоговая задача для сводки\"}. Без пояснений, только JSON."},
    "marketer": {"prompt": "Ты - маркетолог СамПластик. УТП: мультицвет без покраски (AMS), кастом по фото. Без выдуманных фактов и цен."},
    "sales": {"prompt": "Ты - менеджер по продажам СамПластик. Ответы вежливо и с цифрами из базы знаний."},
    "analyst": {"prompt": "Ты - аналитик СамПластик. Таблицы, вилки цен, ссылки, гипотезы помечай ГИПОТЕЗА."},
    "tech": {"prompt": "Ты - технолог 3D-печати на Bambu Lab P1S Combo. Настройки, дефекты, материалы."},
    "logistic": {"prompt": "Ты - закупщик СамПластик. Пластик оптом, поставщики, доставка."},
    "critic": {"prompt": "Ты - строгий редактор-контролёр. ВЕРДИКТ: ОК или ВЕРДИКТ: ДОРАБОТКА + комментарии."},
    "smm": {"prompt": "Ты - SMM-менеджер группы VK СамПластик. Живой язык, без выдуманных цен."},
    "financier": {"prompt": "Ты - финансист Галина Ивановна. Формула v2, налоги, вычеты. Только цифры из базы знаний."},
    "lawyer": {"prompt": "Ты - юрист Михаил. РФ: ЗоЗПП, НК, ЖК, пособия. Номера статей, шаги."},
    "steward": {"prompt": "Ты - дворецкий Степан. Квартира/дом: регламенты, инвентарь, ремонты."},
    "engineer": {"prompt": "Ты - инженер Тимур. Диагностика, регламенты, безопасность."},
    "crm": {"prompt": "Ты - менеджер Ольга. Постоянные клиенты, окружение, напоминания."}
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

bootstrap()
CFG = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
ROLES = CFG.get("roles", DEFAULT_ROLES)
OLLAMA = CFG.get("ollama_url", "http://127.0.0.1:11434")
MODEL = CFG.get("model", "qwen2.5:7b")
FAST_MODEL = CFG.get("fast_model", "phi3:mini")

def now(): return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(msg):
    line = f"[{now()}] {msg}"
    print(line)
    with open(os.path.join(BASE, "logs", "office.log"), "a", encoding="utf-8") as f:
        f.write(line + "\n")

def read_txt(rel, limit):
    p = os.path.join(BASE, rel)
    if not os.path.exists(p): return ""
    return open(p, encoding="utf-8").read()[:limit]

def system_for(role):
    base = ROLES.get(role, {}).get("prompt", DEFAULT_ROLES.get(role, {}).get("prompt", ""))
    know = read_txt(os.path.join("knowledge", "company.md"), 4000)
    lessons = read_txt(os.path.join("knowledge", "lessons.md"), 2000)
    if know: base += "\n\nДАННЫЕ КОМПАНИИ:\n" + know
    if lessons: base += "\n\nУРОКИ ПРОШЛОГО:\n" + lessons
    return base

def ask(role, text, temperature=0.4, model=None, num_ctx=8192):
    msgs = [{"role": "system", "content": system_for(role)}, {"role": "user", "content": text}]
    try:
        r = requests.post(OLLAMA + "/api/chat", json={
            "model": model or MODEL, "messages": msgs, "stream": False,
            "keep_alive": "5m", "options": {"num_ctx": num_ctx, "temperature": temperature}}, timeout=900)
        r.raise_for_status()
    except requests.exceptions.ConnectionError:
        raise SystemExit("НЕ МОГУ соединиться с Ollama.")
    return r.json()["message"]["content"]

def web_search(query, n=5):
    try: from ddgs import DDGS
    except ImportError: from duckduckgo_search import DDGS
    for attempt in range(3):
        try:
            with DDGS() as d:
                rows = list(d.text(query, max_results=n))
            if rows:
                return [{"i": i+1, "title": r.get("title",""), "url": r.get("href",""),
                         "snippet": r.get("body","")} for i, r in enumerate(rows)]
        except Exception as e:
            log(f"Веб-поиск: попытка {attempt+1} не удалась ({e})")
        time.sleep(3 * (attempt + 1))
    return []

def fetch_page(url, limit=6000):
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
        r.raise_for_status()
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script","style","nav","footer","header"]): t.decompose()
        return re.sub(r"\s+", " ", soup.get_text(" ", strip=True))[:limit]
    except Exception as e:
        return f"(страницу загрузить не удалось: {e})"

def gather_sources(query):
    rows = web_search(query)
    if not rows:
        return """(ВЕБ-ПОИСК СЕЙЧАС НЕ ВЫДАЛ ДАННЫХ.
Отвечай ТОЛЬКО по базе знаний; всё, чего не хватает, помечай "уточнить у директора".)"""
    blob = ""
    for s in rows:
        blob += f"\n[ИСТОЧНИК {s['i']}] {s['title']} - {s['url']}\n{s['snippet']}\n"
        time.sleep(1)
    for s in rows[:2]:
        blob += f"\n[ИСТОЧНИК {s['i']}, ТЕКСТ СТРАНИЦЫ]:\n" + fetch_page(s["url"]) + "\n"
        time.sleep(1)
    return blob

def save_report(name, text):
    fn = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M") + "_" + re.sub(r"\W+", "_", name)[:30] + ".md"
    p = os.path.join(BASE, "reports", fn)
    open(p, "w", encoding="utf-8").write(text)
    log("Отчёт сохранён: " + p)
    return p

def journal(entry):
    with open(os.path.join(BASE, "logs", "journal.md"), "a", encoding="utf-8") as f:
        f.write(f"- [{now()}] {entry}\n")

def parse_plan(text):
    """Извлекает JSON из ответа Павла (директора офиса)."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if m: text = m.group(1).strip()
    m = re.search(r"\{[\s\S]*\}", text)
    if m: text = m.group(0)
    try:
        return json.loads(text)
    except:
        return None

def dispatch_task(main_task, use_web=False, callback=None):
    """Авто-диспетчеризация: Павел получает задачу, разбивает, запускает сотрудников по очереди."""
    log(f"ДИСПЕТЧЕРИЗАЦИЯ: {main_task}")
    
    # 1. Павел составляет план
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
    
    # 2. Выполняем подзадачи по очереди
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
        if callback: callback(i, total_steps, role, mode, task)
        
        context = ""
        if use_web:
            context = "ДАННЫЕ ВЕБ-ПОИСКА:\n" + gather_sources(task)
        
        # Предыдущие результаты - как контекст для следующих
        prev_results = "\n".join([f"[{r['role']}]: {r['result'][:300]}" for r in results])
        full_task = task
        if prev_results:
            full_task += f"\n\nРЕЗУЛЬТАТЫ ПРЕДЫДУЩИХ ШАГОВ:\n{prev_results}"
        
        try:
            result = ask(role, context + "\nЗАДАЧА: " + full_task,
                         model=(FAST_MODEL if fast else MODEL),
                         num_ctx=(4096 if fast else 8192))
            results.append({"role": role, "task": task, "result": result, "mode": mode})
        except Exception as e:
            log(f"    Ошибка: {e}")
            results.append({"role": role, "task": task, "result": f"ОШИБКА: {e}", "mode": mode})
    
    # 3. Итоговая сводка от Павла
    final_task = plan.get("final_task", "Сведи все результаты в итоговый отчёт.")
    summary_context = "\n\n".join([
        f"=== {r['role']} ({r['mode']}) ===\nЗадача: {r['task']}\nРезультат: {r['result']}"
        for r in results
    ])
    summary = ask("director",
                  f"ИСХОДНАЯ ЗАДАЧА: {main_task}\n\n{summary_context}\n\n{final_task}\nСведи результаты в итоговый отчёт с выводами.",
                  model=MODEL, num_ctx=8192)
    
    # 4. Собираем финальный отчёт
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
    """Обычный режим: одна задача одному сотруднику."""
    context = ""
    if use_web:
        context = "ДАННЫЕ ВЕБ-ПОИСКА:\n" + gather_sources(task)
    draft = ask(role, context + "\nЗАДАЧА: " + task,
                model=(FAST_MODEL if fast else MODEL),
                num_ctx=(4096 if fast else 8192))
    critic = ask("critic", f"ЗАДАЧА: {task}\n\nОТВЕТ:\n{draft}\n\nВЕРДИКТ: ОК или ДОРАБОТКА + комментарии.")
    if "ДОРАБОТКА" in critic.upper()[:40]:
        draft = ask(role, context + f"\nЗАДАЧА: {task}\nВЕРСИЯ 1:\n{draft}\nКРИТИКА:\n{critic}\nСделай улучшенную версию.",
                    model=(FAST_MODEL if fast else MODEL),
                    num_ctx=(4096 if fast else 8192))
    final = f"# ЗАДАЧА: {task}\n\nРОЛЬ: {role}\n\n{draft}\n\n---\nКритик: {'пропущен (быстрый)' if fast else 'пройден'}\n"
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
    try: main()
    except Exception as e: log("ОШИБКА: " + str(e)); print("Ошибка:", e)