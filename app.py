import streamlit as st
from prompt_loader import load_prompt_blocks
from agent_executor import InniAgent

st.set_page_config(page_title="Inni Analyzer MVP", layout="centered")

# 상태 불러오기
user_inputs = get_user_inputs()

# 현재 단계를 선택 (0단계부터 시작)
if "step_index" not in st.session_state:
    st.session_state.step_index = 0

block = blocks[st.session_state.step_index]

st.title("분석 단계")
st.subheader("아래 프롬프트 내용 기반 분석을 시작합니다.")

# 사용자 입력 받기
st.markdown("### 사용자 입력")
user_inputs["건축주"] = st.text_input("건축주", user_inputs.get("건축주", ""))
user_inputs["주소"] = st.text_input("주소", user_inputs.get("주소", ""))
user_inputs["참고사항"] = st.text_area("참고사항", user_inputs.get("참고사항", ""))
user_inputs["PDF내용"] = st.text_area("PDF 요약 내용", user_inputs.get("PDF내용", ""))

# 분석용 프롬프트 구성
st.markdown("### 분석용 프롬프트")
formatted_prompt = block["prompt"]
for key, value in user_inputs.items():
    formatted_prompt = formatted_prompt.replace(f"{{{{{key}}}}}", value)

# {{prompt_text}}도 치환
if "{{prompt_text}}" in formatted_prompt:
    formatted_prompt = formatted_prompt.replace("{{prompt_text}}", block.get("title", ""))

st.text_area("📄 최종 프롬프트 (LLM 입력값)", formatted_prompt, height=250)

# 분석 버튼
if st.button("🔍 분석 실행"):
    with st.spinner("LLM 추론 중..."):
        try:
            result = agent.run_analysis(formatted_prompt)
            st.success("✅ 분석 완료!")
            st.markdown("### 📌 분석 결과")
            st.markdown(result)
            st.session_state["last_result"] = result
        except Exception as e:
            st.error(f"❌ 분석 중 오류 발생: {e}")

# 다음 단계로 이동
if st.button("➡ 다음 단계 진행"):
    if st.session_state.step_index < len(blocks) - 1:
        st.session_state.step_index += 1
        st.rerun()
    else:
        st.info("마지막 단계입니다.")
