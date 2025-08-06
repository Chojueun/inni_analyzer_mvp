
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
        for objective in st.session_state.get('selected_objectives', []):
            if objective in system.recommended_steps:
                recommended_step_ids.update({step.id for step in system.recommended_steps[objective]})
    
    st.sidebar.write("**선택 가능한 단계**:")
    
    # 단계 추가 상태 관리
    if 'sidebar_step_added' not in st.session_state:
        st.session_state.sidebar_step_added = False
    
    for block in extra_blocks:
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

# ─── 5. 명령어 기반 분석 흐름 ─────────────────────────────
cmd = st.text_input("▶ 명령어 입력 (예: 시작 / 분석 진행 / N단계 진행 / 보고서 생성)")

if cmd.strip() == "시작":
    st.session_state.current_step_index = 0
    st.session_state.cot_history = []
    st.success("모든 입력이 완료되었습니다. '분석 진행'을 입력하세요.")

elif cmd.strip() == "분석 진행" or cmd.strip().endswith("단계 진행"):
    # PDF 업로드 상태 확인
    if not st.session_state.get('uploaded_pdf'):
        st.error("❌ PDF를 먼저 업로드해주세요!")
        st.stop()
    
    # 필수 입력값 검증
    user_inputs = get_user_inputs()
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

# ─── 웹페이지 생성 기능 ─────────────────────────────────────────────
if cmd.strip() == "보고서 생성":
    # user_inputs 먼저 가져오기
    user_inputs = get_user_inputs()
    
    # 분석 결과 수집
    analysis_results = []
    if st.session_state.get('cot_history'):
        for i, history in enumerate(st.session_state.cot_history):
            analysis_results.append({
                'step': history.get('step', f'단계 {i+1}'),
                'summary': history.get('summary', ''),
                'insight': history.get('insight', ''),
                'result': history.get('result', '')
            })
    
    # 프로젝트 정보
    project_info = {
        'project_name': user_inputs.get('project_name', '프로젝트'),
        'owner': user_inputs.get('owner', ''),
        'site_location': user_inputs.get('site_location', ''),
        'site_area': user_inputs.get('site_area', ''),
        'building_type': user_inputs.get('building_type', ''),
        'project_goal': user_inputs.get('project_goal', '')
    }
    
    # 웹페이지 생성 및 다운로드
    from webpage_generator import create_webpage_download_button
    create_webpage_download_button(analysis_results, project_info)
    
    # 기존 보고서 생성 로직도 유지
    if st.session_state.get('cot_history'):
        st.markdown("### 📋 전체 분석 보고서")
        
        # 프로젝트 정보 섹션
        st.markdown("#### 📋 프로젝트 기본 정보")
        project_info_text = f"""
        **프로젝트명**: {user_inputs.get('project_name', 'N/A')}
        **건축주**: {user_inputs.get('owner', 'N/A')}
        **대지위치**: {user_inputs.get('site_location', 'N/A')}
        **대지면적**: {user_inputs.get('site_area', 'N/A')}
        **건물용도**: {user_inputs.get('building_type', 'N/A')}
        **프로젝트 목표**: {user_inputs.get('project_goal', 'N/A')}
        """
        st.markdown(project_info_text)
        
        # 분석 결과 섹션
        st.markdown("#### 📊 분석 결과")
        for i, history in enumerate(st.session_state.cot_history):
            st.markdown(f"**{i+1}. {history.get('step', f'단계 {i+1}')}**")
            if history.get('summary'):
                st.markdown(f"**요약**: {history['summary']}")
            if history.get('insight'):
                st.markdown(f"**인사이트**: {history['insight']}")
            st.markdown(history.get('result', ''))
            st.markdown("---")
        
        # 전체 보고서 내용 생성
        full_report_content = project_info_text + "\n\n" + "\n\n".join([
            f"## {i+1}. {h.get('step', f'단계 {i+1}')}\n\n{h.get('result', '')}"
            for i, h in enumerate(st.session_state.cot_history)
        ])
        
        # 다운로드 버튼들
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 전체 보고서 다운로드 (TXT)
            st.download_button(
                label="📄 전체 보고서 다운로드 (TXT)",
                data=full_report_content,
                file_name=f"{user_inputs.get('project_name', '분석보고서')}_전체보고서.txt",
                mime="text/plain"
            )
        
        with col2:
            # PDF 다운로드 (기존 report_generator 사용)
            try:
                from report_generator import generate_pdf_report
                pdf_data = generate_pdf_report(full_report_content, user_inputs)
                
                st.download_button(
                    label="📄 PDF 다운로드",
                    data=pdf_data,
                    file_name=f"{user_inputs.get('project_name', '분석보고서')}_보고서.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"PDF 생성 중 오류가 발생했습니다: {str(e)}")
        
        with col3:
            # Word 다운로드 (기존 report_generator 사용)
            try:
                from report_generator import generate_word_report
                word_data = generate_word_report(full_report_content, user_inputs)
                
                st.download_button(
                    label="📄 Word 다운로드",
                    data=word_data,
                    file_name=f"{user_inputs.get('project_name', '분석보고서')}_보고서.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
            except Exception as e:
                st.error(f"Word 문서 생성 중 오류가 발생했습니다: {str(e)}")
    else:
        st.warning("생성된 분석 결과가 없습니다.")

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
