#workflow_ui.py

"""
분석 시스템 핵심 구조 UI
- 용도/목적 분류
- 단계 자동 제안
- 필수 단계 포함
- 번외 항목 추가
- 순서 변경 및 추가/삭제
- 전체 순서 확정 및 분석 실행
"""

import streamlit as st
import json
from typing import List, Dict
from analysis_system import AnalysisSystem, PurposeType, ObjectiveType, AnalysisWorkflow, AnalysisStep

def init_analysis_system():
    """분석 시스템 초기화"""
    if "analysis_system" not in st.session_state:
        from analysis_system import AnalysisSystem
        st.session_state.analysis_system = AnalysisSystem()
    
    # 세션 상태 초기화
    if "selected_purpose" not in st.session_state:
        st.session_state.selected_purpose = None
    if "selected_objectives" not in st.session_state:
        st.session_state.selected_objectives = []
    if "workflow_suggested" not in st.session_state:
        st.session_state.workflow_suggested = False
    if "current_workflow" not in st.session_state:
        st.session_state.current_workflow = None
    if "workflow_steps" not in st.session_state:
        st.session_state.workflow_steps = []
    if "removed_steps" not in st.session_state:
        st.session_state.removed_steps = set()
    if "added_steps" not in st.session_state:
        st.session_state.added_steps = set()
    if "button_counter" not in st.session_state:
        st.session_state.button_counter = 0
    if "analysis_started" not in st.session_state:
        st.session_state.analysis_started = False
    if "current_step_index" not in st.session_state:
        st.session_state.current_step_index = 0
    if "cot_history" not in st.session_state:
        st.session_state.cot_history = []
    if "show_project_info" not in st.session_state:
        st.session_state.show_project_info = True

def render_project_info_section():
    """프로젝트 기본 정보 입력 섹션"""
    st.markdown("### 📋 프로젝트 기본 정보")
    
    # 접을 수 있는 섹션
    with st.expander("프로젝트 정보 입력", expanded=st.session_state.get('show_project_info', True)):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("프로젝트명", key="project_name", placeholder="프로젝트명을 입력하세요")
            st.text_input("건축주", key="owner", placeholder="건축주명을 입력하세요")
            st.text_input("대지위치", key="site_location", placeholder="대지 위치를 입력하세요")
            st.text_input("대지면적", key="site_area", placeholder="대지면적을 입력하세요")
        
        with col2:
            st.text_input("건물용도", key="building_type", placeholder="건물용도를 입력하세요")
            st.text_input("용적률", key="floor_area_ratio", placeholder="용적률을 입력하세요")
            st.text_input("건폐율", key="building_coverage_ratio", placeholder="건폐율을 입력하세요")
            st.text_input("프로젝트 목표", key="project_goal", placeholder="프로젝트 목표를 입력하세요")
        
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
            st.session_state["pdf_summary"] = pdf_summary
            st.session_state["site_fields"] = extract_site_analysis_fields(pdf_text)
            st.session_state["uploaded_pdf"] = uploaded_pdf
            st.success("✅ PDF 요약 완료!")
        
        # 정보 입력 완료 버튼
        if st.button("정보 입력 완료", type="primary"):
            st.session_state.show_project_info = False
            st.success("프로젝트 정보 입력이 완료되었습니다!")
            st.rerun()

def render_prompt_blocks_sidebar():
    """프롬프트 분석 단계 전체 리스트 사이드바"""
    st.sidebar.markdown("### 📋 전체 분석 단계")
    
    # 프롬프트 블록 로드
    from prompt_loader import load_prompt_blocks
    blocks = load_prompt_blocks()
    extra_blocks = blocks["extra"]
    
    # 현재 선택된 단계들
    current_step_ids = set()
    if st.session_state.get('workflow_steps'):
        current_step_ids = {step.id for step in st.session_state.workflow_steps}
    
    # 추천 단계들 (제외)
    recommended_step_ids = set()
    if st.session_state.get('current_workflow'):
        system = st.session_state.analysis_system
        for objective in st.session_state.get('selected_objectives', []):
            if objective in system.recommended_steps:
                recommended_step_ids.update({step.id for step in system.recommended_steps[objective]})
    
    st.sidebar.write("**선택 가능한 단계**:")
    
    for block in extra_blocks:
        block_id = block["id"]
        is_selected = block_id in current_step_ids
        is_recommended = block_id in recommended_step_ids
        
        # 추천 단계는 제외하고 표시
        if not is_recommended:
            # 선택된 단계는 회색으로 표시
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
                        order=len(st.session_state.workflow_steps) + 1,
                        category="추가 단계"
                    )
                    
                    if 'workflow_steps' not in st.session_state:
                        st.session_state.workflow_steps = []
                    
                    st.session_state.workflow_steps.append(new_step)
                    st.sidebar.success(f"'{block['title']}' 단계가 추가되었습니다!")
                    st.rerun()
    
    # 현재 선택된 단계들 표시
    if current_step_ids:
        st.sidebar.markdown("---")
        st.sidebar.write("**현재 선택된 단계**:")
        for step in st.session_state.get('workflow_steps', []):
            step_type = "🔴" if step.is_required else "🟡" if step.is_recommended else "🟢"
            st.sidebar.write(f"{step_type} {step.title}")

def render_purpose_selection():
    """용도 선택 UI"""
    st.subheader("### 1. 용도 선택")
    
    system = st.session_state.analysis_system
    available_purposes = list(system.purpose_objective_mapping.keys())
    
    st.write("프로젝트의 주요 용도를 선택하세요:")
    
    # 드롭다운으로 토글 느낌 구현
    purpose_options = [purpose.value for purpose in available_purposes]
    purpose_options.insert(0, "용도를 선택하세요")  # 기본 옵션 추가
    
    selected_purpose_value = st.selectbox(
        "용도 선택",
        options=purpose_options,
        key="purpose_selection",
        index=0
    )
    
    # 선택된 용도 찾기
    selected_purpose = None
    if selected_purpose_value and selected_purpose_value != "용도를 선택하세요":
        selected_purpose = next((p for p in available_purposes if p.value == selected_purpose_value), None)
        st.session_state.selected_purpose = selected_purpose
        
        # 용도가 변경되면 관련 상태 초기화
        if st.session_state.get('previous_purpose') != selected_purpose:
            st.session_state.selected_objectives = []
            st.session_state.workflow_suggested = False
            st.session_state.current_workflow = None
            st.session_state.workflow_steps = []
            st.session_state.removed_steps = set()
            st.session_state.added_steps = set()
            st.session_state.button_counter = 0
            st.session_state.previous_purpose = selected_purpose
    else:
        # 기본 옵션이 선택된 경우
        st.session_state.selected_purpose = None
        st.session_state.selected_objectives = []
        st.session_state.workflow_suggested = False
        st.session_state.current_workflow = None
        st.session_state.workflow_steps = []
        st.session_state.removed_steps = set()
        st.session_state.added_steps = set()
        st.session_state.button_counter = 0
    
    # 선택된 용도 표시
    if selected_purpose:
        st.success(f"**선택된 용도**: {selected_purpose.value}")
        return selected_purpose
    
    return None

def render_objective_selection(purpose: PurposeType):
    """목적 선택 UI"""
    st.subheader("### 2. 목적 선택")
    
    system = st.session_state.analysis_system
    available_objectives = system.get_available_objectives(purpose)
    
    if not available_objectives:
        st.warning("해당 용도에 대한 목적이 정의되지 않았습니다.")
        return []
    
    st.write("분석 목적을 선택하세요 (다중 선택 가능):")
    
    selected_objectives = []
    cols = st.columns(2)
    
    for i, objective in enumerate(available_objectives):
        col_idx = i % 2
        with cols[col_idx]:
            if st.checkbox(
                objective.value,
                key=f"objective_{objective.name}",
                help=get_objective_description(objective)
            ):
                selected_objectives.append(objective)
    
    st.session_state.selected_objectives = selected_objectives
    
    if selected_objectives:
        st.success(f"**선택된 목적**: {', '.join([obj.value for obj in selected_objectives])}")
    
    return selected_objectives

def get_objective_description(objective: ObjectiveType) -> str:
    """목적별 설명 반환"""
    descriptions = {
        ObjectiveType.MARKET_ANALYSIS: "시장 분석, 경쟁사 분석, 수요 분석 등",
        ObjectiveType.DESIGN_GUIDELINE: "디자인 가이드라인, 트렌드 분석 등",
        ObjectiveType.MASS_STRATEGY: "매스 전략, 건축 형태 분석 등",
        ObjectiveType.COST_ANALYSIS: "원가 분석, 경제성 분석 등",
        ObjectiveType.OPERATION_STRATEGY: "운영 전략, 관리 방안 등",
        ObjectiveType.BRANDING: "브랜딩, 정체성, 차별화 등",
        ObjectiveType.LEGAL_REVIEW: "법적 검토, 규제 분석 등",
        ObjectiveType.SPACE_PLANNING: "공간 계획, 면적 배분 등",
        ObjectiveType.CONCEPT_RESEARCH: "컨셉 개발, 아이디어 발굴 등",
        ObjectiveType.RISK_ANALYSIS: "리스크 분석, 위험요소 평가 등",
        ObjectiveType.OTHER: "기타 목적"
    }
    return descriptions.get(objective, "")

def render_workflow_suggestion(purpose: PurposeType, objectives: List[ObjectiveType]):
    """워크플로우 제안 UI"""
    st.subheader("### 3. 분석 단계 자동 제안")
    
    if not objectives:
        st.warning("목적을 선택해주세요.")
        return None
    
    system = st.session_state.analysis_system
    
    # 워크플로우 제안 버튼
    if st.button("분석 단계 자동 제안", type="primary", key="suggest_workflow"):
        workflow = system.suggest_analysis_steps(purpose, objectives)
        st.session_state.current_workflow = workflow
        st.session_state.workflow_steps = system.get_final_workflow(workflow)
        st.session_state.workflow_suggested = True
        st.session_state.removed_steps = set()
        st.session_state.added_steps = set()
        st.session_state.workflow_updated = True
        st.session_state.button_counter = 0
        
        st.success("분석 단계가 자동으로 제안되었습니다!")
        st.rerun()  # UI 업데이트를 위해 rerun 추가
        
        return workflow
    
    # 워크플로우가 이미 제안된 경우 표시
    if st.session_state.workflow_suggested and st.session_state.current_workflow:
        render_workflow_steps(st.session_state.current_workflow)
        return st.session_state.current_workflow
    
    return None

def render_workflow_steps(workflow: AnalysisWorkflow):
    """워크플로우 단계 표시"""
    system = st.session_state.analysis_system
    
    # 제거된 단계를 필터링한 워크플로우 생성
    filtered_steps = []
    for step in st.session_state.workflow_steps:
        if step.id not in st.session_state.removed_steps:
            filtered_steps.append(step)
    
    st.subheader("### 제안된 분석 단계")
    
    # 단계별로 표시
    for i, step in enumerate(filtered_steps):
        with st.expander(f"{i+1}. {step.title} ({step.category})", expanded=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**설명**: {step.description}")
                
                # 단계 유형 표시
                step_type = []
                if step.is_required:
                    step_type.append("🔴 필수")
                if step.is_recommended:
                    step_type.append("🟡 권장")
                if step.is_optional:
                    step_type.append("🟢 선택")
                
                st.write(f"**유형**: {' | '.join(step_type)}")
            
            with col2:
                if not step.is_required:
                    # 제거 버튼에 고유한 키 사용
                    remove_key = f"remove_{step.id}_{i}_{st.session_state.button_counter}"
                    if st.button("제거", key=remove_key):
                        st.session_state.removed_steps.add(step.id)
                        st.session_state.button_counter += 1
                        st.success(f"'{step.title}' 단계가 제거되었습니다!")
                        st.rerun()  # UI 업데이트를 위해 rerun 추가

def render_optional_steps_addition():
    """번외 단계 추가 UI"""
    st.subheader("### 4. 번외 단계 추가")
    
    system = st.session_state.analysis_system
    
    if not st.session_state.current_workflow:
        st.warning("먼저 분석 단계를 제안해주세요.")
        return
    
    # 현재 워크플로우에 없는 번외 단계만 표시
    current_step_ids = {step.id for step in st.session_state.workflow_steps}
    current_step_ids.update(st.session_state.added_steps)  # 이미 추가된 단계도 제외
    
    available_optional_steps = [
        step for step in system.optional_steps 
        if step.id not in current_step_ids
    ]
    
    if not available_optional_steps:
        st.info("추가할 수 있는 번외 단계가 없습니다.")
        return
    
    st.write("**추가 가능한 번외 단계**:")
    
    # 번외 단계들을 2열로 표시
    cols = st.columns(2)
    for i, step in enumerate(available_optional_steps):
        col_idx = i % 2
        with cols[col_idx]:
            with st.expander(f"➕ {step.title} ({step.category})"):
                st.write(f"**설명**: {step.description}")
                
                # 추가 버튼에 고유한 키 사용
                add_key = f"add_{step.id}_{i}_{st.session_state.button_counter}"
                if st.button("추가", key=add_key):
                    st.session_state.added_steps.add(step.id)
                    st.session_state.button_counter += 1
                    st.success(f"'{step.title}' 단계가 추가되었습니다!")
                    st.rerun()  # UI 업데이트를 위해 rerun 추가

def render_step_reordering():
    """단계 순서 변경 UI"""
    st.subheader("### 5. 단계 순서 변경")
    
    # 현재 표시되는 단계들 (순서 변경된 워크플로우 사용)
    current_steps = st.session_state.workflow_steps.copy()  # 직접 복사 사용
    
    if not current_steps:
        st.warning("순서를 변경할 단계가 없습니다.")
        return
    
    # 사용법 안내
    st.info("""
    **📋 순서 변경 방법**
    
    **왜 단계 순서가 중요한가요?**
    Chain of Thought (CoT) 방식으로 분석이 진행되기 때문입니다. 앞 단계의 분석 결과가 뒷 단계의 추론에 직접적으로 영향을 미치므로, 논리적 순서로 단계를 배치하는 것이 중요합니다.
    
    1. **현재 순서 번호**: 이동할 단계의 현재 위치 번호
    2. **이동할 순서 번호**: 이동할 위치의 번호
    3. **순서 변경** 버튼을 클릭하여 실행
    
    **사용 예시**:
    - 3번째 단계를 1번째로 이동: 현재 순서 번호에 3, 이동할 순서 번호에 1 입력
    """)
    
    st.write("**현재 순서**:")
    for i, step in enumerate(current_steps):
        step_type = "🔴" if step.is_required else "🟡" if step.is_recommended else "🟢"
        st.write(f"{i+1}. {step_type} **{step.title}** ({step.category})")
    
    if len(current_steps) > 1:
        st.write("**순서 변경**:")
        col1, col2, col3 = st.columns(3)
        with col1:
            current_idx = st.number_input("현재 순서 번호", min_value=1, max_value=len(current_steps), value=1, help="이동할 단계의 현재 순서 번호를 입력하세요")
        with col2:
            target_idx = st.number_input("이동할 순서 번호", min_value=1, max_value=len(current_steps), value=1, help="이동할 위치의 순서 번호를 입력하세요")
        with col3:
            st.write("")
            st.write("")
            if st.button("순서 변경", key="change_order"):
                if current_idx != target_idx:
                    # 새로운 리스트 생성
                    steps_copy = current_steps.copy()
                    step_to_move = steps_copy.pop(current_idx - 1)
                    steps_copy.insert(target_idx - 1, step_to_move)
                    
                    # session_state 업데이트
                    st.session_state.workflow_steps = steps_copy
                    st.session_state.button_counter += 1
                    st.success(f"단계 {current_idx}를 {target_idx}번째 위치로 이동했습니다!")
                    st.rerun()  # UI 즉시 업데이트
                else:
                    st.warning("현재 순서와 이동할 순서가 같습니다.")
        
        st.write("")
        st.write("**💡 팁**:")
        st.write("- 필수 단계(🔴)는 제거할 수 없지만 순서는 변경 가능합니다.")
        st.write("- 권장 단계(🟡)와 선택 단계(🟢)는 제거와 순서 변경 모두 가능합니다.")
        st.write("- 순서 변경 후에는 분석 실행 시 새로운 순서로 진행됩니다.")
    else:
        st.info("순서 변경을 위해서는 2개 이상의 단계가 필요합니다.")

def render_workflow_confirmation():
    """워크플로우 확정 UI"""
    st.subheader("### 6. 분석 실행")
    
    # 현재 워크플로우 단계들 (순서 변경된 상태 그대로 사용)
    current_steps = st.session_state.workflow_steps.copy()
    
    if not current_steps:
        st.warning("분석 단계가 없습니다.")
        return
    
    # 최종 워크플로우 요약
    st.write("**최종 분석 워크플로우**:")
    
    total_steps = len(current_steps)
    required_steps = len([s for s in current_steps if s.is_required])
    optional_steps = total_steps - required_steps
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 단계 수", total_steps)
    with col2:
        st.metric("필수 단계", required_steps)
    with col3:
        st.metric("선택 단계", optional_steps)

    
    # 분석 실행 버튼
    if st.button("분석 실행", type="primary", key="execute_analysis"):
        st.session_state.analysis_started = True
        st.session_state.current_step_index = 0
        st.session_state.cot_history = []
        st.success("분석이 시작되었습니다! '시작' 명령어를 입력하세요.")
        st.rerun()

def render_analysis_execution():
    """분석 실행 UI - 기존 방식과 동일하게"""
    if not st.session_state.get('analysis_started', False):
        return
    
    st.subheader("###  분석 실행")
    
    # 현재 표시되는 단계들을 ordered_blocks 형태로 변환
    current_steps = []
    for step in st.session_state.workflow_steps:
        if step.id not in st.session_state.removed_steps:
            current_steps.append(step)
    
    # 추가된 단계들도 포함
    system = st.session_state.analysis_system
    for step_id in st.session_state.added_steps:
        optional_step = next((step for step in system.optional_steps if step.id == step_id), None)
        if optional_step:
            current_steps.append(optional_step)
    
    if not current_steps:
        st.warning("분석할 단계가 없습니다.")
        return
    
    # 프롬프트 블록에서 해당 단계들 찾기
    from prompt_loader import load_prompt_blocks
    blocks = load_prompt_blocks()
    extra_blocks = blocks["extra"]
    blocks_by_id = {b["id"]: b for b in extra_blocks}
    
    # ordered_blocks 생성
    ordered_blocks = []
    for step in current_steps:
        if step.id in blocks_by_id:
            ordered_blocks.append(blocks_by_id[step.id])
    
    # session_state에 저장 (기존 시스템과 연동)
    st.session_state.ordered_blocks = ordered_blocks
    
    # 진행 상황 표시
    current_step_index = st.session_state.get('current_step_index', 0)
    progress_text = f"진행 상황: {current_step_index + 1}/{len(ordered_blocks)}"
    st.write(f"**{progress_text}**")
    
    # 현재 단계 표시
    if current_step_index < len(ordered_blocks):
        current_block = ordered_blocks[current_step_index]
        
        st.write("**현재 단계**:")
        st.write(f" **{current_block['title']}**")
        st.write(f"**설명**: {current_block.get('description', '설명 없음')}")
        
        # 기존 방식과 동일한 명령어 입력
        cmd = st.text_input("▶ 명령어 입력 (예: 시작 / 분석 진행 / N단계 진행 / 보고서 생성)", 
                           key=f"cmd_input_{current_step_index}")
        
        if cmd.strip() == "시작":
            st.session_state.current_step_index = 0
            st.session_state.cot_history = []
            st.success("모든 입력이 완료되었습니다. '분석 진행'을 입력하세요.")
            st.rerun()
        
        elif cmd.strip() == "분석 진행" or cmd.strip().endswith("단계 진행"):
            # 기존 app.py의 분석 로직 실행
            execute_analysis_step(current_block, current_step_index, cmd)
    
    else:
        # 모든 단계 완료
        st.success("🎉 모든 분석 단계가 완료되었습니다!")
        
        # 최종 결과 요약
        if st.session_state.get('cot_history'):
            st.write("**📋 최종 분석 결과 요약**:")
            for i, entry in enumerate(st.session_state.cot_history):
                st.write(f"{i+1}. **{entry['step']}**: {entry.get('summary', '')[:100]}...")
        
        # 결과 내보내기 버튼
        if st.button("결과 내보내기", key="export_results"):
            export_analysis_results()
        
        # 새로운 분석 시작 버튼
        if st.button("새로운 분석 시작", key="new_analysis"):
            st.session_state.analysis_started = False
            st.session_state.current_step_index = 0
            st.session_state.cot_history = []
            st.rerun()

def execute_analysis_step(current_block, step_index, cmd):
    """기존 app.py의 분석 로직 실행"""
    from user_state import get_user_inputs, get_pdf_summary
    from agent_executor import (
        run_requirement_table, run_ai_reasoning, 
        run_precedent_comparison, run_strategy_recommendation
    )
    from dsl_to_prompt import convert_dsl_to_prompt
    import time
    
    # 사용자 입력 가져오기
    user_inputs = get_user_inputs()
    pdf_summary = get_pdf_summary()
    
    # PDF 업로드 상태 확인
    if not st.session_state.get('uploaded_pdf'):
        st.error("❌ PDF를 먼저 업로드해주세요!")
        return
    
    # 필수 입력값 검증
    required_fields = ["project_name", "owner", "site_location", "site_area", "building_type", "project_goal"]
    missing_fields = [field for field in required_fields if not user_inputs.get(field, "").strip()]
    
    if missing_fields:
        st.error(f"❌ 다음 필수 정보를 입력해주세요: {', '.join(missing_fields)}")
        return
    
    # PDF 처리 상태 확인
    if not pdf_summary:
        st.error("❌ PDF 처리가 완료되지 않았습니다. PDF를 다시 업로드해주세요.")
        return
    
    # 실행할 단계 번호 결정
    if cmd.strip() == "분석 진행":
        idx = step_index
    else:
        try:
            idx = int(cmd.strip().replace("단계 진행", "")) - 1
        except ValueError:
            st.error("'N단계 진행' 형식으로 입력해주세요.")
            return
    
    # 유효성 검사
    if idx != step_index:
        st.error(f"현재 단계({step_index + 1})와 요청한 단계({idx + 1})가 일치하지 않습니다.")
        return
    
    blk = current_block
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
                            from dsl_to_prompt import prompt_requirement_table
                            prompt = prompt_requirement_table(blk["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                            results[f"result_{i}"] = run_requirement_table(prompt)
                            time.sleep(5)  # 5초 대기
                        elif i == 1:
                            from dsl_to_prompt import prompt_ai_reasoning
                            prompt = prompt_ai_reasoning(blk["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                            results[f"result_{i}"] = run_ai_reasoning(prompt)
                            time.sleep(5)  # 5초 대기
                        elif i == 2:
                            from dsl_to_prompt import prompt_precedent_comparison
                            prompt = prompt_precedent_comparison(blk["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                            results[f"result_{i}"] = run_precedent_comparison(prompt)
                            time.sleep(5)  # 5초 대기
                        elif i == 3:
                            from dsl_to_prompt import prompt_strategy_recommendation
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
                        st.markdown(results.get("requirement_table", "분석 결과가 없습니다."))
                    with tab2:
                        st.markdown(results.get("ai_reasoning", "분석 결과가 없습니다."))
                    with tab3:
                        st.markdown(results.get("precedent_comparison", "분석 결과가 없습니다."))
                    with tab4:
                        st.markdown(results.get("strategy_recommendation", "분석 결과가 없습니다."))
                
                # 다음 단계로 이동
                st.session_state.current_step_index += 1
                st.success(f"'{blk['title']}' 단계가 완료되었습니다! 다음 단계로 진행하세요.")
                st.rerun()

def export_analysis_results():
    """분석 결과 내보내기"""
    if not st.session_state.get('cot_history'):
        st.warning("내보낼 결과가 없습니다.")
        return
    
    # JSON 형태로 결과 내보내기
    import json
    from datetime import datetime
    
    export_data = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'workflow': st.session_state.current_workflow.__dict__ if st.session_state.current_workflow else None,
        'results': st.session_state.cot_history
    }
    
    st.download_button(
        label="📥 분석 결과 다운로드 (JSON)",
        data=json.dumps(export_data, indent=2, ensure_ascii=False),
        file_name=f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

def render_legacy_analysis_system():
    """기존 분석 방식 렌더링"""
    # 기존 app.py의 분석 방식 로직
    from prompt_loader import load_prompt_blocks
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
        
        from streamlit_sortables import sort_items
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

def main():
    """메인 UI"""
    st.title("🏗️ ArchInsight 분석 시스템")
    st.write("프로젝트 용도와 목적에 따른 맞춤형 분석 워크플로우를 구성하세요.")
    
    # 시스템 초기화
    init_analysis_system()
    
    # 1. 프로젝트 기본 정보 입력 (탭 위에 배치)
    render_project_info_section()
    
    # 2. 프롬프트 분석 단계 사이드바
    render_prompt_blocks_sidebar()
    
    # 3. 탭으로 기존 방식과 새로운 방식 선택
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
                
                if workflow or st.session_state.workflow_suggested:
                    # 4. 번외 단계 추가
                    render_optional_steps_addition()
                    
                    # 5. 순서 변경
                    render_step_reordering()
                    
                    # 6. 분석 실행
                    render_workflow_confirmation()
                    
                    # 7. 분석 실행 중 (분석이 시작된 경우)
                    render_analysis_execution()
    
    with tab2:
        st.markdown("### 📋 기존 분석 방식")
        # 기존 분석 방식 로직 (app.py에서 가져옴)
        render_legacy_analysis_system()
    
    # 사이드바에 도움말
    with st.sidebar:
        st.markdown("---")
        st.header("💡 도움말")
        st.write("""
        1. **프로젝트 정보**: 상단에서 기본 정보를 입력하세요
        2. **용도 선택**: 프로젝트의 주요 용도를 선택하세요
        3. **목적 선택**: 분석하고자 하는 목적을 선택하세요
        4. **자동 제안**: 시스템이 적절한 분석 단계를 자동으로 제안합니다
        5. **추가 단계**: 사이드바에서 원하는 단계를 추가할 수 있습니다
        6. **순서 변경**: 단계의 순서를 조정할 수 있습니다
        7. **분석 실행**: 최종 워크플로우로 분석을 실행합니다
        """)

if __name__ == "__main__":
    main() 