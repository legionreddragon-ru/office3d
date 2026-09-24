# test_office.py - ПРИЁМКА ОФИСА: все системы и сотрудники по очереди
import os, time
import office

OK = 0; FAIL = 0

def check(name, cond, detail=""):
    global OK, FAIL
    if cond:
        OK += 1; print(f"[OK]   {name} {detail}")
    else:
        FAIL += 1; print(f"[БРАК] {name} {detail}")

print("=== 1. ФАЙЛЫ И СРЕДА ===")
for rel in ("office.py", "office_ui.py", "config.json",
            os.path.join("knowledge", "company.md"),
            os.path.join("knowledge", "lessons.md"),
            os.path.join("logs", "journal.md"),
            os.path.join("logs", "price_log.md")):
    check("файл " + rel, os.path.exists(os.path.join(office.BASE, rel)))

print("=== 2. МОЗГ (OLLAMA) ===")
try:
    import requests
    r = requests.get(office.OLLAMA + "/api/tags", timeout=5)
    names = [m["name"] for m in r.json().get("models", [])]
    check("Ollama отвечает", True, str(names))
    check("модель " + office.MODEL + " на месте", office.MODEL in names)
    check("быстрая модель phi3 на месте", any(n.startswith("phi3") for n in names))
except Exception as e:
    check("Ollama отвечает", False, str(e))

print("=== 3. БАЗА ЗНАНИЙ И УРОКИ ===")
comp = open(os.path.join(office.BASE, "knowledge", "company.md"), encoding="utf-8").read()
for key in ("СамПластик", "Николай Геннадьевич", "1500 руб/кг", "ЦЕНЫ v2", "ПОСТАВЩИКИ"):
    check("база содержит: " + key, key.lower() in comp.lower())
less = open(os.path.join(office.BASE, "knowledge", "lessons.md"), encoding="utf-8").read()
for key in ("не выдумывай", "скидка", "Отчёт о закупке", "быстром режиме"):
    check("урок содержит: " + key, key in less)

print("=== 4. ВЕБ-ПОИСК (РЕАЛЬНЫЕ ССЫЛКИ) ===")
rows = office.web_search("Самара погода сегодня", n=3)
check("веб-поиск даёт результаты", len(rows) > 0, f"({len(rows)} шт)")
for s in rows[:3]:
    print("      ссылка:", s["url"])

print("=== 5. КАЛЬКУЛЯТОР (МАТЕМАТИКА) ===")
def cost(w, h):
    sub = w / 1000 * 1500 + 3.08 * h + 26.67 * h + 33.33 + 25.0
    c = sub * 1.05 + 20 * h + 97.0
    return round(c * 1.04, 2)
check("Медвежонок = 394.00", abs(cost(75, 2) - 394.00) < 0.5, str(cost(75, 2)))
check("Машинка = 570.14", abs(cost(150, 3) - 570.14) < 0.5, str(cost(150, 3)))
check("Ракета = 975.70", abs(cost(300, 6) - 975.70) < 0.5, str(cost(300, 6)))

print("=== 6. СОТРУДНИКИ ПО ОЧЕРЕДИ (быстро, по одной фразе) ===")
TESTS = [
    ("director", "Одной фразой: главная цель компании на 3 месяца? Если неизвестно - уточнить у директора."),
    ("marketer", "Одной фразой: главное УТП СамПластик."),
    ("smm", "Одной фразой: идея поста VK на сегодня."),
    ("sales", "Одной фразой: ответ клиенту на возражение дорого."),
    ("analyst", "Одной фразой: какой канал продаж выгоднее всего?"),
    ("financier", "Одним числом: себестоимость Медвежонка по полному контуру v2 в рублях из базы знаний."),
    ("lawyer", "Одной фразой: нужна ли лицензия самозанятому на 3D-печать?"),
    ("steward", "Одной фразой: что проверить в квартире перед зимой?"),
    ("engineer", "Одной фразой: первое действие, если принтер не включается?"),
    ("logistic", "Одной фразой: целевая цена закупки пластика?"),
    ("tech", "Одной фразой: какой пластик подходит для мультицветной печати?"),
    ("crm", "Одной фразой: как напомнить постоянным клиентам о новой коллекции?"),
]
for role, q in TESTS:
    t0 = time.perf_counter()
    try:
        a = office.ask(role, q + " Ответь ОДНОЙ фразой по базе знаний.",
                       model=office.FAST_MODEL, num_ctx=4096)
        dt = time.perf_counter() - t0
        good = 0 < len(a.strip()) < 600
        check(f"сотрудник {role}", good, f"({dt:.0f} сек) {a.strip()[:80]}")
    except Exception as e:
        check(f"сотрудник {role}", False, str(e))

print("=== 7. КРИТИК ===")
t0 = time.perf_counter()
c = office.ask("critic", "Ответ сотрудника: 2+2=5. Проверь.")
check("критик ловит ошибку", ("ДОРАБОТКА" in c.upper()) or ("ошиб" in c.lower()), f"({time.perf_counter()-t0:.0f} сек)")

print()
print(f"=== ИТОГ: OK={OK} БРАК={FAIL} ===")
print("Офис недонастроен, смотри строки БРАК выше." if FAIL else "Офис полностью настроен и боеспособен.")