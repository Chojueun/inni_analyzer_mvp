
# app.py
import streamlit as st
import os
import base64
import time
from prompt_loader import load_prompt_blocks
from user_state import (
    init_user_state, get_user_inputs, set_pdf_summary,
    get_pdf_summary, save_step_result,
    get_current_step_index
)
from utils import extract_summary, extract_insight
from streamlit_sortables import sort_items
from summary_generator import summarize_pdf, extract_site_analysis_fields
from user_state import append_step_history
from utils_pdf_vector import save_pdf_chunks_to_chroma
from init_dspy import *
from agent_executor import (
    run_requirement_table,
    run_ai_reasoning,
    run_precedent_comparison,
    run_strategy_recommendation,
)
from dsl_to_prompt import *  # 모든 함수를 한 번에 import
from report_generator import generate_pdf_report, generate_word_report
from PIL import Image

# dA-logo.png가 프로젝트 폴더에 있어야 함!
logo = Image.open("dA-logo.png")

# 방법 1: CSS로 강제 크기 조정
st.markdown("""
<style>
.sidebar .stImage img {
    width: 30px !important;
    height: auto !important;
}
</style>
""", unsafe_allow_html=True)

# PIL로 이미지를 직접 리사이즈
logo = Image.open("dA-logo.png")
logo_resized = logo.resize((100, int(100 * logo.height / logo.width)), Image.Resampling.LANCZOS)
st.sidebar.image(logo_resized, use_column_width=False)


BANNER_HEIGHT = 220

st.markdown(f"""
    <style>
    .banner-bg {{
        position: fixed;
        top: 0; left: 0; right: 0;
        width: 100vw;
        height: {BANNER_HEIGHT}px;
        background: #F8F9FA;
        border-bottom: 2.7px solid #08B89D;
        z-index: 1000;
        display: flex;
        flex-direction: column;
        justify-content: flex-end;
        align-items: center;
        padding-bottom: 20px;
        margin-top: 0;  /* 위쪽 마진 제거 */
    }}
    .banner-title {{
        font-size: 2.9rem;
        font-weight: 900;
        color: #111;
        font-family: 'Montserrat', 'Inter', sans-serif;
        letter-spacing: -2px;
        margin-bottom: 6px;
        line-height: 1.13;
    }}
    .banner-subtitle {{
        font-size: 1.16rem;
        font-weight: 600;
        color: #08B89D;
        letter-spacing: 1.1px;
        font-family: 'Montserrat', 'Inter', sans-serif;
    }}
    /* 컨텐츠 전체를 배너 높이만큼 아래로 */
    .main .block-container {{
        margin-top: {BANNER_HEIGHT + 6}px;
    }}
    /* 사이드바도 배너 높이만큼 아래로 */
    .css-1d391kg {{
        margin-top: {BANNER_HEIGHT + 6}px;
    }}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <div class="banner-bg">
        <div class="banner-title">ArchInsight</div>
        <div class="banner-subtitle">AI-driven Project Insight & Workflow</div>
    </div>
""", unsafe_allow_html=True)


# ──────────────────────────────
# 3. API 사용량 카운트 기능 (직접 숫자로)
if "api_calls" not in st.session_state:
    st.session_state.api_calls = 0

# API 사용 호출부에 아래 라인 예시로 추가(각 run_... 함수 실행 때마다 +=1)
# st.session_state.api_calls += 1

with st.sidebar:
    st.markdown("### 🔧 시스템 상태")
    st.info(f"Claude API: {'✅' if os.environ.get('ANTHROPIC_API_KEY') else '❌'}")
    st.info(f"SerpAPI: {'✅' if os.environ.get('SERP_API_KEY') else '❌'}")
    st.markdown("### 🔧 API 사용량")
    st.info(f"API 호출 횟수: {st.session_state.api_calls}")


# ─── 초기화 ─────────────────────────────────────────────
init_user_state()


# ─── 1. 사용자 입력 & PDF 업로드 ─────────────────────────
st.sidebar.header("📥 프로젝트 기본 정보 입력")
user_inputs = get_user_inputs()

uploaded_pdf = st.sidebar.file_uploader("📎 PDF 업로드", type=["pdf"])
if uploaded_pdf:
    # PDF 처리
    pdf_bytes = uploaded_pdf.read()
    temp_path = "temp_uploaded.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)
    save_pdf_chunks_to_chroma(temp_path, pdf_id="projectA")
    st.sidebar.success("✅ PDF 벡터DB 저장 완료!")

    # PDF 텍스트 추출 및 요약
    from utils import extract_text_from_pdf
    pdf_text = extract_text_from_pdf(pdf_bytes)
    pdf_summary = summarize_pdf(pdf_text)
    set_pdf_summary(pdf_summary)
    st.session_state["site_fields"] = extract_site_analysis_fields(pdf_text)
    st.sidebar.success("✅ PDF 요약 완료!")

# PDF 업로드 상태 표시
if uploaded_pdf:
    st.sidebar.success("✅ PDF 업로드 완료")
else:
    st.sidebar.warning("⚠️ PDF를 업로드해주세요")

# ─── 2. 새로운 분석 시스템 ───────────────────────────
from analysis_system import AnalysisSystem, PurposeType, ObjectiveType
from workflow_ui import (
    init_analysis_system, render_purpose_selection, 
    render_objective_selection, render_workflow_suggestion,
    render_workflow_steps, render_optional_steps_addition,
    render_step_reordering, render_workflow_confirmation
)

# 분석 시스템 초기화
init_analysis_system()

blocks = load_prompt_blocks()
extra_blocks = blocks["extra"]
blocks_by_id = {b["id"]: b for b in extra_blocks}

# 탭으로 기존 방식과 새로운 방식 선택
tab1, tab2 = st.tabs(["🏗️ 새로운 분석 시스템", "📋 기존 분석 방식"])

with tab1:
    st.markdown("### 🏗️ ArchInsight 분석 시스템")
    st.write("프로젝트 용도와 목적에 따른 맞춤형 분석 워크플로우를 구성하세요.")
    
    # 1. 용도 선택
    purpose = render_purpose_selection()
    
    if purpose:
        # 2. 목적 선택
        objectives = render_objective_selection(purpose)
        
        if objectives:
            # 3. 워크플로우 제안
            workflow = render_workflow_suggestion(purpose, objectives)
            
            if workflow:
                # 4. 번외 단계 추가
                render_optional_steps_addition()
                
                # 5. 순서 변경
                render_step_reordering()
                
                # 6. 분석 실행
                render_workflow_confirmation()
                
                # 워크플로우를 기존 시스템과 연동
                if st.session_state.workflow_steps:
                    st.session_state.ordered_blocks = []
                    for step in st.session_state.workflow_steps:
                        # 기존 블록과 매핑
                        block_id = step.id
                        if block_id in blocks_by_id:
                            st.session_state.ordered_blocks.append(blocks_by_id[block_id])

with tab2:
    st.markdown("### 📋 기존 분석 방식")
    
    # 기존 블럭 로드 & 단계 선택
    blocks = load_prompt_blocks()
    extra_blocks = blocks["extra"]
    blocks_by_id = {b["id"]: b for b in extra_blocks}

    st.markdown("🔲 **분석에 포함할 단계 선택**")
    selected_ids = []
    for blk in extra_blocks:
        if st.checkbox(blk["title"], key=f"sel_{blk['id']}"):
            selected_ids.append(blk["id"])

    # 선택된 블럭 순서 조정
    if selected_ids:
        selected_blocks = [blocks_by_id[sid] for sid in selected_ids]
        titles = [blk["title"] for blk in selected_blocks]
        sort_key = "block_sorter_" + "_".join(selected_ids)
        ordered_titles = sort_items(titles, key=sort_key)
        ordered_blocks = [next(blk for blk in selected_blocks if blk["title"] == t)
                          for t in ordered_titles]

        # 화면에 박스로 표시
        cols = st.columns(len(ordered_blocks))
        for col, blk in zip(cols, ordered_blocks):
            col.markdown(
                f"<div style='background:#e63946; color:white; "
                f"padding:8px; border-radius:4px; text-align:center;'>"
                f"{blk['title']}</div>",
                unsafe_allow_html=True,
            )
        st.markdown("---")
    else:
        ordered_blocks = []
    
    # 기존 방식의 ordered_blocks를 session_state에 저장
    st.session_state.ordered_blocks = ordered_blocks if 'ordered_blocks' not in st.session_state else st.session_state.ordered_blocks

# ─── 4. 누적된 이전 분석 결과 ───────────────────────────
if st.session_state.cot_history:
    st.markdown("### 🧠 누적 분석 결과")
    for entry in st.session_state.cot_history:
        st.markdown(f"#### {entry['step']}")
        st.markdown(f"**요약:** {entry.get('summary', '')}")
        st.markdown(f"**인사이트:** {entry.get('insight', '')}")
        st.markdown(f"---\n{entry['result']}")
        st.markdown("---")

# ─── 5. 명령어 기반 분석 흐름 ─────────────────────────────
cmd = st.text_input("▶ 명령어 입력 (예: 시작 / 분석 진행 / N단계 진행 / 보고서 생성)")

if cmd.strip() == "시작":
    st.session_state.current_step_index = 0
    st.session_state.cot_history = []
    st.success("모든 입력이 완료되었습니다. '분석 진행'을 입력하세요.")

elif cmd.strip() == "분석 진행" or cmd.strip().endswith("단계 진행"):
    # PDF 업로드 상태 확인
    if not uploaded_pdf:
        st.error("❌ PDF를 먼저 업로드해주세요!")
        st.stop()
    
    # 필수 입력값 검증
    required_fields = ["project_name", "owner", "site_location", "site_area", "building_type", "project_goal"]
    missing_fields = [field for field in required_fields if not user_inputs.get(field, "").strip()]
    
    if missing_fields:
        st.error(f"❌ 다음 필수 정보를 입력해주세요: {', '.join(missing_fields)}")
        st.stop()
    
    # PDF 처리 상태 확인
    pdf_summary = get_pdf_summary()
    if not pdf_summary:
        st.error("❌ PDF 처리가 완료되지 않았습니다. PDF를 다시 업로드해주세요.")
        st.stop()
    
    # 새로운 분석 시스템의 워크플로우 사용
    ordered_blocks = st.session_state.get('ordered_blocks', [])
    
    # 실행할 단계 번호 결정
    if cmd.strip() == "분석 진행":
        idx = get_current_step_index()
    else:
        try:
            idx = int(cmd.strip().replace("단계 진행", "")) - 1
        except ValueError:
            st.error("'N단계 진행' 형식으로 입력해주세요.")
            idx = None

    # 유효성 검사
    if idx is not None and 0 <= idx < len(ordered_blocks):
        blk = ordered_blocks[idx]
        step_id = blk["id"]
        prev = "\n".join(f"[{h['step']}] {h['result']}" for h in st.session_state.cot_history)
        
        # site_fields 안전하게 가져오기
        site_fields = st.session_state.get("site_fields", {})
        if not site_fields:
            st.warning("⚠️ PDF에서 사이트 정보를 추출하지 못했습니다. 기본값으로 진행합니다.")
            site_fields = {
                "site_location": user_inputs.get("site_location", ""),
                "site_area": user_inputs.get("site_area", ""),
                "zoning": user_inputs.get("zoning", "")
            }

        # 단계별 상태 초기화
        if "current_step_outputs" not in st.session_state:
            st.session_state.current_step_outputs = {}
        if st.session_state.current_step_outputs.get("step_id") != step_id:
            st.session_state.current_step_outputs = {"step_id": step_id}
        outputs = st.session_state.current_step_outputs

        # 이미 완료된 단계인지 확인
        cot_done_steps = [h['step'] for h in st.session_state.cot_history]
        if blk['title'] in cot_done_steps:
            st.info(f"이미 분석이 완료된 단계입니다. 다음 단계로 이동하세요.")
        else:
            # 통합 분석 버튼
            if st.button(f"🔍 {blk['title']} 통합 분석 실행", key=f"analyze_{step_id}_{idx}"):
                with st.spinner(f"{blk['title']} 통합 분석 중..."):
                    # PDF 요약을 딕셔너리 형태로 변환
                    pdf_summary_dict = {
                        "pdf_summary": pdf_summary,
                        "project_name": user_inputs.get("project_name", ""),
                        "owner": user_inputs.get("owner", ""),
                        "site_location": user_inputs.get("site_location", ""),
                        "site_area": user_inputs.get("site_area", ""),
                        "building_type": user_inputs.get("building_type", ""),
                        "project_goal": user_inputs.get("project_goal", "")
                    }
                    
                    # 통합 프롬프트 생성
                    base_prompt = convert_dsl_to_prompt(blk["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                    
                    # 단계별로 다른 분석 실행
                    results = {}
                    output_structure = blk["content_dsl"].get("output_structure", [])
                    
                    # 동시 실행 대신 순차 실행
                    if output_structure:
                        # 순차적으로 실행 (동시 실행 대신)
                        for i, structure in enumerate(output_structure):
                            if i == 0:
                                prompt = prompt_requirement_table(blk["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                                results[f"result_{i}"] = run_requirement_table(prompt)
                                time.sleep(5)  # 5초 대기
                            elif i == 1:
                                prompt = prompt_ai_reasoning(blk["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                                results[f"result_{i}"] = run_ai_reasoning(prompt)
                                time.sleep(5)  # 5초 대기
                            elif i == 2:
                                prompt = prompt_precedent_comparison(blk["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                                results[f"result_{i}"] = run_precedent_comparison(prompt)
                                time.sleep(5)  # 5초 대기
                            elif i == 3:
                                prompt = prompt_strategy_recommendation(blk["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                                results[f"result_{i}"] = run_strategy_recommendation(prompt)
                    else:
                        # 기본 4개 분석 (fallback)
                        prompt_req = base_prompt + "\n\n⚠️ 반드시 '요구사항 정리표' 항목만 표로 생성. 그 외 항목은 출력하지 마세요."
                        results["requirement_table"] = run_requirement_table(prompt_req)
                        
                        prompt_reason = base_prompt + "\n\n⚠️ 반드시 'AI reasoning' 항목(Chain-of-Thought 논리 해설)만 생성. 그 외 항목은 출력하지 마세요."
                        results["ai_reasoning"] = run_ai_reasoning(prompt_reason)
                        
                        prompt_precedent = base_prompt + "\n\n⚠️ 반드시 '유사 사례 비교' 표 또는 비교 해설만 출력. 그 외 항목은 출력하지 마세요."
                        results["precedent_comparison"] = run_precedent_comparison(prompt_precedent)
                        
                        prompt_strategy = base_prompt + "\n\n⚠️ 반드시 '전략적 제언 및 시사점'만 출력. 그 외 항목은 출력하지 마세요."
                        results["strategy_recommendation"] = run_strategy_recommendation(prompt_strategy)
                    
                    # 결과를 session_state에 저장
                    outputs.update(results)
                    outputs["saved"] = True
                    
                    # 탭으로 분할 표시
                    st.markdown(f"### 📋 {blk['title']} 분석 결과")
                    
                    if output_structure:
                        # 동적으로 탭 생성
                        tab_names = output_structure
                        tabs = st.tabs(tab_names)
                        
                        # 각 탭에 해당하는 결과 표시
                        for i, (tab, tab_name) in enumerate(zip(tabs, tab_names)):
                            with tab:
                                st.markdown(f"#### {tab_name}")
                                result_key = f"result_{i}"
                                if result_key in results:
                                    st.markdown(results[result_key])
                                else:
                                    st.info("분석 결과가 준비되지 않았습니다.")
                    else:
                        # 기본 4개 탭 (fallback)
                        tab1, tab2, tab3, tab4 = st.tabs([" 요구사항", " AI 추론", " 사례비교", "✅ 전략제언"])
                        
                        with tab1:
                            st.markdown("#### 📊 요구사항 정리표")
                            st.markdown(results.get("requirement_table", "결과 없음"))
                        
                        with tab2:
                            st.markdown("#### 🧠 AI 추론 해설")
                            st.markdown(results.get("ai_reasoning", "결과 없음"))
                        
                        with tab3:
                            st.markdown("#### 🧾 유사 사례 비교")
                            st.markdown(results.get("precedent_comparison", "결과 없음"))
                        
                        with tab4:
                            st.markdown("#### ✅ 전략적 제언 및 시사점")
                            st.markdown(results.get("strategy_recommendation", "결과 없음"))
                    
                    # 전체 결과를 cot_history에 저장
                    if output_structure:
                        # output_structure에 따라 동적으로 결과 조합
                        full_result_parts = []
                        for i, structure in enumerate(output_structure):
                            result_key = f"result_{i}"
                            if result_key in results:
                                full_result_parts.append(f"{structure}\n{results[result_key]}")
                        
                        full_result = "\n\n".join(full_result_parts)
                    else:
                        # 기본 4개 키 사용 (fallback)
                        full_result = (
                            "📊 요구사항 정리표\n" + results.get("requirement_table", "결과 없음") + "\n\n" +
                            "🧠 AI 추론 해설\n" + results.get("ai_reasoning", "결과 없음") + "\n\n" +
                            "🧾 유사 사례 비교\n" + results.get("precedent_comparison", "결과 없음") + "\n\n" +
                            "✅ 전략적 제언 및 시사점\n" + results.get("strategy_recommendation", "결과 없음")
                        )
                    
                    st.session_state.cot_history.append({
                        "step": blk["title"],
                        "result": full_result,
                        "summary": extract_summary(full_result),
                        "insight": extract_insight(full_result)
                    })
                    
                    save_step_result(blk["id"], full_result)
                    append_step_history(
                        step_id=blk["id"],
                        title=blk["title"],
                        prompt="통합 분석",
                        result=full_result
                    )
                    
                    st.success("✅ 통합 분석이 완료되었습니다! 다음 단계로 이동하세요.")
                    st.session_state.current_step_index = idx + 1
                    st.session_state.current_step_outputs = {}

            # 진행 상황 표시
            if outputs.get("saved"):
                st.info("✅ 이 단계의 분석이 완료되었습니다.")
            else:
                st.info("💡 위의 '통합 분석 실행' 버튼을 클릭하여 분석을 시작하세요.")

        # 안내 메시지
        if st.session_state.current_step_index < len(ordered_blocks):
            st.info(
                f"■ '{blk['title']}' 완료. 다음: "
                f"'{st.session_state.current_step_index+1}단계 진행'"
            )
        else:
            st.info("■ 모든 단계 완료! '보고서 생성'을 입력하세요.")

    else:
        st.warning("유효한 단계가 아닙니다. 선택된 단계와 순서를 확인해주세요.")

elif cmd.strip() == "보고서 생성":
    if not st.session_state.cot_history:
        st.error("❌ 생성된 분석 결과가 없습니다. 먼저 분석을 진행해주세요.")
    else:
        st.markdown("### 📄 보고서 생성")
        
        # 프로젝트 정보
        project_info = f"""
# 한국 {user_inputs.get('project_name', '프로젝트')} 분석 보고서

## 한국 프로젝트 기본 정보
- **프로젝트명**: {user_inputs.get('project_name', 'N/A')}
- **소유자**: {user_inputs.get('owner', 'N/A')}
- **위치**: {user_inputs.get('site_location', 'N/A')}
- **면적**: {user_inputs.get('site_area', 'N/A')}
- **건물유형**: {user_inputs.get('building_type', 'N/A')}
- **프로젝트 목표**: {user_inputs.get('project_goal', 'N/A')}

---
"""
        
        # 분석 결과 수집
        analysis_content = ""
        for i, entry in enumerate(st.session_state.cot_history, 1):
            analysis_content += f"""
## {i}. {entry['step']}

### 📊 요약
{entry.get('summary', '요약 정보 없음')}

### 🧠 인사이트
{entry.get('insight', '인사이트 정보 없음')}

### 📋 상세 분석 결과
{entry['result']}

---
"""
        
        # 전체 보고서 내용
        full_report = project_info + analysis_content
        
        # 보고서 미리보기
        st.markdown("#### 📄 보고서 미리보기")
        st.markdown(full_report)
        
        # PDF 생성 버튼
        if st.button("💾 PDF 보고서 다운로드", key="download_pdf"):
            try:
                pdf_bytes = generate_pdf_report(full_report, user_inputs)
                st.download_button(
                    label="💾 PDF 다운로드",
                    data=pdf_bytes,
                    file_name=f"{user_inputs.get('project_name', '분석보고서')}_보고서.pdf",
                    mime="application/pdf"
                )
                st.success("✅ PDF 보고서가 생성되었습니다!")
            except Exception as e:
                st.error(f"❌ PDF 생성 중 오류 발생: {e}")
        
        # Word 문서 생성 버튼 (조건부)
        try:
            from report_generator import DOCX_AVAILABLE
            if DOCX_AVAILABLE:
                if st.button("💾 Word 문서 다운로드", key="download_word"):
                    try:
                        docx_bytes = generate_word_report(full_report, user_inputs)
                        st.download_button(
                            label="💾 Word 다운로드",
                            data=docx_bytes,
                            file_name=f"{user_inputs.get('project_name', '분석보고서')}_보고서.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                        st.success("✅ Word 문서가 생성되었습니다!")
                    except Exception as e:
                        st.error(f"❌ Word 문서 생성 중 오류 발생: {e}")
            else:
                st.info("ℹ️ Word 문서 기능을 사용하려면 'pip install python-docx'를 실행해주세요.")
        except ImportError:
            st.info("ℹ️ Word 문서 기능을 사용하려면 'pip install python-docx'를 실행해주세요.")


# PDF 업로드 시 디버깅 정보
if uploaded_pdf:
    st.sidebar.success("✅ PDF 업로드 완료")
    
    # PDF 처리 상태 확인
    if st.session_state.get("pdf_summary"):
        st.sidebar.success("✅ PDF 요약 완료")
    else:
        st.sidebar.warning("⚠️ PDF 요약 처리 중...")
    
    # 벡터 DB 상태 확인
    try:
        from utils_pdf_vector import collection
        if collection:
            st.sidebar.success("✅ 벡터 DB 연결 완료")
        else:
            st.sidebar.error("❌ 벡터 DB 연결 실패")
    except:
        st.sidebar.error("❌ 벡터 DB 초기화 실패")



# Rate Limit 경고
if st.session_state.get("api_calls", 0) > 10:
    st.sidebar.warning("⚠️ API 호출이 많습니다. 잠시 대기해주세요.")

# Rate Limit 오류 발생 시 대기 후 재시도
import time

if "rate_limit_wait" not in st.session_state:
    st.session_state.rate_limit_wait = False

if st.session_state.rate_limit_wait:
    st.warning("⚠️ Rate Limit으로 인해 1분 대기 중입니다...")
    time.sleep(60)
    st.session_state.rate_limit_wait = False
    st.rerun()
