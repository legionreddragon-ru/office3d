# test_fair_reminders.py - удаление ярмарки забирает её напоминания
import os
import tempfile
import shutil
import office_db as db

TMP = tempfile.mkdtemp(prefix="fair_rem_test_")
db.DB_PATH = os.path.join(TMP, "t.db")
db.init_db()
db.migrate_db()

fid = db.add_fair("2026-11-05", "test", "mall", 1000.0, 5000.0, "", "")
db.add_reminder("2026-11-02", "подготовить пост-анонс к ярмарке 'test'", "ярмарка")
db.add_reminder("2026-11-06", "посчитать итоги ярмарки 'test'", "ярмарка")
db.add_reminder("2026-11-01", "позвонить клиенту", "клиент")

before = len(db.list_reminders("open"))
db.delete_fair(fid)
after = db.list_reminders("open")

assert before == 3, before
assert len(after) == 1, [r["text"] for r in after]
assert "позвонить клиенту" in after[0]["text"], [r["text"] for r in after]
print("ТЕСТ OK: ярмарка удалена вместе с 2 напоминаниями, чужое напоминание уцелело")
shutil.rmtree(TMP, ignore_errors=True)