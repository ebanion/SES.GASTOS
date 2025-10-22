# utils/ocr.py
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import os


def extract_text_from_image(image_path: str) -> str:
    """Extract text from image using OCR"""
    try:
        # Configurar Tesseract para diferentes sistemas
        import platform
        if platform.system() == "Windows":
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        from PIL import Image
        image = Image.open(image_path)
        text = pytesseract.image_to_string(image, lang="spa+eng")
        return text.strip()
    except Exception as e:
        print(f"[OCR] Error extracting text from image: {e}")
        return ""

def extract_text_from_pdf(pdf_path: str) -> str:
    text = ""

    # Configurar ruta de Tesseract (importante para Windows)
    import platform
    if platform.system() == "Windows":
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # 1. Intentar extracción directa con pdfplumber (si hay texto digital)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"[OCR] Error en pdfplumber: {e}")

    # 2. Si no se extrajo nada, usar OCR con Tesseract
    if not text.strip():
        try:
            images = convert_from_path(pdf_path)
            for img in images:
                ocr_text = pytesseract.image_to_string(img, lang="spa")
                text += ocr_text + "\n"
        except Exception as e:
            print(f"[OCR] Error en OCR con Tesseract: {e}")

    return text.strip()
