#pdf_loader.py

from PyPDF2 import PdfReader

def extract_text_from_pdf_pyPDF2(uploaded_file):
    """PyPDF2를 사용한 PDF 텍스트 추출"""
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text.strip()