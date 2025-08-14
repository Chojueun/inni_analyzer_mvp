
# app.py
import streamlit as st
import os
import time
from prompt_loader import load_prompt_blocks
from user_state import (
    init_user_state, get_user_inputs, save_step_result, append_step_history, get_current_step_index
)
from summary_generator import summarize_pdf, extract_site_analysis_fields
from utils_pdf import save_pdf_chunks_to_chroma, get_pdf_summary_from_session, set_pdf_summary_to_session
from utils import extract_summary, extract_insight
from init_dspy import *
from dsl_to_prompt import (
    convert_dsl_to_prompt, prompt_requirement_table, prompt_ai_reasoning,
    prompt_precedent_comparison, prompt_strategy_recommendation
)
from agent_executor import (
    run_requirement_table, run_ai_reasoning,
    run_precedent_comparison, run_strategy_recommendation
)
from PIL import Image
from auth_system import init_auth, login_page, admin_panel, logout
from analysis_system import AnalysisStep, AnalysisSystem

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
st.sidebar.image(logo_resized, use_container_width=False)

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

# 인증 시스템 초기화
init_auth()

# 로그인 상태 확인
if not st.session_state.authenticated:
    login_page()
    st.stop()

# 로그인된 사용자 정보 표시
st.sidebar.markdown(f"### 👤 {st.session_state.current_user}")
if st.sidebar.button("로그아웃"):
    logout()

# 관리자만 접근 가능한 패널
if st.session_state.current_user == "admin":
    with st.sidebar.expander("관리자 패널"):
        admin_panel()

# 사이드바에서 실행 방식 선택 제거
with st.sidebar:
    st.markdown("### 🤖 AI 모델 선택")
    
    from init_dspy import get_model_info, get_available_models_sdk
    
    # SDK로 실시간 모델 목록 가져오기
    try:
        sdk_models = get_available_models_sdk()
        if sdk_models:
            display_models = sdk_models
            st.success(f"✅ SDK에서 {len(sdk_models)}개 모델 조회됨")
        else:
            from init_dspy import available_models
            display_models = available_models
            st.warning("⚠️ SDK 조회 실패, 기본 모델 목록 사용")
    except Exception as e:
        from init_dspy import available_models
        display_models = available_models
        st.error(f"❌ 모델 목록 조회 오류: {e}")
    
    # 현재 선택된 모델
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = "claude-3-5-sonnet-20241022"
    
    # 모델 선택 드롭다운
    selected_model = st.selectbox(
        "Claude 모델 선택",
        options=display_models,
        index=display_models.index(st.session_state.selected_model) if st.session_state.selected_model in display_models else 0,
        format_func=lambda x: f"{x} (SDK)" if x in sdk_models else f"{x} (기본)",
        help="분석에 사용할 Claude 모델을 선택하세요"
    )
    
    # 모델 변경 시 세션 상태만 업데이트 (DSPy 설정 변경 안함)
    if selected_model != st.session_state.selected_model:
        st.session_state.selected_model = selected_model
        st.success(f"✅ 모델이 {selected_model}로 변경되었습니다!")
    
    # 모델 정보 표시
    model_info = get_model_info()
    if selected_model in model_info:
        info = model_info[selected_model]
        st.info(f"""
        **{info['name']}**
        - 속도: {info['speed']}
        - 성능: {info['power']}
        - 비용: {info['cost']}
        - 용도: {info['best_for']}
        """)
    
    # 모델 새로고침 버튼
    if st.button("🔄 모델 목록 새로고침"):
        st.rerun()
    
    # 작업 유형별 모델 추천 (수정된 버전)
    st.markdown("#### 💡 작업별 추천 모델")
    
    task_recommendations = {
        "빠른 분석": "claude-3-5-haiku-20241022",
        "상세 분석": "claude-3-5-sonnet-20241022", 
        "복잡한 분석": "claude-3-opus-20240229",
        "비용 절약": "claude-3-haiku-20240307"
    }
    
    for task, model in task_recommendations.items():
        model_name = model_info.get(model, {}).get('name', model)
        if st.button(f"📋 {task}", key=f"recommend_{model}", help=f"{model_name} 사용"):
            # DSPy 설정 변경 없이 세션 상태만 업데이트
            st.session_state.selected_model = model
            st.success(f"✅ {task}용 모델({model_name})으로 변경되었습니다!")
            st.rerun()

# ─── 초기화 ─────────────────────────────────────────────
init_user_state()



# ─── 1. 프로젝트 기본 정보 입력 (탭 위에 배치) ─────────────────────────

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
        # PDF 처리 로직 (간단 저장만 사용)
        pdf_bytes = uploaded_pdf.read()
        temp_path = "temp_uploaded.pdf"
        with open(temp_path, "wb") as f:
            f.write(pdf_bytes)
        
        # 간단 저장 사용
        if save_pdf_chunks_to_chroma(temp_path, pdf_id="projectA"):
            st.success("✅ PDF 저장 완료!")
        else:
            st.error("❌ PDF 저장 실패!")
        
        # PDF 텍스트 추출 및 요약 (기존 코드)
        from utils_pdf import extract_text_from_pdf
        from summary_generator import summarize_pdf, extract_site_analysis_fields, analyze_pdf_comprehensive, get_pdf_quality_report

        pdf_text = extract_text_from_pdf(pdf_bytes, "bytes")

        # 새로운 고급 분석 사용
        comprehensive_result = analyze_pdf_comprehensive(pdf_text)

        # 기존 호환성을 위한 처리
        pdf_summary = comprehensive_result["summary"]
        set_pdf_summary_to_session(pdf_summary)
        st.session_state["site_fields"] = comprehensive_result["site_fields"]

        # 새로운 고급 정보 저장
        st.session_state["pdf_analysis_result"] = comprehensive_result
        st.session_state["pdf_quality_report"] = get_pdf_quality_report(pdf_text)

        # 품질 정보 표시
        quality = comprehensive_result["quality"]
        if quality["grade"] in ["A+", "A"]:
            st.success("✅ PDF 분석 품질: 우수")
        elif quality["grade"] in ["B+", "B"]:
            st.info("ℹ️ PDF 분석 품질: 양호")
        else:
            st.warning("⚠️ PDF 분석 품질: 개선 필요")

        st.success("✅ PDF 요약 완료!")
    
    # 정보 입력 완료 버튼
    if st.button("정보 입력 완료", type="primary"):
        st.session_state.show_project_info = False
        
        # 워크플로우 관련 상태 초기화
        st.session_state.workflow_steps = []
        st.session_state.removed_steps = set()
        st.session_state.added_steps = set()
        st.session_state.current_step_index = 0
        st.session_state.analysis_started = False
        st.session_state.cot_history = []
        st.session_state.ordered_blocks = []
        st.session_state.selected_purpose = None
        st.session_state.selected_objectives = []
        st.session_state.current_workflow = None
        
        st.success("프로젝트 정보 입력이 완료되었습니다!")
        st.rerun()

# ─── 사이드바에 추가 선택 가능한 단계들 (프로젝트 정보 완료 후 표시) ─────────────────────────
if not st.session_state.get('show_project_info', True):
    st.sidebar.markdown("### 📋 추가 선택 가능한 단계")
    
    # 프롬프트 블록 로드
    from prompt_loader import load_prompt_blocks
    blocks = load_prompt_blocks()
    extra_blocks = blocks["extra"]
    
    # 현재 선택된 단계들 (제거된 단계 제외)
    current_step_ids = set()
    if st.session_state.get('workflow_steps'):
        for step in st.session_state.workflow_steps:
            if step.id not in st.session_state.get('removed_steps', set()):
                current_step_ids.add(step.id)
    
    # 추가된 단계들도 포함
    added_step_ids = st.session_state.get('added_steps', set())
    current_step_ids.update(added_step_ids)
    
    # 자동 제안된 단계들 (제외)
    auto_suggested_ids = set()
    if st.session_state.get('current_workflow'):
        from analysis_system import AnalysisSystem
        system = AnalysisSystem()
        selected_purpose = st.session_state.get('selected_purpose')
        selected_objectives = st.session_state.get('selected_objectives', [])
        
        if selected_purpose and selected_objectives:
            # 용도별 권장 단계들
            purpose_enum = None
            for purpose in system.recommended_steps.keys():
                if purpose.value == selected_purpose:
                    purpose_enum = purpose
                    break
            
            if purpose_enum:
                auto_suggested_ids.update({step.id for step in system.recommended_steps[purpose_enum]})
    
    # 자동 제안되지 않은 추가 선택 가능한 단계들만 필터링
    additional_blocks = []
    for block in extra_blocks:
        block_id = block["id"]
        if block_id not in auto_suggested_ids and block_id not in current_step_ids:
            additional_blocks.append(block)
    
    if additional_blocks:
        st.sidebar.write("**추가로 선택 가능한 단계**:")
        
        # 단계 추가 상태 관리
        if 'sidebar_step_added' not in st.session_state:
            st.session_state.sidebar_step_added = False
        
        for block in additional_blocks:
            block_id = block["id"]
            
            # 선택 가능한 단계
            if st.sidebar.button(f"➕ {block['title']}", key=f"add_block_{block_id}"):
                # 단계 추가
                from analysis_system import AnalysisSystem
                system = AnalysisSystem()
                cot_order = system._load_recommended_cot_order()
                
                # 권장 순서에 따른 적절한 위치 찾기
                new_step_order = cot_order.get(block_id, len(st.session_state.get('workflow_steps', [])) + 1)
                
                new_step = AnalysisStep(
                    id=block_id,
                    title=block['title'],
                    description=block.get('description', ''),
                    is_optional=True,
                    order=new_step_order,
                    category="추가 단계"
                )
                
                if 'workflow_steps' not in st.session_state:
                    st.session_state.workflow_steps = []
                
                # 적절한 위치에 삽입
                st.session_state.workflow_steps.append(new_step)
                
                # 권장 순서로 재정렬
                sorted_steps = system.sort_steps_by_recommended_order(st.session_state.workflow_steps)
                for i, step in enumerate(sorted_steps, 1):
                    step.order = i
                
                st.session_state.workflow_steps = sorted_steps
                st.session_state.sidebar_step_added = True
                st.sidebar.success(f"'{block['title']}' 단계가 권장 순서에 맞게 추가되었습니다!")
        
        # 사이드바 단계 추가 후 상태 초기화
        if st.session_state.sidebar_step_added:
            st.session_state.sidebar_step_added = False
    else:
        st.sidebar.info("✅ 모든 관련 단계가 자동으로 선택되었습니다.")

# ─── 권장 CoT 순서 설명 ─────────────────────────
with st.expander("📖 권장 CoT 순서 가이드", expanded=False):
    st.markdown("""
    ### 🎯 권장 분석 순서 (초→중→후)
    
    **초기 단계 (1-6)**
    1. **doc_collector** — 문서 수집·목차화(근거 라벨 고정)
    2. **requirements_extractor** — 요구 분류·우선순위 도출
    3. **requirement_analysis** — 요구사항 매트릭스/제약·우선순위 정리
    4. **context_analyzer** — 암묵 의도·KPI 보정
    5. **task_comprehension** — 성공기준·전제조건·리스크 가설 확정
    6. **risk_strategist** (Gate-A) — 초기 리스크 레지스터; 임계 초과 시 3–5 재루프
    
    **중기 단계 (7-12)**
    7. **site_regulation_analysis** — 대지·법규 핵심 제약/기회
    8. **compliance_analyzer** (Baseline) (Gate-B) — 필수 규정 1차 체크
    9. **precedent_benchmarking** — 사례 인사이트/운영 모델
    10. **competitor_analyzer** — 경쟁 포지션·차별화(리테일/업무/숙박 필수)
    11. **design_trend_application** — 적용 가능한 트렌드 쇼트리스트
    12. **mass_strategy** — 매스 옵션 세트
    
    **후기 단계 (13-23)**
    13. **flexible_space_strategy** — 가변/확장 원칙(문화/교육/업무 등 필수)
    14. **concept_development** — 컨셉 문장·평가기준
    15. **area_programming** — 공간별 적정면적/배분 원칙
    16. **schematic_space_plan** — 평면·단면 스키매틱
    17. **ux_circulation_simulation** — 시나리오별 동선 시뮬(운수/의료/운동/리테일/노유자 필수)
    18. **design_requirement_summary** — 최종 요구·가이드라인(체크리스트 포함)
    19. **cost_estimation** — 공사비 모델/변동요인
    20. **operation_investment_analysis** — 운영·수익성 모델
    21. **architectural_branding_identity** — 브랜딩/차별화 메시지 정렬
    22. **action_planner** — 실행 체크리스트(담당·기한·리스크 링크)
    23. **proposal_framework** — 제안서 와이어프레임/슬라이드 구조
    """)

# ─── 분석 시작 전 단계 정렬 및 시작 ─────────────────────────
if st.session_state.get('workflow_steps'):
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 권장 순서 제안", type="secondary", help="선택된 단계들을 권장 CoT 순서로 재정렬합니다"):
            from analysis_system import AnalysisSystem
            system = AnalysisSystem()
            
            # 현재 단계들을 권장 순서로 정렬
            sorted_steps = system.sort_steps_by_recommended_order(st.session_state.workflow_steps)
            
            # 순서 번호 업데이트
            for i, step in enumerate(sorted_steps, 1):
                step.order = i
            
            st.session_state.workflow_steps = sorted_steps
            st.success("✅ 단계가 권장 순서로 재정렬되었습니다!")
            st.rerun()
    
    with col2:
        if st.button("🚀 분석 시작", type="primary", help="선택된 단계들로 분석을 시작합니다"):
            st.session_state.analysis_started = True
            st.session_state.current_step_index = 0
            st.success("🎯 분석이 시작되었습니다!")
            st.rerun()
    
    with col3:
        if st.button("👀 단계 목록 보기", help="현재 선택된 단계들의 순서를 확인합니다"):
            st.session_state.show_step_list = True
            st.rerun()

# ─── 단계 목록 표시 ─────────────────────────
if st.session_state.get('show_step_list', False):
    st.markdown("### 📋 현재 선택된 단계 목록")
    
    if st.session_state.get('workflow_steps'):
        # 권장 순서로 정렬
        from analysis_system import AnalysisSystem
        system = AnalysisSystem()
        sorted_steps = system.sort_steps_by_recommended_order(st.session_state.workflow_steps)
        
        for i, step in enumerate(sorted_steps, 1):
            col1, col2, col3 = st.columns([0.1, 0.7, 0.2])
            with col1:
                st.markdown(f"**{i}.**")
            with col2:
                st.markdown(f"**{step.title}**")
            with col3:
                if st.button(f"❌ 제거", key=f"remove_{step.id}"):
                    st.session_state.workflow_steps.remove(step)
                    st.success(f"'{step.title}' 단계가 제거되었습니다!")
                    st.rerun()
        
        if st.button("✅ 목록 닫기"):
            st.session_state.show_step_list = False
            st.rerun()
    else:
        st.info("선택된 단계가 없습니다.")

# ─── 3. 새로운 탭 기반 인터페이스 ───────────────────────────
from workflow_ui import render_tabbed_interface

# 탭 기반 인터페이스 렌더링 (이 부분만 남기고 나머지 중복 UI 제거)
render_tabbed_interface()

# ─── 4. 누적된 이전 분석 결과 ───────────────────────────
# 이 부분 제거 (탭 인터페이스에서 처리됨)
# if st.session_state.cot_history:
#     st.markdown("### 누적 분석 결과")
#     for entry in st.session_state.cot_history:
#         st.markdown(f"#### {entry['step']}")
#         st.markdown(f"**요약:** {entry.get('summary', '')}")
#         st.markdown(f"**인사이트:** {entry.get('insight', '')}")
#         st.markdown(f"---\n{entry['result']}")
#         st.markdown("---")

# 웹페이지 생성과 전체 분석 보고서는 보고서 생성 탭으로 이동

# PDF 업로드 시 디버깅 정보
if st.session_state.get('uploaded_pdf'):
    st.sidebar.success("✅ PDF 업로드 완료")
    
    # PDF 처리 상태 확인
    if st.session_state.get("pdf_summary"):
        st.sidebar.success("✅ PDF 요약 완료")
    else:
        st.sidebar.warning("⚠️ PDF 요약 처리 중...")
    
    # PDF 처리 상태 확인
    if st.session_state.get("pdf_chunks"):
        st.sidebar.success("✅ PDF 텍스트 저장 완료")
    else:
        st.sidebar.warning("⚠️ PDF 텍스트 처리 중...")

# Rate Limit 경고
if st.session_state.get("api_calls", 0) > 10:
    st.sidebar.warning("⚠️ API 호출이 많습니다. 잠시 대기해주세요.")

# Rate Limit 오류 발생 시 대기 후 재시도
if "rate_limit_wait" not in st.session_state:
    st.session_state.rate_limit_wait = False

if st.session_state.rate_limit_wait:
    st.warning("⚠️ Rate Limit으로 인해 1분 대기 중입니다...")
    time.sleep(60)
    st.session_state.rate_limit_wait = False
    st.rerun()
