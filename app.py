
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
from webpage_generator import create_webpage_download_button

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

if "total_cost" not in st.session_state:
    st.session_state.total_cost = 0.0

if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = {"input": 0, "output": 0}

# API 사용 호출부에 아래 라인 예시로 추가(각 run_... 함수 실행 때마다 +=1)
# st.session_state.api_calls += 1

with st.sidebar:
    st.markdown("### 🔧 시스템 상태")
    st.info(f"Claude API: {'✅' if os.environ.get('ANTHROPIC_API_KEY') else '❌'}")
    st.info(f"SerpAPI: {'✅' if os.environ.get('SERP_API_KEY') else '❌'}")
    
    st.markdown("### 💰 API 사용량")
    
    # 사용량 정보를 더 자세히 표시
    col1, col2 = st.columns(2)
    with col1:
        st.metric("API 호출 횟수", f"{st.session_state.api_calls}")
        st.metric("총 비용", f"${st.session_state.total_cost:.4f}")
    with col2:
        st.metric("입력 토큰", f"{st.session_state.total_tokens['input']:,}")
        st.metric("출력 토큰", f"{st.session_state.total_tokens['output']:,}")
    
    # 한국어 비용 표시
    krw_rate = 1300  # USD to KRW 환율 (대략적)
    krw_cost = st.session_state.total_cost * krw_rate
    st.info(f"💡 예상 원화 비용: 약 {krw_cost:,.0f}원", icon="💰")
    
    # 평균 비용 정보
    if st.session_state.api_calls > 0:
        avg_cost = st.session_state.total_cost / st.session_state.api_calls
        st.caption(f"평균 호출당 비용: ${avg_cost:.4f}")
    
    # 실시간 상태 표시
    if st.session_state.api_calls > 0:
        st.success(f"🔄 마지막 업데이트: {time.strftime('%H:%M:%S')}")
    
    # 사용량 업데이트 알림
    if "last_usage_update" not in st.session_state:
        st.session_state.last_usage_update = None
    
    if st.session_state.last_usage_update != st.session_state.api_calls:
        st.session_state.last_usage_update = st.session_state.api_calls
        st.info("📊 사용량이 업데이트되었습니다!")
    

    
    # 사용량 관리 버튼들
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 초기화", type="secondary"):
            st.session_state.api_calls = 0
            st.session_state.total_cost = 0.0
            st.session_state.total_tokens = {"input": 0, "output": 0}
            st.success("사용량이 초기화되었습니다!")
            st.rerun()
    
    with col2:
        if st.button("🔄 새로고침", type="secondary"):
            st.rerun()
    
    with col3:
        # 사용량 데이터 내보내기
        usage_data = {
            "api_calls": st.session_state.api_calls,
            "total_cost_usd": st.session_state.total_cost,
            "total_cost_krw": st.session_state.total_cost * 1300,
            "input_tokens": st.session_state.total_tokens["input"],
            "output_tokens": st.session_state.total_tokens["output"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        st.download_button(
            label="📊 내보내기",
            data=str(usage_data),
            file_name=f"api_usage_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )

# ─── 초기화 ─────────────────────────────────────────────
init_user_state()



# ─── 1. 프로젝트 기본 정보 입력 (탭 위에 배치) ─────────────────────────

# API 사용량 표시 (메인 영역)
if st.session_state.api_calls > 0:
    with st.container():
        st.markdown("### 💰 현재 API 사용량")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 호출", f"{st.session_state.api_calls}")
        with col2:
            st.metric("총 비용", f"${st.session_state.total_cost:.4f}")
        with col3:
            krw_cost = st.session_state.total_cost * 1300
            st.metric("예상 원화", f"{krw_cost:,.0f}원")
        
        # 상세 사용량 정보
        with st.expander("📊 상세 사용량 정보", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("입력 토큰", f"{st.session_state.total_tokens['input']:,}")
                st.metric("출력 토큰", f"{st.session_state.total_tokens['output']:,}")
            with col2:
                if st.session_state.api_calls > 0:
                    avg_cost = st.session_state.total_cost / st.session_state.api_calls
                    st.metric("평균 호출당 비용", f"${avg_cost:.4f}")
                    avg_tokens = (st.session_state.total_tokens['input'] + st.session_state.total_tokens['output']) / st.session_state.api_calls
                    st.metric("평균 토큰", f"{avg_tokens:,.0f}")
        
        # 사용량 상태 표시
        if st.session_state.total_cost > 0:
            progress_ratio = min(st.session_state.total_cost / 10.0, 1.0)  # $10 기준
            st.progress(progress_ratio, text=f"사용량 진행률: {progress_ratio*100:.1f}%")
        
        # 테스트 버튼 (개발용)
        if st.button("🧪 테스트 API 호출", type="secondary"):
            st.session_state.api_calls += 1
            st.session_state.total_cost += 0.01
            st.session_state.total_tokens["input"] += 100
            st.session_state.total_tokens["output"] += 50
            st.success("테스트 API 호출이 추가되었습니다!")
            st.rerun()

st.markdown("### 프로젝트 기본 정보")

# 접을 수 있는 섹션
with st.expander("프로젝트 정보 입력", expanded=st.session_state.get('show_project_info', True)):
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("프로젝트명", key="project_name", placeholder="예: Woori Bank Dasan Campus")
        st.text_input("건축주", key="owner", placeholder="예: Woori Bank")
        st.text_input("대지위치", key="site_location", placeholder="예: Namyangju-si, Gyeonggi-do")
        st.text_input("대지면적", key="site_area", placeholder="예: 30,396.0㎡ ")
    
    with col2:
        st.text_input("용적률", key="zoning", placeholder="예: General Residential Zone")
        st.text_input("건물용도", key="building_type", placeholder="예: Training Center")
        st.text_input("프로젝트 목표", key="project_goal", placeholder="예: Develop an innovative training campus...")
    
    # PDF 업로드
    uploaded_pdf = st.file_uploader("📎 PDF 업로드", type=["pdf"])
    if uploaded_pdf:
        # PDF 처리 로직 (기존 app.py에서 가져옴)
        pdf_bytes = uploaded_pdf.read()
        temp_path = "temp_uploaded.pdf"
        with open(temp_path, "wb") as f:
            f.write(pdf_bytes)
        
        from utils_pdf_vector import save_pdf_chunks_to_chroma
        save_pdf_chunks_to_chroma(temp_path, pdf_id="projectA")
        st.success("✅ PDF 벡터DB 저장 완료!")
        
        # PDF 텍스트 추출 및 요약
        from utils import extract_text_from_pdf
        from summary_generator import summarize_pdf, extract_site_analysis_fields
        pdf_text = extract_text_from_pdf(pdf_bytes)
        pdf_summary = summarize_pdf(pdf_text)
        set_pdf_summary(pdf_summary)
        st.session_state["site_fields"] = extract_site_analysis_fields(pdf_text)
        st.session_state["uploaded_pdf"] = uploaded_pdf
        st.success("✅ PDF 요약 완료!")
    
    # 정보 입력 완료 버튼
    if st.button("정보 입력 완료", type="primary"):
        st.session_state.show_project_info = False
        st.success("프로젝트 정보 입력이 완료되었습니다!")
        st.rerun()

# ─── 사이드바에 전체 프롬프트 블록 리스트 (프로젝트 정보 완료 후 표시) ─────────────────────────
if not st.session_state.get('show_project_info', True):
    st.sidebar.markdown("### 📋 전체 분석 단계")
    
    # 프롬프트 블록 로드
    from prompt_loader import load_prompt_blocks
    blocks = load_prompt_blocks()
    extra_blocks = blocks["extra"]
    
    # 건축설계 발표용 Narrative와 ArchiRender GPT 제외
    excluded_ids = {"claude_narrative", "midjourney_prompt"}
    available_blocks = [block for block in extra_blocks if block["id"] not in excluded_ids]
    
    # 현재 선택된 단계들 (제거된 단계 제외)
    current_step_ids = set()
    if st.session_state.get('workflow_steps'):
        for step in st.session_state.workflow_steps:
            if step.id not in st.session_state.get('removed_steps', set()):
                current_step_ids.add(step.id)
    
    # 추가된 단계들도 포함
    added_step_ids = st.session_state.get('added_steps', set())
    current_step_ids.update(added_step_ids)
    
    # 추천 단계들 (제외)
    recommended_step_ids = set()
    if st.session_state.get('current_workflow'):
        from analysis_system import AnalysisSystem
        system = AnalysisSystem()
        # selected_objectives가 없을 경우 빈 리스트 사용
        selected_objectives = st.session_state.get('selected_objectives', [])
        if selected_objectives:  # 빈 리스트가 아닐 때만 처리
            for objective in selected_objectives:
                if objective in system.recommended_steps:
                    recommended_step_ids.update({step.id for step in system.recommended_steps[objective]})
    
    st.sidebar.write("**선택 가능한 단계**:")
    
    # 단계 추가 상태 관리
    if 'sidebar_step_added' not in st.session_state:
        st.session_state.sidebar_step_added = False
    
    for block in available_blocks:
        block_id = block["id"]
        is_selected = block_id in current_step_ids
        is_recommended = block_id in recommended_step_ids
        
        # 모든 단계를 표시 (추천 단계도 포함)
        if is_selected:
            st.sidebar.markdown(f"~~{block['title']}~~ *(선택됨)*")
        else:
            # 선택 가능한 단계
            if st.sidebar.button(f"➕ {block['title']}", key=f"add_block_{block_id}"):
                # 단계 추가
                from analysis_system import AnalysisStep
                new_step = AnalysisStep(
                    id=block_id,
                    title=block['title'],
                    description=block.get('description', ''),
                    is_optional=True,
                    order=len(st.session_state.get('workflow_steps', [])) + 1,
                    category="추가 단계"
                )
                
                if 'workflow_steps' not in st.session_state:
                    st.session_state.workflow_steps = []
                
                st.session_state.workflow_steps.append(new_step)
                st.session_state.sidebar_step_added = True
                st.sidebar.success(f"'{block['title']}' 단계가 추가되었습니다!")
    
    # 사이드바 단계 추가 후 상태 초기화
    if st.session_state.sidebar_step_added:
        st.session_state.sidebar_step_added = False

# ─── 2. 새로운 탭 기반 인터페이스 ───────────────────────────
from workflow_ui import render_tabbed_interface

# 탭 기반 인터페이스 렌더링
render_tabbed_interface()

# ─── 4. 누적된 이전 분석 결과 ───────────────────────────
if st.session_state.cot_history:
    st.markdown("### 누적 분석 결과")
    for entry in st.session_state.cot_history:
        st.markdown(f"#### {entry['step']}")
        st.markdown(f"**요약:** {entry.get('summary', '')}")
        st.markdown(f"**인사이트:** {entry.get('insight', '')}")
        st.markdown(f"---\n{entry['result']}")
        st.markdown("---")

# 웹페이지 생성과 전체 분석 보고서는 보고서 생성 탭으로 이동

# PDF 업로드 시 디버깅 정보
if st.session_state.get('uploaded_pdf'):
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
