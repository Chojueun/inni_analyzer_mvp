import fitz  # PyMuPDF
import re
from typing import Dict, Optional, List


def extract_text_from_pdf(pdf_file) -> str:
    """
    PDF 파일에서 전체 텍스트를 추출한다.
    Streamlit UploadedFile 객체를 인자로 받는다.
    """
    pdf_bytes = pdf_file.read()
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

    # 사용자 정보
    user_info_lines = "\n".join([
        f"- {key}: {value}" for key, value in user_info.items() if value
    ])
    if user_info_lines:
        sections.append("📌 사용자 입력 정보\n" + user_info_lines)

    # PDF 요약
    if pdf_summary:
        sections.append("📄 대상 문서 요약\n" + pdf_summary.strip())

    # 이전 단계 결과 (Chain-of-Thought)
    if step_context:
        sections.append("🔗 이전 단계 분석 결과 (누적)\n" + step_context.strip())

    # 현재 단계 분석 지시어
    sections.append("🧠 현재 단계 분석 지시어\n" + block_prompt.strip())

    return "\n\n".join(sections).strip()
