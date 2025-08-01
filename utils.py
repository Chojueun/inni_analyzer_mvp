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


def clean_text(text: str) -> str:
    """
    텍스트 정제: 불필요한 개행, 공백 제거
    """
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def summarize_cot_history(cot_history: List[Dict]) -> str:
    """
    CoT 히스토리를 간결하게 요약 (Step N + 결과 요약 형태)
    """
    return "\n".join([
        f"[{item['step']}] {item['result'].strip()}"
        for item in cot_history
    ])


def merge_prompt_content(
    block_prompt: str,
    user_info: Dict[str, str],
    pdf_summary: str,
    step_context: Optional[str] = ""
) -> str:
    """
    전체 분석 프롬프트를 구성 (사용자 입력 + PDF 요약 + 이전 단계 결과 + 분석 지시어 순으로 정렬)
    """
    sections = []

    # ① 사용자 입력
    if user_info:
        lines = "\n".join([f"- {k}: {v}" for k, v in user_info.items() if v])
        sections.append("📌 사용자 입력 정보\n" + lines)

    # ② PDF 요약
    if isinstance(pdf_summary, dict):
        lines = []
        if pdf_summary.get("project_name"):
            lines.append(f"- 사업명: {pdf_summary['project_name']}")
        if pdf_summary.get("site_location"):
            lines.append(f"- 위치: {pdf_summary['site_location']}")
        if pdf_summary.get("budget"):
            lines.append(f"- 예산: {pdf_summary['budget']}")
        if pdf_summary.get("timeline"):
            lines.append(f"- 일정: {pdf_summary['timeline']}")
        if pdf_summary.get("explicit_requirements"):
            lines.append(f"- 명시적 요구사항: {pdf_summary['explicit_requirements'][:150]}...")
        if pdf_summary.get("implicit_needs"):
            lines.append(f"- 암묵적 니즈: {pdf_summary['implicit_needs'][:150]}...")
        if pdf_summary.get("risks"):
            lines.append(f"- 주요 리스크: {pdf_summary['risks'][:150]}...")
        
        sections.append("📄 PDF 요약 정보\n" + "\n".join(lines))

    elif isinstance(pdf_summary, str):
        sections.append("📄 PDF 요약 (텍스트)\n" + pdf_summary[:300] + "...")

    # ③ 이전 단계 누적 요약 (0~N-1단계)
    if step_context:
        sections.append("🔗 이전 단계 누적 분석 요약\n" + step_context)

    # ④ 현재 단계 분석 지시어
    sections.append("🧠 현재 단계 분석 지시어\n" + block_prompt.strip())

    # 전체 구성
    return "\n\n".join(sections).strip()

