# autotest.py v2 - автопроверка офиса (UI тестируется через файлы-обёртки)
import os
import sys
import tempfile
import shutil

BASE = os.path.dirname(os.path.abspath(__file__))
RESULTS = []

def check(name, fn):
    try:
        fn()
        RESULTS.append((name, True))
        print("  [OK] " + name)
    except Exception as e:
        RESULTS.append((name, False))
        print("  [FAIL] " + name + " -> " + str(e))

TMP = tempfile.mkdtemp(prefix="office_autotest_")
import office_db as db
db.DB_PATH = os.path.join(TMP, "test.db")

def _write_wrapper(name, module):
    path = os.path.join(TMP, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write("import sys\n")
        f.write("sys.path.insert(0, " + repr(BASE) + ")\n")
        f.write("import " + module + " as m\n")
        f.write("m.render()\n")
    return path

def t_db_core():
    db.init_db()
    pid = db.add_printer("T1", "Model", 0.4, "256", "PLA", 1000, 1000, "test")
    assert pid >= 1
    pl = db.add_plastic("PETG", "red", 1000, 200, "shelf", "Ozon", pid)
    ok, msg = db.use_plastic(pl, 75, "test", pid, "sample", "note")
    assert ok, msg
    rows = db.list_plastic()
    assert rows[0]["weight_grams"] == 925, rows[0]["weight_grams"]
    ok2, _ = db.use_plastic(pl, 99999, "test", pid, "test", "")
    assert not ok2

def t_db_products_tx():
    pr = db.add_product("Dragon", 3, "PETG", 75, 394.0, 550.0, "showcase", None)
    assert pr >= 1
    photo = os.path.join(TMP, "photo.png")
    with open(photo, "wb") as f:
        f.write(b"x")
    tx = db.add_transaction("expense", "materials", 100.0, "test", photo)
    assert tx >= 1
    db.delete_transaction(tx)
    assert not os.path.exists(photo)
    db.add_transaction("income", "other", 50.0, "t2", None)
    db.clear_transactions()
    assert db.list_transactions() == []

def t_inventory():
    rep = db.inventory_report()
    assert "plastic" in rep and "products" in rep

def t_ocr():
    import office_ocr
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (400, 80), "white")
    d = ImageDraw.Draw(img)
    d.text((20, 30), "PETG 1299 rub", fill="black")
    p = os.path.join(TMP, "ocr.png")
    img.save(p)
    txt = office_ocr.recognize_image(p)
    assert "1299" in txt.replace(" ", ""), txt
    am = office_ocr.find_amounts("total 16628.00 rub")
    assert am, am

def t_office_logic():
    import office
    assert office.detect_gibberish("cerebellum lesion parkinson")[0]
    assert not office.detect_gibberish("Dragon from PETG plastic, price 550 rubles")[0]
    office.BB_FILE = os.path.join(TMP, "bb.json")
    with open(office.BB_FILE, "w", encoding="utf-8") as f:
        f.write("{}")
    office.update_blackboard_from_text('```json {"update": {"fact": {"value": "price 100", "source": ""}}} ```', "logistic")
    assert office.load_blackboard() == {}
    office.update_blackboard_from_text('```json {"update": {"fact": {"value": "not found", "source": "base"}}} ```', "logistic")
    assert office.load_blackboard() == {}
    office.update_blackboard_from_text('```json {"update": {"fact": {"value": "seam 394", "source": "base"}}} ```', "marketer")
    assert office.load_blackboard() == {}
    office.update_blackboard_from_text('```json {"update": {"fact": {"value": "seam 394", "source": "base"}}} ```', "financier")
    assert office.load_blackboard() != {}

def t_ui_smoke():
    from streamlit.testing.v1 import AppTest
    import receipts_ui
    receipts_ui.ACC_DIR = os.path.join(TMP, "acc")
    os.makedirs(receipts_ui.ACC_DIR, exist_ok=True)
    at = AppTest.from_file(_write_wrapper("ui_receipts.py", "receipts_ui"), default_timeout=60)
    at.run()
    assert not at.exception, str(at.exception)
    at2 = AppTest.from_file(_write_wrapper("ui_warehouse.py", "warehouse_ui"), default_timeout=60)
    at2.run()
    assert not at2.exception, str(at2.exception)

def t_ui_orphans():
    from streamlit.testing.v1 import AppTest
    import receipts_ui
    acc = receipts_ui.ACC_DIR
    orphan = os.path.join(acc, "orphan.png")
    with open(orphan, "wb") as f:
        f.write(b"o")
    linked = os.path.join(acc, "linked.png")
    with open(linked, "wb") as f:
        f.write(b"l")
    db.add_transaction("expense", "materials", 1.0, "t", linked)
    at = AppTest.from_file(_write_wrapper("ui_receipts2.py", "receipts_ui"), default_timeout=60)
    at.run()
    btn = None
    for b in at.button:
        if "сирот" in b.label.lower():
            btn = b
    assert btn is not None, "orphan button not found"
    btn.click().run()
    assert not os.path.exists(orphan), "orphan not deleted"
    assert os.path.exists(linked), "linked photo was deleted"

def main():
    print("=== AUTOTEST OFFICE ===")
    check("DB: sklad and spisanie", t_db_core)
    check("DB: tovary, operacii, udalenie s foto", t_db_products_tx)
    check("DB: inventarizaciya", t_inventory)
    check("OCR: raspoznavanie i summy", t_ocr)
    check("Logika: detector i zamki Doski", t_office_logic)
    check("UI: rendery bez oshibok", t_ui_smoke)
    check("UI: uborka sirotskih foto", t_ui_orphans)
    bad = [r for r in RESULTS if not r[1]]
    print("=== ITOG: %d/%d OK ===" % (len(RESULTS) - len(bad), len(RESULTS)))
    shutil.rmtree(TMP, ignore_errors=True)
    if bad:
        sys.exit(1)

if __name__ == "__main__":
    main()