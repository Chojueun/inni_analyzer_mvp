import streamlit as st

def get_user_inputs():
    if "user_inputs" not in st.session_state:
        st.session_state.user_inputs = {
            "건축주": "",
            "주소": "",
            "참고사항": "",
            "PDF내용": ""
        }
    return st.session_state.user_inputs


def update_user_inputs(key, value):
    st.session_state["user_inputs"][key] = value
