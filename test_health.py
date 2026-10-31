# test_health.py - проверка иммунной системы (диагностика + инциденты)
import os
import tempfile
import shutil
import office_db as db
import health_ui

TMP = tempfile.mkdtemp(prefix="health_test_")
db.DB_PATH = os.path.join(TMP, "t.db")
db.init_db()
db.migrate_db()
health_ui.BASE = TMP
health_ui.INC_FILE = os.path.join(TMP, "incidents.json")
os.makedirs(os.path.join(TMP, "accounting"), exist_ok=True)

finds = health_ui.run_checks()
assert isinstance(finds, list)
assert not any(f[0] == "db_integrity" for f in finds), finds

items = health_ui.load_incidents()
assert items == []
fid = health_ui.next_id(items)
assert fid.startswith("INC-")
items.append({"id": fid, "timestamp": health_ui.now_str(), "type": "test_type", "severity": "INFO", "symptom": "тест", "suggested_action": "нет", "status": "OPEN"})
health_ui.save_incidents(items)
items2 = health_ui.load_incidents()
assert len(items2) == 1 and items2[0]["status"] == "OPEN"
items2[0]["status"] = "HEALED"
health_ui.save_incidents(items2)
assert health_ui.load_incidents()[0]["status"] == "HEALED"
print("ТЕСТ OK: диагностика и инциденты работают")
shutil.rmtree(TMP, ignore_errors=True)