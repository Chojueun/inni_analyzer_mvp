import streamlit as st

def init_user_state():
    if "pdf_summary" not in st.session_state:
        st.session_state.pdf_summary = ""
    if "user_inputs" not in st.session_state:
        st.session_state.user_inputs = {
            "건축주": "",
            "주소": "",
            "대지면적": "",
            "용도지역": "",
            "건폐율": "",
            "용적률": "",
            # 필요시 더 추가 가능
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

    st.session_state.user_inputs["owner"] = st.sidebar.text_input(
        "건축주 이름 (예: 현대건설)", value=st.session_state.user_inputs.get("owner", "")
    )
    st.session_state.user_inputs["site_location"] = st.sidebar.text_input(
        "대상지 위치 (예: 서울 강남구)", value=st.session_state.user_inputs.get("site_location", "")
    )
    st.session_state.user_inputs["project_goal"] = st.sidebar.text_area(
        "프로젝트 목표 (예: 복합문화시설 개발, ESG 친화적 리모델링 등)", value=st.session_state.user_inputs.get("project_goal", "")
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
    """
    단계 결과를 CoT 방식으로 누적 저장
    """
    st.session_state.step_history.append({
        "id": step_id,
        "title": title,
        "prompt": prompt,
        "result": result
    })

def get_step_context() -> str:
    """
    지금까지의 단계 결과를 순서대로 정리해서 CoT 프롬프트에 넣을 수 있도록 반환
    """
    lines = []
    for step in st.session_state.get("step_history", []):
        lines.append(f"🔹 단계: {step['title']}")
        lines.append(f"📝 입력 프롬프트:\n{step['prompt']}")
        lines.append(f"📌 분석 결과:\n{step['result']}")
        lines.append("-" * 40)
    return "\n".join(lines)

def next_step():
    st.session_state.current_step_index += 1

def previous_step():
    st.session_state.current_step_index = max(0, st.session_state.current_step_index - 1)

def get_current_step_index() -> int:
    return st.session_state.current_step_index
