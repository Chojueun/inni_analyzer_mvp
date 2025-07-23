# app.py
import streamlit as st
from agent_executor import InniAgent
from prompt_loader import load_prompt_blocks
from user_state import get_user_inputs
from utils import extract_text_from_pdf, format_prompt_with_inputs

st.set_page_config(page_title="Inni Analyzer MVP", layout="wide")

st.title("📊 Inni Analyzer: GPT-4o 기반 건축 프로젝트 분석")

# 1. 사용자 입력 수집
st.sidebar.header("📥 프로젝트 기본 정보 입력")

user_inputs = get_user_inputs()

uploaded_pdf = st.sidebar.file_uploader("📎 과업지시서 또는 제안요청서 (PDF)", type=["pdf"])
pdf_text = ""

if uploaded_pdf:
    pdf_text = extract_text_from_pdf(uploaded_pdf)
    st.sidebar.success("✅ PDF 업로드 및 텍스트 추출 완료!")
    user_inputs["pdf_summary"] = pdf_text  # ✅ pdf 요약을 user_inputs에 추가

# 2. 프롬프트 블록 선택
blocks = load_prompt_blocks()

selected_block = st.sidebar.selectbox(
    "🔍 분석할 단계를 선택하세요:",
    blocks,
    format_func=lambda b: f"{b['step']} - {b['title']}"
)

if selected_block:
    st.subheader(f"📘 {selected_block['step']}: {selected_block['title']}")
    st.markdown(f"```\n{selected_block['content']}\n```")

    if st.button("🚀 이 단계 분석 실행"):
        with st.spinner("🔎 분석 중입니다..."):
            # 프롬프트 조합
            full_prompt = format_prompt_with_inputs(
                selected_block["content"],
                user_inputs
            )
            agent = InniAgent()
            result = agent.run_analysis(full_prompt)

        st.success("✅ 분석 완료!")
        st.markdown("### 🔍 결과")
        st.markdown(result)

        # Chain-of-Thought 형태 연결을 위한 상태 저장
        if "cot_history" not in st.session_state:
            st.session_state.cot_history = []
        st.session_state.cot_history.append({
            "step": selected_block["step"],
            "title": selected_block["title"],
            "prompt": full_prompt,
            "result": result
        })

        if len(st.session_state.cot_history) > 1:
            st.markdown("---")
            st.markdown("### 🧠 이전 단계와의 연결 (CoT)")
            for i, h in enumerate(st.session_state.cot_history[:-1]):
                st.markdown(f"**{i+1}. {h['step']} - {h['title']}**")
                st.markdown(f"- 결과 요약: {h['result'][:200]}...")