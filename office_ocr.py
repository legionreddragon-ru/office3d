# office_ocr.py - распознавание текста с картинок
import os
import re
import pytesseract

TESS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(TESS_PATH):
    pytesseract.pytesseract.tesseract_cmd = TESS_PATH

def recognize_image(path):
    from PIL import Image
    try:
        img = Image.open(path)
        return pytesseract.image_to_string(img, lang="rus+eng")
    except Exception as e:
        return "ОШИБКА РАСПОЗНАВАНИЯ: " + str(e)

def find_amounts(text):
    return re.findall(r"(\d[\d\s.,]{0,10})\s*(?:₽|руб|rub)", text, re.IGNORECASE)