# test_ocr.py - проверка распознавания текста
import pytesseract
from PIL import Image, ImageDraw

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

img = Image.new("RGB", (500, 120), "white")
d = ImageDraw.Draw(img)
d.text((20, 30), "Ozon PETG 1 kg 1299 rub", fill="black")
d.text((20, 70), "Mir hobbii PLA 1150", fill="black")
img.save("test_ocr.png")

try:
    text = pytesseract.image_to_string(img, lang="eng+rus")
except Exception as e:
    print("Русский язык не подхватился, пробую только английский:", e)
    text = pytesseract.image_to_string(img, lang="eng")

print("=== РАСПОЗНАНО ===")
print(text)
print("=== КОНЕЦ ===")