from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib import colors
import io
import re

# python-docx가 있으면 import, 없으면 None
try:
    from docx import Document
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    Document = None
    WD_ALIGN_PARAGRAPH = None

def register_korean_font():
    """한국어 폰트 등록"""
    try:
        # NOTOSANSKR-VF.TTF 폰트 등록
        pdfmetrics.registerFont(TTFont('NotoSansKR', 'NOTOSANSKR-VF.TTF'))
        return True
    except:
        # 폰트 파일이 없으면 기본 폰트 사용
        return False

def clean_text_for_pdf(text):
    """PDF용 텍스트 정리 - HTML 태그 제거 및 안전한 형식으로 변환"""
    if not text:
        return ""
    
    # HTML 태그 제거
    text = re.sub(r'<br\s*/?>', '\n', text)  # <br> 태그를 줄바꿈으로
    text = re.sub(r'<[^>]+>', '', text)  # 모든 HTML 태그 제거
    
    # 특수 문자 처리
    text = text.replace('•', '•')  # bullet point
    text = text.replace('–', '-')  # en dash
    text = text.replace('—', '-')  # em dash
    
    # 연속된 공백 정리
    text = re.sub(r'\s+', ' ', text)
    
    # 줄바꿈 정리
    text = re.sub(r'\n\s*\n', '\n\n', text)
    
    return text.strip()

def generate_pdf_report(content, user_inputs):
    """PDF 보고서 생성"""
    
    # 메모리 버퍼에 PDF 생성
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # 스타일 설정
    styles = getSampleStyleSheet()
    
    # 한국어 폰트 등록
    font_registered = register_korean_font()
    
    # 커스텀 스타일 생성
    if font_registered:
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontName='NotoSansKR',
            fontSize=16,
            spaceAfter=12,
            alignment=1  # 중앙 정렬
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName='NotoSansKR',
            fontSize=14,
            spaceAfter=8
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName='NotoSansKR',
            fontSize=10,
            spaceAfter=6
        )
    else:
        # 기본 폰트 사용
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
    
    # 내용을 문단으로 분할
    story = []
    
    # 제목 추가
    project_name = user_inputs.get('project_name', '프로젝트')
    title_text = f"📊 {project_name} 분석 보고서"
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 20))
    
    # 내용 파싱 및 추가
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 제목 처리
        if line.startswith('# '):
            text = clean_text_for_pdf(line[2:].strip())
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 12))
        elif line.startswith('## '):
            text = clean_text_for_pdf(line[3:].strip())
            story.append(Paragraph(text, heading_style))
            story.append(Spacer(1, 8))
        elif line.startswith('### '):
            text = clean_text_for_pdf(line[4:].strip())
            story.append(Paragraph(text, heading_style))
            story.append(Spacer(1, 6))
        elif line.startswith('---'):
            story.append(Spacer(1, 12))
        else:
            # 일반 텍스트 처리
            if line:
                # 표 형식 처리 (간단한 표)
                if '|' in line:
                    # 표를 텍스트로 변환
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if len(cells) >= 2:
                        # HTML 태그 없이 안전한 형식으로
                        key = clean_text_for_pdf(cells[0])
                        value = clean_text_for_pdf(cells[1])
                        formatted_line = f"<b>{key}</b>: {value}"
                        story.append(Paragraph(formatted_line, normal_style))
                else:
                    # 일반 텍스트 정리
                    clean_line = clean_text_for_pdf(line)
                    if clean_line:
                        story.append(Paragraph(clean_line, normal_style))
    
    # PDF 생성
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        # 오류 발생 시 간단한 텍스트로 재시도
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        simple_story = []
        
        # 간단한 텍스트로 변환
        simple_story.append(Paragraph(f"📊 {project_name} 분석 보고서", title_style))
        simple_story.append(Spacer(1, 20))
        
        # 원본 텍스트를 그대로 사용 (HTML 태그 제거)
        clean_content = clean_text_for_pdf(content)
        paragraphs = clean_content.split('\n\n')
        
        for para in paragraphs:
            if para.strip():
                simple_story.append(Paragraph(para.strip(), normal_style))
                simple_story.append(Spacer(1, 6))
        
        doc.build(simple_story)
        buffer.seek(0)
        return buffer.getvalue()

def generate_word_report(content, user_inputs):
    """Word 문서 보고서 생성"""
    
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx 모듈이 설치되지 않았습니다. 'pip install python-docx'로 설치해주세요.")
    
    # Word 문서 생성
    doc = Document()
    
    # 제목 설정
    project_name = user_inputs.get('project_name', '프로젝트')
    title = doc.add_heading(f"📊 {project_name} 분석 보고서", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 내용 파싱 및 추가
    lines = content.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 제목 처리
        if line.startswith('# '):
            text = clean_text_for_pdf(line[2:].strip())
            doc.add_heading(text, level=1)
        elif line.startswith('## '):
            text = clean_text_for_pdf(line[3:].strip())
            doc.add_heading(text, level=2)
        elif line.startswith('### '):
            text = clean_text_for_pdf(line[4:].strip())
            doc.add_heading(text, level=3)
        elif line.startswith('---'):
            doc.add_paragraph()  # 빈 줄 추가
        else:
            # 일반 텍스트 처리
            if line:
                # 표 형식 처리
                if '|' in line:
                    cells = [cell.strip() for cell in line.split('|') if cell.strip()]
                    if len(cells) >= 2:
                        p = doc.add_paragraph()
                        p.add_run(f"{clean_text_for_pdf(cells[0])}: ").bold = True
                        p.add_run(clean_text_for_pdf(cells[1]))
                else:
                    clean_line = clean_text_for_pdf(line)
                    if clean_line:
                        doc.add_paragraph(clean_line)
    
    # 메모리 버퍼에 저장
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue() 