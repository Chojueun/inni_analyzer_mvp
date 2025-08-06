# user_state.py
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
        }
    if "step_results" not in st.session_state:
        st.session_state.step_results = {}
    if "cot_history" not in st.session_state:
        st.session_state.cot_history = []
    if "step_history" not in st.session_state:
        st.session_state.step_history = []
    if "current_step_index" not in st.session_state:
        st.session_state.current_step_index = 0

def get_user_inputs():
    """st.session_state에서 직접 프로젝트 정보를 가져옴"""
    return {
        "project_name": st.session_state.get("project_name", ""),
        "owner": st.session_state.get("owner", ""),
        "site_location": st.session_state.get("site_location", ""),
        "site_area": st.session_state.get("site_area", ""),
        "zoning": st.session_state.get("zoning", ""),
        "building_type": st.session_state.get("building_type", ""),
        "project_goal": st.session_state.get("project_goal", "")
    }

def set_pdf_summary(summary: str):
    st.session_state.pdf_summary = summary

def get_pdf_summary() -> str:
    return st.session_state.pdf_summary

def save_step_result(step_id: str, result: str):
    st.session_state.step_results[step_id] = result

def append_step_history(step_id: str, title: str, prompt: str, result: str):
    from utils import extract_summary, extract_insight

    st.session_state.step_history.append({
        "id": step_id,
        "title": title,
        "prompt": prompt,
        "result": result,
        "summary": extract_summary(result),
        "insight": extract_insight(result)
    })

def get_current_step_index() -> int:
    return st.session_state.current_step_index

# 쓰이지 않는 함수들 제거:
# - update_user_input()
# - get_step_result()
# - get_step_context()
# - next_step()
# - previous_step()
# - reset_steps()
# - is_started()
# - advance_step()