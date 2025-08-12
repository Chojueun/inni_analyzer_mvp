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
    
    # 워크플로우 관련 상태 초기화
    if "workflow_steps" not in st.session_state:
        st.session_state.workflow_steps = []
    if "removed_steps" not in st.session_state:
        st.session_state.removed_steps = set()
    if "added_steps" not in st.session_state:
        st.session_state.added_steps = set()
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False
    if "analysis_completed" not in st.session_state:
        st.session_state.analysis_completed = False
    if "show_next_step_button" not in st.session_state:
        st.session_state.show_next_step_button = False
    if "current_step_display_data" not in st.session_state:
        st.session_state.current_step_display_data = None
    if "current_step_outputs" not in st.session_state:
        st.session_state.current_step_outputs = {}
    if "web_search_settings" not in st.session_state:
        st.session_state.web_search_settings = {}
    if "uploaded_pdf" not in st.session_state:
        st.session_state.uploaded_pdf = None
    if "site_fields" not in st.session_state:
        st.session_state.site_fields = {}
    if "pdf_analysis_result" not in st.session_state:
        st.session_state.pdf_analysis_result = {}
    if "pdf_quality_report" not in st.session_state:
        st.session_state.pdf_quality_report = {}
    if "selected_purpose" not in st.session_state:
        st.session_state.selected_purpose = None
    if "selected_objectives" not in st.session_state:
        st.session_state.selected_objectives = []
    if "analysis_system" not in st.session_state:
        from analysis_system import AnalysisSystem
        st.session_state.analysis_system = AnalysisSystem()

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

def reset_workflow_state():
    """워크플로우 상태 초기화"""
    st.session_state.workflow_steps = []
    st.session_state.removed_steps = set()
    st.session_state.added_steps = set()
    st.session_state.analysis_started = False
    st.session_state.analysis_completed = False
    st.session_state.current_step_index = 0
    st.session_state.cot_history = []
    st.session_state.show_next_step_button = False
    st.session_state.current_step_display_data = None
    st.session_state.current_step_outputs = {}

