#report_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import io
import re
import os

# python-docx가 있으면 import, 없으면 None
try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    Document = None
    WD_ALIGN_PARAGRAPH = None

def register_korean_font():
    """한국어 폰트 등록 - 여러 옵션 시도"""
    font_options = [
        'NOTOSANSKR-VF.TTF',
        'NanumGothicCoding.ttf',
        'NanumGothicCoding-Bold.ttf',
        'malgun.ttf',  # Windows 기본 폰트
        'gulim.ttc',   # Windows 기본 폰트
    ]
    
    for font_file in font_options:
        try:
            if os.path.exists(font_file):
                pdfmetrics.registerFont(TTFont('KoreanFont', font_file))
                print(f"한국어 폰트 등록 성공: {font_file}")
                return True
        except Exception as e:
            print(f"폰트 등록 실패 ({font_file}): {e}")
            continue
    
    # 폰트 파일이 없으면 기본 폰트 사용
    print("한국어 폰트를 찾을 수 없어 기본 폰트를 사용합니다.")
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

def parse_table_from_text(text):
    """텍스트에서 표 형식을 파싱하여 2D 배열로 변환"""
    lines = text.strip().split('\n')
    table_data = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 구분선 제거
        if re.match(r'^[\s\-=_]+\s*$', line):
            continue
            
        # | 구분자로 분할
        if '|' in line:
            cells = [cell.strip() for cell in line.split('|')]
            # 첫 번째와 마지막 빈 셀 제거 (마크다운 표 형식)
            if cells and not cells[0].strip():
                cells = cells[1:]
            if cells and not cells[-1].strip():
                cells = cells[:-1]
            table_data.append(cells)
        else:
            # 탭이나 공백으로 구분된 경우
            cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
            if not cells:
                cells = [cell.strip() for cell in re.split(r'\s{2,}', line) if cell.strip()]
            if cells:
                table_data.append(cells)
    
    return table_data

def is_table_format(text):
    """텍스트가 표 형식인지 확인"""
    lines = text.strip().split('\n')
    if len(lines) < 2:
        return False
    
    # 표 구분자 확인
    table_indicators = ['|', '\t']
    for line in lines[:3]:
        if any(indicator in line for indicator in table_indicators):
            return True
    
    # 구분선 확인
    for line in lines:
        if re.match(r'^[\s\-=_]+\s*$', line.strip()):
            return True
    
    # 정렬된 텍스트 확인
    if len(lines) >= 2:
        first_line = lines[0]
        second_line = lines[1]
        first_words = re.split(r'\s{2,}', first_line.strip())
        second_words = re.split(r'\s{2,}', second_line.strip())
        
        if len(first_words) >= 2 and len(second_words) >= 2:
            if abs(len(first_words) - len(second_words)) <= 1:
                return True
    
    return False

def generate_pdf_report(content, user_inputs):
    """PDF 보고서 생성 - 표 처리 개선 및 폰트 문제 해결"""
    
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
            fontName='KoreanFont',
            fontSize=16,
            spaceAfter=12,
            alignment=1  # 중앙 정렬
        )
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontName='KoreanFont',
            fontSize=14,
            spaceAfter=8
        )
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontName='KoreanFont',
            fontSize=10,
            spaceAfter=6
        )
    else:
        # 기본 폰트 사용 (한국어 지원 안됨)
        title_style = styles['Heading1']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']
    
    # 내용을 문단으로 분할
    story = []
    
    # 제목 추가
    project_name = user_inputs.get('project_name', '프로젝트')
    title_text = f"{project_name} 분석 보고서"
    story.append(Paragraph(title_text, title_style))
    story.append(Spacer(1, 20))
    
    # 내용 파싱 및 추가
    paragraphs = content.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # 표 형식 처리
        if is_table_format(para):
            table_data = parse_table_from_text(para)
            if table_data and len(table_data) > 0:
                # 표 생성
                table = Table(table_data)
                
                # 표 스타일 설정 - 폰트 문제 해결
                if font_registered:
                    table_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, -1), 'KoreanFont'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige]),
                    ])
                else:
                    # 기본 폰트 사용 (한국어가 깨질 수 있음)
                    table_style = TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 0), (-1, 0), 12),
                        ('FONTSIZE', (0, 1), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.beige]),
                    ])
                
                table.setStyle(table_style)
                story.append(table)
                story.append(Spacer(1, 12))
                continue
        
        # 일반 텍스트 처리
        lines = para.split('\n')
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
                    clean_line = clean_text_for_pdf(line)
                    if clean_line:
                        story.append(Paragraph(clean_line, normal_style))
    
    # PDF 생성
    try:
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        print(f"PDF 생성 오류: {e}")
        # 오류 발생 시 간단한 텍스트로 재시도
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        simple_story = []
        
        # 간단한 텍스트로 변환
        simple_story.append(Paragraph(f"{project_name} 분석 보고서", title_style))
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
    """Word 문서 보고서 생성 - 표 처리 개선"""
    
    if not DOCX_AVAILABLE:
        raise ImportError("python-docx 모듈이 설치되지 않았습니다. 'pip install python-docx'로 설치해주세요.")
    
    # Word 문서 생성
    doc = Document()
    
    # 제목 설정
    project_name = user_inputs.get('project_name', '프로젝트')
    title = doc.add_heading(f"{project_name} 분석 보고서", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 내용 파싱 및 추가
    paragraphs = content.split('\n\n')
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        # 표 형식 처리
        if is_table_format(para):
            table_data = parse_table_from_text(para)
            if table_data and len(table_data) > 0:
                # Word 표 생성
                table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                table.style = 'Table Grid'
                
                # 데이터 채우기
                for i, row in enumerate(table_data):
                    for j, cell in enumerate(row):
                        if i < len(table.rows) and j < len(table.rows[i].cells):
                            table.rows[i].cells[j].text = clean_text_for_pdf(cell)
                
                doc.add_paragraph()  # 표 후 빈 줄
                continue
        
        # 일반 텍스트 처리
        lines = para.split('\n')
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
                    clean_line = clean_text_for_pdf(line)
                    if clean_line:
                        doc.add_paragraph(clean_line)
    
    # 메모리 버퍼에 저장
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def generate_report_content(report_type, include_charts, include_recommendations, include_appendix):
    """보고서 내용 생성 - 보고서 유형별 차이점 적용"""
    from user_state import get_user_inputs
    user_inputs = get_user_inputs()
    
    # 기본 정보
    report_content = f"""
# {user_inputs.get('project_name', '프로젝트')} 분석 보고서
**보고서 유형**: {report_type}

## 📋 프로젝트 기본 정보
- **프로젝트명**: {user_inputs.get('project_name', 'N/A')}
- **건축주**: {user_inputs.get('owner', 'N/A')}
- **대지위치**: {user_inputs.get('site_location', 'N/A')}
- **대지면적**: {user_inputs.get('site_area', 'N/A')}
- **건물용도**: {user_inputs.get('building_type', 'N/A')}
- **프로젝트 목표**: {user_inputs.get('project_goal', 'N/A')}

"""
    
    # 분석 결과 추가
    import streamlit as st
    if st.session_state.get('cot_history'):
        if report_type == "전체 분석 보고서":
            # 전체 분석 보고서: 모든 상세 내용 포함
            report_content += "## 전체 분석 결과\n"
            for i, history in enumerate(st.session_state.cot_history, 1):
                report_content += f"""
### {i}. {history['step']}

**요약**: {history.get('summary', '')}

**인사이트**: {history.get('insight', '')}

**상세 분석**:
{history.get('result', '')}

---
"""
        
        elif report_type == "요약 보고서":
            # 요약 보고서: 핵심 요약과 인사이트만
            for i, history in enumerate(st.session_state.cot_history, 1):
                report_content += f"""
### {i}. {history['step']}

**핵심 요약**: {history.get('summary', '')}

**주요 인사이트**: {history.get('insight', '')}

---
"""
        
        elif report_type == "전문가 보고서":
            # 전문가 보고서: 기술적 분석과 전문적 권장사항
            report_content += "## 전문가 분석 결과\n"
            for i, history in enumerate(st.session_state.cot_history, 1):
                report_content += f"""
### {i}. {history['step']}

**분석 요약**: {history.get('summary', '')}

**전문가 인사이트**: {history.get('insight', '')}

**기술적 분석**:
{history.get('result', '')[:500]}...

---
"""
        
        elif report_type == "클라이언트 보고서":
            # 클라이언트 보고서: 비즈니스 관점의 핵심 내용
            report_content += "## 💼 비즈니스 분석 결과\n"
            for i, history in enumerate(st.session_state.cot_history, 1):
                report_content += f"""
### {i}. {history['step']}

**비즈니스 요약**: {history.get('summary', '')}

**핵심 가치**: {history.get('insight', '')}

**실행 가능한 제안**:
{history.get('result', '')[:300]}...

---
"""
    
    # 추가 섹션들 (보고서 유형별로 다르게 적용)
    if include_charts:
        if report_type == "전체 분석 보고서":
            report_content += """
## 상세 차트 및 다이어그램
(모든 차트 및 다이어그램이 포함됩니다)
"""
        elif report_type == "요약 보고서":
            report_content += """
## 핵심 차트
(주요 차트만 포함됩니다)
"""
        elif report_type == "전문가 보고서":
            report_content += """
## 전문가 차트 및 분석 다이어그램
(기술적 분석을 위한 상세 차트가 포함됩니다)
"""
        elif report_type == "클라이언트 보고서":
            report_content += """
## 💼 비즈니스 차트
(비즈니스 의사결정을 위한 핵심 차트가 포함됩니다)
"""
    
    if include_recommendations:
        if report_type == "전체 분석 보고서":
            report_content += """
## 💡 종합 권장사항
분석 결과를 바탕으로 한 상세한 권장사항이 포함됩니다.
"""
        elif report_type == "요약 보고서":
            report_content += """
## 💡 핵심 권장사항
가장 중요한 권장사항만 포함됩니다.
"""
        elif report_type == "전문가 보고서":
            report_content += """
## 💡 전문가 권장사항
기술적 관점에서의 전문적 권장사항이 포함됩니다.
"""
        elif report_type == "클라이언트 보고서":
            report_content += """
## 💡 비즈니스 권장사항
비즈니스 관점에서의 실행 가능한 권장사항이 포함됩니다.
"""
    
    if include_appendix:
        if report_type == "전체 분석 보고서":
            report_content += """
## 📋 상세 부록
모든 추가 자료 및 참고문헌이 포함됩니다.
"""
        elif report_type == "요약 보고서":
            report_content += """
## 📋 핵심 부록
주요 참고자료만 포함됩니다.
"""
        elif report_type == "전문가 보고서":
            report_content += """
## 📋 전문가 부록
기술적 참고자료 및 전문 문헌이 포함됩니다.
"""
        elif report_type == "클라이언트 보고서":
            report_content += """
## 📋 비즈니스 부록
비즈니스 관련 참고자료가 포함됩니다.
"""
    
    return report_content