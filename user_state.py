#user_state.py

import streamlit as st

def init_user_state():
    if "pdf_summary" not in st.session_state:
        st.session_state.pdf_summary = ""
    if "user_inputs" not in st.session_state:
        st.session_state.user_inputs = {
            "project_name": "",
            "owner": "",
            "site_location": "",
            "site_area": "",
            "zoning": "",
            "building_type": "",
            "project_goal": "",
            # 필요시 추가
        }
    if "step_results" not in st.session_state:
        st.session_state.step_results = {}  # 각 단계별 분석 결과 저장
    if "cot_history" not in st.session_state:
        st.session_state.cot_history = []
    if "step_history" not in st.session_state:
        st.session_state.step_history = []  # 각 단계의 (id, title, prompt, result)
    if "current_step_index" not in st.session_state:
        st.session_state.current_step_index = 0

def get_user_inputs():
    if "user_inputs" not in st.session_state:
        st.session_state.user_inputs = {}

    st.session_state.user_inputs["project_name"] = st.sidebar.text_input(
        "Project Name (예: Woori Bank Dasan Campus)", value=st.session_state.user_inputs.get("project_name", "")
    )
    st.session_state.user_inputs["owner"] = st.sidebar.text_input(
        "Owner (예: Woori Bank)", value=st.session_state.user_inputs.get("owner", "")
    )
    st.session_state.user_inputs["site_location"] = st.sidebar.text_input(
        "Site Location (예: Namyangju-si, Gyeonggi-do)", value=st.session_state.user_inputs.get("site_location", "")
    )
    st.session_state.user_inputs["site_area"] = st.sidebar.text_input(
        "Site Area (예: 7,500㎡)", value=st.session_state.user_inputs.get("site_area", "")
    )
    st.session_state.user_inputs["zoning"] = st.sidebar.text_input(
        "Zoning (예: General Residential Zone)", value=st.session_state.user_inputs.get("zoning", "")
    )
    st.session_state.user_inputs["building_type"] = st.sidebar.text_input(
        "Building Type (예: Training Center)", value=st.session_state.user_inputs.get("building_type", "")
    )
    st.session_state.user_inputs["project_goal"] = st.sidebar.text_area(
        "Project Goal (예: Develop an innovative training campus...)", value=st.session_state.user_inputs.get("project_goal", "")
    )

    return st.session_state.user_inputs

def update_user_input(key: str, value: str):
    if "user_inputs" not in st.session_state:
        st.session_state.user_inputs = {}
    st.session_state.user_inputs[key] = value

def set_pdf_summary(summary: str):
    st.session_state.pdf_summary = summary

def get_pdf_summary() -> str:
    return st.session_state.pdf_summary

def save_step_result(step_id: str, result: str):
    st.session_state.step_results[step_id] = result

def get_step_result(step_id: str) -> str:
    return st.session_state.step_results.get(step_id, "")

def append_step_history(step_id: str, title: str, prompt: str, result: str):
    from utils import extract_summary, extract_insight  # utils.py에 만들어둘 함수

    st.session_state.step_history.append({
        "id": step_id,
        "title": title,
        "prompt": prompt,
        "result": result,
        "summary": extract_summary(result),
        "insight": extract_insight(result)
    })

def get_step_context() -> str:
    """
    지금까지의 단계 결과를 섹션별로 정리하여 다음 프롬프트에 누적 전달.
    """
    lines = []
    for step in st.session_state.get("step_history", []):
        lines.append(f"🔹 단계: {step['title']}")
        lines.append("📄 요구사항 요약표 / 분석 결과:")
        lines.append(step['result'])  # 이미 구조화된 출력이므로 그대로 사용
        lines.append("-" * 40)
    return "\n".join(lines)

def next_step():
    st.session_state.current_step_index += 1

def previous_step():
    st.session_state.current_step_index = max(0, st.session_state.current_step_index - 1)

def get_current_step_index() -> int:
    return st.session_state.current_step_index

def reset_steps():
    st.session_state.current_step_index = 0

def is_started() -> bool:
    return st.session_state.current_step_index >= 0

def advance_step():
    st.session_state.current_step_index += 1