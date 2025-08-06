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
    if 'analysis_system' not in st.session_state:
        st.session_state.analysis_system = AnalysisSystem()
    if 'current_workflow' not in st.session_state:
        st.session_state.current_workflow = None
    if 'selected_purpose' not in st.session_state:
        st.session_state.selected_purpose = None
    if 'selected_objectives' not in st.session_state:
        st.session_state.selected_objectives = []
    if 'workflow_steps' not in st.session_state:
        st.session_state.workflow_steps = []

def render_purpose_selection():
    """용도 선택 UI"""
    st.subheader("### 1. 용도 선택")
    
    purposes = list(PurposeType)
    purpose_names = [p.value for p in purposes]
    
    selected_purpose_idx = st.selectbox(
        "프로젝트 용도를 선택하세요:",
        range(len(purposes)),
        format_func=lambda x: purpose_names[x],
        key="purpose_select"
    )
    
    selected_purpose = purposes[selected_purpose_idx]
    st.session_state.selected_purpose = selected_purpose
    
    # 용도 설명
    purpose_descriptions = {
        PurposeType.OFFICE: "사무실, 업무공간, 코워킹스페이스 등",
        PurposeType.RESIDENTIAL: "주택, 아파트, 호텔, 숙박시설 등",
        PurposeType.COMMERCIAL: "상업시설, 쇼핑몰, 레스토랑 등",
        PurposeType.CULTURAL: "문화시설, 박물관, 갤러리, 공연장 등",
        PurposeType.EDUCATIONAL: "학교, 교육시설, 도서관 등",
        PurposeType.MEDICAL: "병원, 의료시설, 약국 등",
        PurposeType.INDUSTRIAL: "공장, 창고, 물류시설 등",
        PurposeType.MIXED_USE: "복합용도 건물, 상업+주거 등",
        PurposeType.OTHER: "기타 용도"
    }
    
    st.info(f"**선택된 용도**: {selected_purpose.value}\n\n{purpose_descriptions.get(selected_purpose, '')}")
    
    return selected_purpose

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
    
    if st.button("분석 단계 자동 제안", type="primary"):
        workflow = system.suggest_analysis_steps(purpose, objectives)
        st.session_state.current_workflow = workflow
        st.session_state.workflow_steps = system.get_final_workflow(workflow)
        
        st.success("분석 단계가 자동으로 제안되었습니다!")
        
        # 제안된 단계 표시
        render_workflow_steps(workflow)
        
        return workflow
    
    return None

def render_workflow_steps(workflow: AnalysisWorkflow):
    """워크플로우 단계 표시"""
    system = st.session_state.analysis_system
    all_steps = system.get_final_workflow(workflow)
    
    st.subheader("### 제안된 분석 단계")
    
    # 단계별로 표시
    for i, step in enumerate(all_steps):
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
                    if st.button("제거", key=f"remove_{step.id}"):
                        workflow = system.remove_step(workflow, step.id)
                        st.session_state.current_workflow = workflow
                        st.session_state.workflow_steps = system.get_final_workflow(workflow)
                        st.rerun()

def render_optional_steps_addition():
    """번외 단계 추가 UI"""
    st.subheader("### 4. 번외 단계 추가")
    
    system = st.session_state.analysis_system
    
    if not st.session_state.current_workflow:
        st.warning("먼저 분석 단계를 제안해주세요.")
        return
    
    # 현재 워크플로우에 없는 번외 단계만 표시
    current_step_ids = {step.id for step in st.session_state.workflow_steps}
    available_optional_steps = [
        step for step in system.optional_steps 
        if step.id not in current_step_ids
    ]
    
    if not available_optional_steps:
        st.info("추가할 수 있는 번외 단계가 없습니다.")
        return
    
    st.write("추가할 번외 단계를 선택하세요:")
    
    for step in available_optional_steps:
        with st.expander(f"➕ {step.title} ({step.category})"):
            st.write(f"**설명**: {step.description}")
            
            if st.button("추가", key=f"add_{step.id}"):
                workflow = st.session_state.current_workflow
                workflow = system.add_optional_step(workflow, step.id)
                st.session_state.current_workflow = workflow
                st.session_state.workflow_steps = system.get_final_workflow(workflow)
                st.success(f"'{step.title}' 단계가 추가되었습니다!")
                st.rerun()

def render_step_reordering():
    """단계 순서 변경 UI"""
    st.subheader("### 5. 단계 순서 변경")
    
    if not st.session_state.workflow_steps:
        st.warning("분석 단계가 없습니다.")
        return
    
    system = st.session_state.analysis_system
    
    # 드래그 앤 드롭으로 순서 변경
    st.write("단계를 드래그하여 순서를 변경하세요:")
    
    step_items = []
    for step in st.session_state.workflow_steps:
        step_type = "🔴" if step.is_required else "🟡" if step.is_recommended else "🟢"
        step_items.append(f"{step_type} {step.title}")
    
    # 간단한 순서 변경 UI (실제 드래그 앤 드롭은 복잡하므로 체크박스로 대체)
    st.write("**현재 순서**:")
    for i, step in enumerate(st.session_state.workflow_steps):
        step_type = "🔴" if step.is_required else "🟡" if step.is_recommended else "🟢"
        st.write(f"{i+1}. {step_type} {step.title} ({step.category})")
    
    # 순서 변경 버튼 (실제로는 더 복잡한 UI가 필요)
    if st.button("순서 변경 모드"):
        st.info("순서 변경 기능은 향후 드래그 앤 드롭으로 구현 예정입니다.")

def render_workflow_confirmation():
    """워크플로우 확정 UI"""
    st.subheader("### 6. 분석 실행")
    
    if not st.session_state.workflow_steps:
        st.warning("분석 단계가 없습니다.")
        return
    
    system = st.session_state.analysis_system
    workflow = st.session_state.current_workflow
    
    # 최종 워크플로우 요약
    st.write("**최종 분석 워크플로우**:")
    
    total_steps = len(st.session_state.workflow_steps)
    required_steps = len([s for s in st.session_state.workflow_steps if s.is_required])
    optional_steps = total_steps - required_steps
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 단계 수", total_steps)
    with col2:
        st.metric("필수 단계", required_steps)
    with col3:
        st.metric("선택 단계", optional_steps)
    
    # 워크플로우 설정 내보내기
    if workflow:
        config = system.export_workflow_config(workflow)
        
        st.write("**워크플로우 설정**:")
        st.json(config)
        
        # 분석 실행 버튼
        if st.button("분석 실행", type="primary", key="execute_analysis"):
            st.success("분석이 시작되었습니다!")
            
            # 실제 분석 실행 로직은 여기에 구현
            execute_analysis_workflow(workflow)

def execute_analysis_workflow(workflow: AnalysisWorkflow):
    """실제 분석 실행"""
    st.write("### 분석 실행 중...")
    
    # 각 단계별 분석 실행
    for i, step in enumerate(st.session_state.workflow_steps):
        with st.spinner(f"단계 {i+1}/{len(st.session_state.workflow_steps)}: {step.title}"):
            # 실제 분석 로직 구현
            st.write(f"**{step.title}** 분석 완료")
            st.write(f"설명: {step.description}")
            
            # 임시 결과 (실제로는 각 단계별 분석 결과)
            st.info(f"단계 {i+1} 분석 결과가 생성되었습니다.")
    
    st.success("모든 분석이 완료되었습니다!")

def main():
    """메인 UI"""
    st.title("🏗️ ArchInsight 분석 시스템")
    st.write("프로젝트 용도와 목적에 따른 맞춤형 분석 워크플로우를 구성하세요.")
    
    # 시스템 초기화
    init_analysis_system()
    
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
    
    # 사이드바에 도움말
    with st.sidebar:
        st.header("💡 도움말")
        st.write("""
        1. **용도 선택**: 프로젝트의 주요 용도를 선택하세요
        2. **목적 선택**: 분석하고자 하는 목적을 선택하세요 (다중 선택 가능)
        3. **자동 제안**: 시스템이 적절한 분석 단계를 자동으로 제안합니다
        4. **번외 추가**: 필요한 경우 추가 단계를 선택할 수 있습니다
        5. **순서 변경**: 단계의 순서를 조정할 수 있습니다
        6. **분석 실행**: 최종 워크플로우로 분석을 실행합니다
        """)

if __name__ == "__main__":
    main() 