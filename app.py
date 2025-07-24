import streamlit as st
from agent_executor import InniAgent
from prompt_loader import load_prompt_blocks
from user_state import (
    get_user_inputs, set_pdf_summary,
    get_pdf_summary, save_step_result
)
from utils import extract_text_from_pdf, merge_prompt_content
from dsl_to_prompt import convert_dsl_to_prompt
from user_state import init_user_state

init_user_state()

st.set_page_config(page_title="Inni Analyzer MVP", layout="wide")

st.title("📊 Inni Analyzer: GPT-4o 기반 건축 프로젝트 분석")

# 📥 1. 사용자 입력 수집
st.sidebar.header("📥 프로젝트 기본 정보 입력")
user_inputs = get_user_inputs()

uploaded_pdf = st.sidebar.file_uploader("📎 과업지시서 또는 제안요청서 (PDF)", type=["pdf"])

if uploaded_pdf:
    pdf_text = extract_text_from_pdf(uploaded_pdf)
    set_pdf_summary(pdf_text)
    st.sidebar.success("✅ PDF 업로드 및 텍스트 추출 완료!")

# 📦 2. 프롬프트 블록 로드
blocks = load_prompt_blocks()
block_list = list(blocks.values())

# ✅ 3. 분석 블록 선택
selected_blocks = st.sidebar.multiselect(
    "🔍 분석할 블럭들을 선택하고 순서를 조정하세요:",
    block_list,
    format_func=lambda b: f"{b['title']}"
)
# 🚀 4. 분석 실행
if selected_blocks and st.button("🚀 선택한 블럭들 분석 실행"):
    st.session_state.cot_history = []  # 누적 결과 초기화

    for idx, block in enumerate(selected_blocks):
        step_id = block["id"]
        title = block["title"]

        # 🔗 누적된 이전 분석 내용 정리 (먼저)
        step_context = "\n".join([
            f"[{prev['step']}] {prev['result']}" for prev in st.session_state.cot_history
        ])

        # DSL 기반 프롬프트 구성
        if "content_dsl" in block:
            prompt_template = convert_dsl_to_prompt(
                dsl_block=block["content_dsl"],
                user_inputs=user_inputs,
                previous_summary=step_context,
                pdf_summary=get_pdf_summary()
            )
        else:
            prompt_template = block["content"]

        st.markdown(f"### 📘 Step {idx+1}: {title}")
        st.code(prompt_template, language="markdown")

        # 🧠 전체 프롬프트 구성
        full_prompt = merge_prompt_content(
            block_prompt=prompt_template,
            user_info=user_inputs,
            pdf_summary=get_pdf_summary(),
            step_context=step_context
        )

        # 🤖 분석 실행
        with st.spinner("🔎 GPT 분석 중입니다..."):
            agent = InniAgent()
            result = agent.run_analysis(full_prompt)

        # ✅ 결과 출력 및 저장
        st.success("✅ 분석 완료!")
        st.markdown("### 🔍 결과")
        st.markdown(result)

        st.session_state.cot_history.append({
            "step": f"Step {idx+1}",
            "title": title,
            "prompt": full_prompt,
            "result": result
        })
        save_step_result(step_id, result)

    # 🧠 전체 분석 흐름 요약 (Chain-of-Thought)
    if len(st.session_state.cot_history) > 1:
        st.markdown("---")
        st.markdown("### 🧠 전체 분석 흐름 요약 (Chain-of-Thought)")
        for i, h in enumerate(st.session_state.cot_history):
            st.markdown(f"**{i+1}. {h['title']}**")
            st.markdown(f"- 결과 요약: {h['result'][:200]}...")
