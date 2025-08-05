
#utils.py

import fitz  # PyMuPDF
import re
from typing import Dict, Optional, List


def extract_summary(result: str) -> str:
    """
    전체 Claude 출력 텍스트에서 300자 내외 요약을 자동 추출
    """
    # 1. ‘요구사항 분석’ 또는 ‘핵심 요약표’ 섹션이 있으면 우선 추출
    if "요구사항 분석" in result:
        m = re.search(r"(요구사항 분석.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()[:300]
    elif "요약" in result:
        m = re.search(r"(요약.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()[:300]

    # 2. 앞부분 300자 기본 제공
    return result.strip()[:300] + "..."

def extract_insight(result: str) -> str:
    """
    GPT 출력 텍스트에서 전략 제언 또는 시사점 섹션을 추출
    """
    if "전략적 제언" in result:
        m = re.search(r"(전략적 제언.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()
    elif "시사점" in result:
        m = re.search(r"(시사점.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()
    elif "Insight" in result:
        m = re.search(r"(Insight.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()

    # fallback
    return "※ 전략적 제언 항목이 명확히 감지되지 않았습니다."


def extract_text_from_pdf(pdf_bytes) -> str:
    """
    PDF 바이트에서 전체 텍스트를 추출한다.
    """
    import fitz
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join([page.get_text() for page in doc])
