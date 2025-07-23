# user_state.py
import streamlit as st

def init_user_state():
    """
    초기 상태 변수 설정
    """
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
    if "current_step_index" not in st.session_state:
        st.session_state.current_step_index = 0  # 현재 선택된 단계


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
    """
    사용자 입력 값 갱신
    """
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

def next_step():
    st.session_state.current_step_index += 1

def previous_step():
    st.session_state.current_step_index = max(0, st.session_state.current_step_index - 1)

def get_current_step_index() -> int:
    return st.session_state.current_step_index
