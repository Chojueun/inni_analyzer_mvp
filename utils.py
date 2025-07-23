# utils.py
import fitz  # PyMuPDF
import re
import streamlit as st

def extract_text_from_pdf(pdf_file) -> str:
    pdf_bytes = pdf_file.read()  # Streamlit의 UploadedFile은 BytesIO
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join([page.get_text() for page in doc])

def clean_text(text: str) -> str:
    """
    불필요한 공백/개행 정리 등 텍스트 정제
    """
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()

def merge_prompt_content(block_prompt: str, user_info: dict, pdf_summary: str, previous_results: str = "") -> str:
    """
    프롬프트 실행 시 필요한 정보들을 하나로 합침
    """
    combined = "■ 사용자 정보\n"
    for key, value in user_info.items():
        combined += f"- {key}: {value}\n"

    combined += "\n■ PDF 요약\n"
    combined += pdf_summary + "\n"

    if previous_results:
        combined += "\n■ 이전 단계 결과 요약\n"
        combined += previous_results + "\n"

    combined += "\n■ 분석 프롬프트\n"
    combined += block_prompt.strip()

    return combined.strip()

def format_prompt_with_inputs(prompt_template: str, user_inputs: dict) -> str:
    """
    사용자 입력, PDF 요약, 이전 단계 결과를 포함해 최종 프롬프트를 생성
    """
    # 1. 이전 단계 요약 생성 (CoT)
    previous_summary = ""
    if "cot_history" in st.session_state and st.session_state.cot_history:
        previous_summary = "\n".join([
            f"[{item['step']}] {item['result']}" for item in st.session_state.cot_history
        ])

    # 2. 사용자 입력 포맷
    try:
        filled_prompt = prompt_template.format(**user_inputs)
    except KeyError as e:
        missing_key = str(e)
        return f"[오류] 프롬프트에 필요한 키 '{missing_key}'가 없습니다."

    # 3. 최종 프롬프트 조합
    final_prompt = ""
    if previous_summary:
        final_prompt += "■ 이전 단계 결과 요약\n" + previous_summary + "\n\n"

    final_prompt += "■ 분석 프롬프트\n" + filled_prompt

    return final_prompt.strip()
