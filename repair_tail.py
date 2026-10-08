# repair_tail.py - безопасно заменяет хвост office.py
MARK = "def dispatch_task("
tail = r'''
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
'''
path = "office.py"
src = open(path, encoding="utf-8").read()
i = src.find(MARK)
if i < 0:
    print("СТОП: не нашёл строку def dispatch_task - файл НЕ менял")
else:
    head = src[:i]
    open(path, "w", encoding="utf-8").write(head + tail.strip() + "\n")
    print("ГОТОВО: хвост перезаписан, всего строк:", len((head + tail.strip()).splitlines()))