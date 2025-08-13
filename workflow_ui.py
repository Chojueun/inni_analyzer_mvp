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
import re
import time
import os
from datetime import datetime
from agent_executor import execute_agent
from user_state import get_user_inputs, save_step_result, append_step_history
from report_generator import generate_pdf_report, generate_word_report
from webpage_generator import create_webpage_download_button
from prompt_loader import load_prompt_blocks
from analysis_system import (
    AnalysisSystem, PurposeType, ObjectiveType, AnalysisStep, AnalysisWorkflow
)
from agent_executor import (
    run_requirement_table,
    run_ai_reasoning,
    run_precedent_comparison,
    run_strategy_recommendation,
)
from utils import extract_summary, extract_insight
from utils_pdf import (
    initialize_vector_system,
    extract_text_from_pdf,
    save_pdf_chunks_to_chroma,
    search_pdf_chunks,
    get_pdf_summary,
    get_pdf_summary_from_session
)
from dsl_to_prompt import convert_dsl_to_prompt

# 파일 상단에 상수 정의
REQUIRED_FIELDS = ["project_name", "building_type", "site_location", "owner", "site_area", "project_goal"]
FEEDBACK_TYPES = ["추가 분석 요청", "수정 요청", "다른 관점 제시", "구조 변경", "기타"]

def execute_claude_analysis(prompt, description):
    """Claude 분석 실행 함수 - 세션 상태 기반 모델 선택"""
    
    # 세션 상태에서 선택된 모델 가져오기
    selected_model = st.session_state.get('selected_model', 'claude-3-5-sonnet-20241022')
    
    # SDK 방식으로 실행 (DSPy 설정 변경 없이)
    from init_dspy import execute_with_sdk
    result = execute_with_sdk(prompt, selected_model)
    
    return result

def create_analysis_workflow(purpose_enum, objective_enums):
    """워크플로우 생성 함수"""
    system = AnalysisSystem()
    return system.suggest_analysis_steps(purpose_enum, objective_enums)

def validate_user_inputs(user_inputs):
    """사용자 입력 검증 함수"""
    missing_fields = [field for field in REQUIRED_FIELDS if not user_inputs.get(field)]
    return missing_fields

def create_pdf_summary_dict(user_inputs, pdf_summary):
    """PDF 요약 딕셔너리 생성 함수"""
    return {
        "pdf_summary": pdf_summary,
        "project_name": user_inputs.get("project_name", ""),
        "owner": user_inputs.get("owner", ""),
        "site_location": user_inputs.get("site_location", ""),
        "site_area": user_inputs.get("site_area", ""),
        "building_type": user_inputs.get("building_type", ""),
        "project_goal": user_inputs.get("project_goal", "")
    }

def render_purpose_selection():
    """1단계: 용도 선택"""
    st.subheader("🏗️ 1단계: 건물 용도 선택")
    
    purpose_options = [purpose.value for purpose in PurposeType]
    selected_purpose = st.selectbox(
        "건물 용도를 선택하세요",
        purpose_options,
        key="selected_purpose"
    )
    
    if selected_purpose:
        return PurposeType(selected_purpose)
    return None

def render_objective_selection(purpose: PurposeType, system: AnalysisSystem):
    """2단계: 목적 선택"""
    st.subheader("🎯 2단계: 분석 목적 선택")
    
    available_objectives = system.get_available_objectives(purpose)
    objective_options = [obj.value for obj in available_objectives]
    
    selected_objectives = st.multiselect(
        "분석 목적을 선택하세요 (복수 선택 가능)",
        objective_options,
        key="selected_objectives"
    )
    
    if selected_objectives:
        return [ObjectiveType(obj) for obj in selected_objectives]
    return []

def render_analysis_steps_management(selected_purpose, selected_objectives, system):
    """3단계: 분석 단계 관리"""
    st.subheader("📋 3단계: 분석 단계 관리")
    
    # 워크플로우 생성 - suggest_analysis_steps 사용
    workflow = system.suggest_analysis_steps(selected_purpose, selected_objectives)
    
    # 제거된 단계들을 필터링
    removed_steps = st.session_state.get('removed_steps', set())
    workflow.steps = [step for step in workflow.steps if step.id not in removed_steps]
    workflow.custom_steps = [step for step in workflow.custom_steps if step.id not in removed_steps]
    
    # 최종 워크플로우 가져오기
    final_steps = system.get_final_workflow(workflow)
    
    st.markdown("### 현재 분석 단계들:")
    
    # 모든 단계를 하나의 리스트로 통합
    all_steps = final_steps.copy()
    
    for i, step in enumerate(all_steps):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            if step.is_required:
                st.markdown(f" **{step.title}** (필수)")
            elif step.is_recommended:
                st.markdown(f" **{step.title}** (권장)")
            else:
                st.markdown(f" **{step.title}** (선택)")
            st.markdown(f"*{step.description}*")
        
        with col2:
            # 제거 버튼
            if not step.is_required:
                if st.button("❌ 제거", key=f"remove_{step.id}_{i}", use_container_width=True):
                    # 제거된 단계 세트에 추가
                    if 'removed_steps' not in st.session_state:
                        st.session_state.removed_steps = set()
                    st.session_state.removed_steps.add(step.id)
                    st.success(f"'{step.title}' 단계가 제거되었습니다!")
                    st.rerun()
            else:
                st.markdown("❌ 제거")
        
        with col3:
            # 위로 이동 버튼
            if i > 0:
                if st.button("⬆️ 위로", key=f"up_{step.id}_{i}", use_container_width=True):
                    # 현재 단계와 위 단계의 순서를 바꿈
                    all_steps[i], all_steps[i-1] = all_steps[i-1], all_steps[i]
                    
                    # 순서 번호 업데이트
                    for j, s in enumerate(all_steps):
                        s.order = (j + 1) * 10
                    
                    # 워크플로우 업데이트
                    workflow.steps = [s for s in all_steps if s.is_required or s.is_recommended]
                    workflow.custom_steps = [s for s in all_steps if s.is_optional]
                    
                    # 세션 상태에 저장
                    st.session_state.workflow_steps = all_steps
                    st.session_state.current_workflow = workflow
                    
                    st.success(f"'{step.title}' 단계가 위로 이동되었습니다!")
                    st.rerun()
            else:
                st.markdown("⬆️ 위로")
        
        with col4:
            # 아래로 이동 버튼
            if i < len(all_steps) - 1:
                if st.button("⬇️ 아래로", key=f"down_{step.id}_{i}", use_container_width=True):
                    # 현재 단계와 아래 단계의 순서를 바꿈
                    all_steps[i], all_steps[i+1] = all_steps[i+1], all_steps[i]
                    
                    # 순서 번호 업데이트
                    for j, s in enumerate(all_steps):
                        s.order = (j + 1) * 10
                    
                    # 워크플로우 업데이트
                    workflow.steps = [s for s in all_steps if s.is_required or s.is_recommended]
                    workflow.custom_steps = [s for s in all_steps if s.is_optional]
                    
                    # 세션 상태에 저장
                    st.session_state.workflow_steps = all_steps
                    st.session_state.current_workflow = workflow
                    
                    st.success(f"'{step.title}' 단계가 아래로 이동되었습니다!")
                    st.rerun()
            else:
                st.markdown("⬇️ 아래로")
        
        with col5:
            st.markdown(f"**순서:** {step.order}")
    
    # 순서 재정렬 버튼
    if st.button("🔄 전체 순서 재정렬", key="reorder_all", use_container_width=True):
        # 모든 단계를 10단위로 재정렬
        for i, step in enumerate(all_steps):
            step.order = (i + 1) * 10
        
        # 워크플로우 업데이트
        workflow.steps = [s for s in all_steps if s.is_required or s.is_recommended]
        workflow.custom_steps = [s for s in all_steps if s.is_optional]
        
        # 세션 상태에 저장
        st.session_state.workflow_steps = all_steps
        st.session_state.current_workflow = workflow
        
        st.success("순서가 재정렬되었습니다!")
        st.rerun()
    
    # 워크플로우를 세션 상태에 저장
    st.session_state.workflow_steps = all_steps
    st.session_state.current_workflow = workflow
    
    return workflow

def render_workflow_summary(workflow: AnalysisWorkflow, system: AnalysisSystem):
    """4단계: 워크플로우 요약"""
    st.subheader("📊 4단계: 최종 분석 워크플로우")
    
    st.markdown(f"**선택된 용도:** {workflow.purpose.value}")
    st.markdown(f"**선택된 목적:** {workflow.objective.value}")
    
    st.markdown("### 최종 분석 단계들:")
    
    final_steps = system.get_final_workflow(workflow)
    
    # 각 단계별 웹 검색 설정을 저장할 딕셔너리 초기화
    if 'web_search_settings' not in st.session_state:
        st.session_state.web_search_settings = {}
    
    for i, step in enumerate(final_steps, 1):
        if step.is_required:
            level_icon = "��"
            level_text = "필수"
        elif step.is_recommended:
            level_icon = "��"
            level_text = "권장"
        else:
            level_icon = "��"
            level_text = "선택"
        
        # 각 단계별 웹 검색 체크박스
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"{i}. {level_icon} **{step.title}** ({level_text})")
            st.markdown(f"   - {step.description}")
        
        with col2:
            # 웹 검색 체크박스 (기본값: False)
            web_search_key = f"web_search_{step.id}"
            if web_search_key not in st.session_state.web_search_settings:
                st.session_state.web_search_settings[web_search_key] = False
            
            st.session_state.web_search_settings[web_search_key] = st.checkbox(
                "웹 검색",
                value=st.session_state.web_search_settings[web_search_key],
                key=web_search_key
            )
    
    # 분석 실행 버튼을 여기서 직접 처리
    if st.button("🚀 분석 실행", type="primary", use_container_width=True, key="execute_analysis"):
        # 분석 상태 설정
        st.session_state.analysis_started = True
        st.session_state.current_step_index = 0
        st.session_state.cot_history = []
        st.session_state.workflow_steps = final_steps
        st.session_state.show_feedback = False
        
        st.success("✅ 분석이 시작되었습니다! 각 단계를 수동으로 진행하세요.")
        st.rerun()
    
    return False  # 버튼 반환 대신 False 반환

def validate_prompt_structure(dsl_block: dict) -> bool:
    """DSL 블록의 구조 유효성 검증"""
    content_dsl = dsl_block.get("content_dsl", {})
    output_structure = content_dsl.get("output_structure", [])
    
    if not output_structure:
        st.warning("⚠️ 이 블록에는 output_structure가 정의되지 않았습니다.")
        return False
    
    if len(output_structure) < 1:
        st.warning("⚠️ output_structure가 비어있습니다.")
        return False
    
    return True

def debug_analysis_result(result: str, output_structure: list):
    """분석 결과 디버깅 정보 표시"""
    with st.expander("🔍 디버깅 정보", expanded=False):
        st.markdown("**Output Structure:**")
        for i, structure in enumerate(output_structure, 1):
            st.markdown(f"{i}. {structure}")
        
        st.markdown("**AI 응답 길이:**")
        st.markdown(f"{len(result)} 문자")
        
        st.markdown("**구조명 매칭 결과:**")
        for structure in output_structure:
            found = structure in result
            st.markdown(f"- {structure}: {'✅' if found else '❌'}")
        
        st.markdown("**전체 응답 미리보기:**")
        st.code(result[:500] + "..." if len(result) > 500 else result)

def render_analysis_execution():
    """분석 실행 UI - 단계별 진행 방식"""
    if not st.session_state.get('analysis_started', False):
        return

    st.title("🏗️ 건축 분석 워크플로우")
    st.subheader("### 분석 실행")

    # cot_history 디버깅 정보 추가
    st.sidebar.markdown("### 🔍 분석 실행 디버깅")
    if st.session_state.get('cot_history'):
        st.sidebar.write(f"**완료된 분석: {len(st.session_state.cot_history)}개**")
        for i, history in enumerate(st.session_state.cot_history):
            step_name = history.get('step', f'단계 {i+1}')
            result_length = len(history.get('result', ''))
            st.sidebar.write(f"**{i+1}. {step_name}**")
            st.sidebar.write(f"   길이: {result_length} 문자")
            if result_length > 0:
                preview = history.get('result', '')[:30] + "..." if result_length > 30 else history.get('result', '')
                st.sidebar.write(f"   미리보기: {preview}")
    else:
        st.sidebar.write("**완료된 분석: 없음**")

    # 간단 검색 시스템 초기화
    try:
        from utils_pdf import initialize_vector_system
        initialize_vector_system()
    except Exception as e:
        st.warning(f"⚠️ 검색 시스템 초기화 실패: {e}")
        st.info("ℹ️ 기본 검색 모드로 진행합니다.")

    # 1) 실행 대상 단계 목록 구성
    current_steps = st.session_state.get('workflow_steps', [])
    
    if not current_steps:
        st.warning("분석할 단계가 없습니다.")
        return

    # 2) prompt_loader에서 해당 단계들 매칭
    try:
        # 프롬프트 블록 로드
        from prompt_loader import load_prompt_blocks
        blocks = load_prompt_blocks()
        extra_blocks = blocks.get("extra", [])
        blocks_by_id = {b["id"]: b for b in extra_blocks}

        # ordered_blocks 대신 workflow_steps 사용
        st.session_state.ordered_blocks = current_steps
        
    except Exception as e:
        st.error(f"❌ 프롬프트 블록 로드 실패: {e}")
        return

    # 3) 진행 표시
    current_step_index = st.session_state.get('current_step_index', 0)
    total_steps = len(current_steps)

    if total_steps == 0:
        st.warning("⚠️ 실행할 분석 단계가 없습니다.")
        return

    progress_percentage = ((current_step_index + 1) / total_steps) * 100
    st.progress(progress_percentage / 100)
    st.write(f"**진행 상황**: {current_step_index + 1} / {total_steps}")

    # 4) 현재 단계 표시 및 실행
    if current_step_index < len(current_steps):
        current_step = current_steps[current_step_index]
        
        # 현재 단계에 해당하는 블록 찾기
        current_block = None
        if current_step.id in blocks_by_id:
            current_block = blocks_by_id[current_step.id]
        
        st.markdown(f"### 🔍 현재 단계: {current_step.title}")
        st.markdown(f"**설명**: {current_step.description}")
        
        # 현재 단계의 분석 상태 확인
        step_completed = any(h['step'] == current_step.title for h in st.session_state.get('cot_history', []))
        
        # 분석 실행 버튼 (항상 표시)
        if current_block:
            button_text = f"🚀 {current_block['title']} 분석 실행"
        else:
            button_text = f"🚀 {current_step.title} 분석 실행"
        
        if st.button(button_text, type="primary", key=f"analyze_{current_step.id}_{current_step_index}"):
            try:
                # current_block이 None인 경우 처리
                if not current_block:
                    st.error(f"❌ '{current_step.title}' 단계에 해당하는 블록을 찾을 수 없습니다.")
                    st.error(f"단계 ID: {current_step.id}")
                    st.error("사용 가능한 블록들:")
                    for block in extra_blocks:
                        st.error(f"- {block['id']}: {block['title']}")
                    return
                
                # PDF 요약 정보 가져오기
                pdf_summary = get_pdf_summary()
                if not pdf_summary:
                    st.error("❌ PDF 요약 정보가 없습니다. PDF를 다시 업로드해주세요.")
                    return
                
                # 사용자 입력 정보 가져오기
                user_inputs = get_user_inputs()
                
                # 분석 실행 부분에 디버깅 정보 추가
                with st.spinner(f"{current_block['title']} 분석 중..."):
                    # DSL을 프롬프트로 변환
                    from dsl_to_prompt import convert_dsl_to_prompt
                    
                    # 이전 분석 결과들 가져오기
                    previous_results = ""
                    if st.session_state.get('cot_history'):
                        previous_results = "\n\n".join([f"**{h['step']}**: {h['result']}" for h in st.session_state.cot_history])
                    
                    # 프롬프트 생성
                    prompt = convert_dsl_to_prompt(
                        dsl_block=current_block,
                        user_inputs=user_inputs,
                        previous_summary=previous_results,
                        pdf_summary=pdf_summary,
                        site_fields=st.session_state.get('site_fields', {}),
                        include_web_search=False
                    )
                    
                    # Claude 분석 실행
                    result = execute_claude_analysis(prompt, current_block['title'])
                    
                    if result and result != f"{current_block['title']} 분석 실패":
                        # 결과 저장
                        save_step_result(current_step.id, result)
                        append_step_history(current_step.id, current_block['title'], prompt, result)
                        
                        # cot_history에도 추가 (기존 호환성 유지)
                        if 'cot_history' not in st.session_state:
                            st.session_state.cot_history = []
                        st.session_state.cot_history.append({
                            'step': current_block['title'],
                            'result': result
                        })
                        
                        st.success(f"✅ {current_block['title']} 분석 완료!")
                        
                        # 분석 완료 후 즉시 결과 표시
                        st.markdown("---")
                        st.markdown(f"### 📋 {current_block['title']} 분석 결과")
                        
                        output_structure = current_block.get("content_dsl", {}).get("output_structure", [])
                        if output_structure:
                            parsed_results = parse_analysis_result_by_structure(result, output_structure)
                            result_tabs = st.tabs(output_structure)
                            for i, (tab, structure_name) in enumerate(zip(result_tabs, output_structure)):
                                with tab:
                                    st.markdown(f"### {structure_name}")
                                    content = parsed_results.get(structure_name, "")
                                    if content and not content.startswith("⚠️"):
                                        st.markdown(content)
                                    else:
                                        st.warning("⚠️ 이 구조의 결과를 찾을 수 없습니다.")
                        else:
                            with st.expander(f"📋 {current_block['title']} - 분석 결과", expanded=True):
                                st.markdown(result)
                        
                        # 컨트롤 버튼들
                        st.markdown("---")
                        st.markdown("### 🎛️ 분석 제어")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            if st.button("🔄 다시 분석", key=f"reanalyze_{current_step.id}_{current_step_index}"):
                                # 재분석 실행
                                try:
                                    pdf_summary = get_pdf_summary()
                                    user_inputs = get_user_inputs()
                                    
                                    with st.spinner(f"{current_step.title} 재분석 중..."):
                                        from dsl_to_prompt import convert_dsl_to_prompt
                                        
                                        previous_results = ""
                                        if st.session_state.get('cot_history'):
                                            # 현재 단계 결과 제외
                                            previous_results = "\n\n".join([
                                                f"**{h['step']}**: {h['result']}" 
                                                for h in st.session_state.cot_history 
                                                if h['step'] != current_block['title']
                                            ])
                                        
                                        prompt = convert_dsl_to_prompt(
                                            dsl_block=current_block,
                                            user_inputs=user_inputs,
                                            previous_summary=previous_results,
                                            pdf_summary=pdf_summary,
                                            site_fields=st.session_state.get('site_fields', {}),
                                            include_web_search=False
                                        )
                                        
                                        new_result = execute_claude_analysis(prompt, current_block['title'])
                                        
                                        if new_result and new_result != f"{current_block['title']} 분석 실패":
                                            # 기존 결과 업데이트
                                            for h in st.session_state.cot_history:
                                                if h['step'] == current_block['title']:
                                                    h['result'] = new_result
                                                    break
                                            
                                            save_step_result(current_step.id, new_result)
                                            st.success("✅ 재분석 완료!")
                                            st.rerun()
                                        else:
                                            st.error("❌ 재분석 실패")
                                except Exception as e:
                                    st.error(f"❌ 재분석 오류: {e}")
                        
                        with col2:
                            if st.button("💬 피드백", key=f"feedback_{current_step.id}_{current_step_index}"):
                                st.session_state.show_feedback = True
                                st.rerun()
                        
                        with col3:
                            if current_step_index > 0:
                                if st.button("⬅️ 이전 단계", key=f"prev_{current_step.id}_{current_step_index}"):
                                    st.session_state.current_step_index = current_step_index - 1
                                    st.rerun()
                            else:
                                st.markdown("⬅️ 이전 단계")
                        
                        with col4:
                            if current_step_index < len(current_steps) - 1:
                                if st.button("➡️ 다음 단계", key=f"next_{current_step.id}_{current_step_index}"):
                                    st.session_state.current_step_index = current_step_index + 1
                                    st.rerun()
                            else:
                                if st.button("🏁 완료", key=f"finish_{current_step.id}_{current_step_index}"):
                                    st.success("모든 분석이 완료되었습니다!")
                                    st.session_state.analysis_completed = True
                        
                        # 다음 단계 안내
                        if current_step_index < len(current_steps) - 1:
                            next_step = current_steps[current_step_index + 1]
                            st.info(f"➡️ 다음 단계: {next_step.title}")
                    else:
                        st.error(f"❌ {current_block['title']} 분석 실패")
                
            except Exception as e:
                st.error(f"❌ 분석 실행 오류: {e}")
                import traceback
                st.code(traceback.format_exc())
        
        # 이미 완료된 단계인 경우 결과 표시
        if step_completed:
            st.success(f"✅ {current_step.title} - 분석 완료")
            
            # 결과 표시 - output_structure 기반 탭으로 변경
            step_result = next((h['result'] for h in st.session_state.cot_history if h['step'] == current_step.title), "")
            
            # DSL에서 output_structure 가져오기
            output_structure = current_block.get("content_dsl", {}).get("output_structure", []) if current_block else []
            
            if output_structure:
                # 디버깅 정보 표시 (개발 모드)
                if st.session_state.get('debug_mode', False):
                    with st.expander("🔍 디버깅 정보", expanded=False):
                        st.markdown("**Output Structure:**")
                        for i, structure in enumerate(output_structure, 1):
                            st.markdown(f"{i}. {structure}")
                        
                        st.markdown("**AI 응답 길이:**")
                        st.markdown(f"{len(step_result)} 문자")
                        
                        st.markdown("**구조명 매칭 결과:**")
                        for structure in output_structure:
                            found = structure in step_result
                            st.markdown(f"- {structure}: {'✅' if found else '❌'}")
                        
                        st.markdown("**전체 응답 미리보기:**")
                        st.code(step_result[:1000] + "..." if len(step_result) > 1000 else step_result)
                
                # 결과를 구조별로 파싱
                parsed_results = parse_analysis_result_by_structure(step_result, output_structure)
                
                # output_structure 기반 탭 생성
                result_tabs = st.tabs(output_structure)
                
                for i, (tab, structure_name) in enumerate(zip(result_tabs, output_structure)):
                    with tab:
                        st.markdown(f"### {structure_name}")
                        
                        content = parsed_results.get(structure_name, "")
                        
                        if content and not content.startswith("⚠️"):
                            st.markdown(content)
                        else:
                            st.warning("⚠️ 이 구조의 결과를 찾을 수 없습니다.")
                            
                            # 디버깅 정보 표시
                            with st.expander("🔍 디버깅 정보", expanded=False):
                                st.markdown("**전체 AI 응답:**")
                                st.code(step_result[:1000] + "..." if len(step_result) > 1000 else step_result)
                                
                                st.markdown("**구조명 검색 결과:**")
                                found = structure_name in step_result
                                st.markdown(f"- '{structure_name}' 포함 여부: {'✅' if found else '❌'}")
                                
                                if found:
                                    st.markdown("**관련 부분:**")
                                    idx = step_result.find(structure_name)
                                    context = step_result[max(0, idx-100):idx+len(structure_name)+200]
                                    st.code(context)
            else:
                # output_structure가 없는 경우
                if current_block:
                    expander_title = f"📋 {current_block['title']} - 분석 결과"
                else:
                    expander_title = f"📋 {current_step.title} - 분석 결과"
                
                with st.expander(expander_title, expanded=True):
                    st.markdown(step_result)
            
            # 컨트롤 버튼들 (이미 완료된 단계용)
            st.markdown("---")
            st.markdown("### 🎛️ 분석 제어")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔄 다시 분석", key=f"reanalyze_completed_{current_step.id}_{current_step_index}"):
                    # 재분석 실행
                    try:
                        pdf_summary = get_pdf_summary()
                        user_inputs = get_user_inputs()
                        
                        with st.spinner(f"{current_block['title']} 재분석 중..."):
                            from dsl_to_prompt import convert_dsl_to_prompt
                            
                            previous_results = ""
                            if st.session_state.get('cot_history'):
                                # 현재 단계 결과 제외
                                previous_results = "\n\n".join([
                                    f"**{h['step']}**: {h['result']}" 
                                    for h in st.session_state.cot_history 
                                    if h['step'] != current_block['title']
                                ])
                            
                            prompt = convert_dsl_to_prompt(
                                dsl_block=current_block,
                                user_inputs=user_inputs,
                                previous_summary=previous_results,
                                pdf_summary=pdf_summary,
                                site_fields=st.session_state.get('site_fields', {}),
                                include_web_search=False
                            )
                            
                            new_result = execute_claude_analysis(prompt, current_block['title'])
                            
                            if new_result and new_result != f"{current_block['title']} 분석 실패":
                                # 기존 결과 업데이트
                                for h in st.session_state.cot_history:
                                    if h['step'] == current_block['title']:
                                        h['result'] = new_result
                                        break
                                
                                save_step_result(current_step.id, new_result)
                                st.success("✅ 재분석 완료!")
                                st.rerun()
                            else:
                                st.error("❌ 재분석 실패")
                    except Exception as e:
                        st.error(f"❌ 재분석 오류: {e}")
            
            with col2:
                if st.button("💬 피드백", key=f"feedback_completed_{current_step.id}_{current_step_index}"):
                    st.session_state.show_feedback = True
                    st.rerun()
            
            with col3:
                if current_step_index > 0:
                    if st.button("⬅️ 이전 단계", key=f"prev_completed_{current_step.id}_{current_step_index}"):
                        st.session_state.current_step_index = current_step_index - 1
                        st.rerun()
                else:
                    st.markdown("⬅️ 이전 단계")
            
            with col4:
                if current_step_index < len(current_steps) - 1:
                    if st.button("➡️ 다음 단계", key=f"next_completed_{current_step.id}_{current_step_index}"):
                        st.session_state.current_step_index = current_step_index + 1
                        st.rerun()
                else:
                    if st.button("🏁 완료", key=f"finish_completed_{current_step.id}_{current_step_index}"):
                        st.success("모든 분석이 완료되었습니다!")
                        st.session_state.analysis_completed = True
            
            # 다음 단계 안내
            if current_step_index < len(current_steps) - 1:
                next_step = current_steps[current_step_index + 1]
                st.info(f"➡️ 다음 단계: {next_step.title}")

def render_optimization_tab():
    """최적화 조건 탭 렌더링"""
    st.header("🎯 최적화 조건 분석")
    
    # 분석 결과 확인
    if not st.session_state.get('cot_history'):
        st.warning("⚠️ 먼저 분석을 완료해주세요.")
        return
    
    st.info("�� 기존 분석 결과를 바탕으로 매스별 최적화 조건을 자동으로 분석합니다.")
    
    # 자동 분석 실행
    if st.button("�� 매스별 최적화 조건 자동 분석", type="primary"):
        with st.spinner("매스별 최적화 조건을 자동으로 분석하고 있습니다..."):
            try:
                # 사용자 입력 가져오기
                from user_state import get_user_inputs
                user_inputs = get_user_inputs()
                
                # 새로운 생성 함수 사용
                optimization_result = generate_optimization_analysis(user_inputs, st.session_state.cot_history)
                
                # 결과를 session_state에 저장
                st.session_state.optimization_result = optimization_result
                
                # 결과 표시
                st.success("✅ 매스별 최적화 조건 분석이 완료되었습니다!")
                
                # 결과를 탭으로 표시
                st.markdown("### 📋 매스별 최적화 조건 분석 결과")
                st.markdown(optimization_result)
                
                # 결과 다운로드 버튼
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"mass_optimization_conditions_{timestamp}.json"
                
                # JSON 형태로 결과 저장
                optimization_data = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "project_info": {
                        "project_name": user_inputs.get('project_name', ''),
                        "building_type": user_inputs.get('building_type', ''),
                        "site_location": user_inputs.get('site_location', ''),
                        "owner": user_inputs.get('owner', ''),
                        "site_area": user_inputs.get('site_area', '')
                    },
                    "analysis_result": optimization_result
                }
                
                # JSON 파일 다운로드 버튼
                st.download_button(
                    label=" 매스별 최적화 조건 분석 결과 다운로드",
                    data=json.dumps(optimization_data, ensure_ascii=False, indent=2),
                    file_name=filename,
                    mime="application/json"
                )
                
            except Exception as e:
                st.error(f"❌ 매스별 최적화 조건 분석 중 오류가 발생했습니다: {e}")
    
    # 이전 분석 결과 표시
    if st.session_state.get('optimization_result'):
        st.markdown("### 📋 이전 매스별 최적화 조건 분석 결과")
        with st.expander("이전 분석 결과 보기", expanded=False):
            st.markdown(st.session_state.optimization_result)

def render_tabbed_interface():
    """탭 기반 인터페이스 렌더링"""
    st.header("🏗️ ArchInsight 분석 시스템")
    
    # 탭 생성 (최적화 조건 탭 추가)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 분석 워크플로우", 
        "📊 분석 결과", 
        "🎯 최적화 조건",
        "📝 건축설계 발표용 Narrative", 
        "🎨 ArchiRender GPT",
        "📄 보고서 생성"
    ])
    
    with tab1:
        render_analysis_workflow()
    
    with tab2:
        render_report_tab()
    
    with tab3:
        render_optimization_tab()
    
    with tab4:
        render_claude_narrative_tab()
    
    with tab5:
        render_midjourney_prompt_tab()
    
    with tab6:
        render_report_generation_tab()

def render_report_tab():
    """분석 결과 탭 렌더링"""
    st.header("📊 분석 결과")
    
    if st.session_state.get('cot_history'):
        st.success("✅ 분석이 완료되었습니다!")
        
        # 각 단계별 결과 표시
        st.subheader("📋 각 단계별 분석 결과")
        for i, history in enumerate(st.session_state.cot_history, 1):
            with st.expander(f"📋 {i}. {history['step']}", expanded=True):
                st.markdown(f"**요약:** {history.get('summary', '')}")
                st.markdown(f"**인사이트:** {history.get('insight', '')}")
                st.markdown("---")
                st.markdown(history.get('result', ''))
        
        # PDF/Word 다운로드 섹션 추가 (Tab 6에서 이동)
        st.markdown("---")
        st.subheader("📄 분석 결과 다운로드")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📄 PDF 보고서")
            if st.button("📄 PDF 다운로드", type="primary", key="pdf_download_analysis"):
                with st.spinner("PDF 보고서를 생성하고 있습니다..."):
                    try:
                        from report_generator import generate_report_content, generate_pdf_report
                        report_content = generate_report_content(
                            "전체 분석 보고서", 
                            True, 
                            True, 
                            False
                        )
                        
                        pdf_data = generate_pdf_report(report_content, st.session_state)
                        st.download_button(
                            label="📄 PDF 다운로드",
                            data=pdf_data,
                            file_name=f"{st.session_state.get('project_name', '분석보고서')}_보고서.pdf",
                            mime="application/pdf",
                            key="pdf_download_analysis_final"
                        )
                        
                    except Exception as e:
                        st.error(f"PDF 생성 오류: {e}")
        
        with col2:
            st.markdown("#### 📄 Word 보고서")
        if st.button("📄 Word 다운로드", type="primary", key="word_download_analysis"):
            with st.spinner("Word 보고서를 생성하고 있습니다..."):
                try:
                    from report_generator import generate_report_content, generate_word_report
                    report_content = generate_report_content(
                        "전체 분석 보고서", 
                        True, 
                        True, 
                        False
                    )
                        
                    word_data = generate_word_report(report_content, st.session_state)
                    st.download_button(
                        label="📄 Word 다운로드",
                        data=word_data,
                        file_name=f"{st.session_state.get('project_name', '분석보고서')}_보고서.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="word_download_analysis_final"
                    )
                    
                except Exception as e:
                    st.error(f"Word 생성 오류: {e}")
        
        # 전체 누적 분석 결과
        st.markdown("---")
        st.subheader("📊 전체 누적 분석 결과")
        
        # 사용자 입력 가져오기
        from user_state import get_user_inputs
        user_inputs = get_user_inputs()
        
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
        
        # 전체 분석 결과를 output_structure 기반 동적 탭으로 표시
        st.markdown("#### 📊 전체 분석 결과")
        
        # DSL에서 output_structure 가져오기
        from prompt_loader import load_prompt_blocks
        blocks = load_prompt_blocks()
        extra_blocks = blocks["extra"]
        
        # 모든 단계의 output_structure 수집
        all_output_structures = set()
        for block in extra_blocks:
            if "content_dsl" in block and "output_structure" in block["content_dsl"]:
                for structure in block["content_dsl"]["output_structure"]:
                    all_output_structures.add(structure)
        
        if all_output_structures:
            # output_structure 기반 동적 탭 생성
            result_tabs = st.tabs(list(all_output_structures))
            
            for i, (tab, structure_name) in enumerate(zip(result_tabs, all_output_structures)):
                with tab:
                    st.markdown(f"### {structure_name}")
                    
                    # 각 단계별로 해당 구조에 맞는 내용 표시
                    for j, history in enumerate(st.session_state.cot_history):
                        st.markdown(f"####  단계 {j+1}: {history.get('step', f'단계 {j+1}')}")
                        
                        # 구조별로 다른 표시 방식
                        if "매트릭스" in structure_name or "표" in structure_name:
                            st.markdown("##### 📊 구조화된 데이터")
                            st.markdown(history.get('result', '')[:500] + "...")
                        elif "분석" in structure_name or "추론" in structure_name:
                            st.markdown("##### 🧠 분석 및 추론")
                            st.markdown(history.get('result', '')[:500] + "...")
                        else:
                            st.markdown("##### 📋 일반 결과")
                            st.markdown(history.get('result', '')[:500] + "...")
        else:
            # 기본 탭 구조
            tab1, tab2, tab3, tab4 = st.tabs(["📊 요구사항", "🧠 AI 추론", "🧾 유사 사례비교", "✅ 전략제언"])
            
            with tab1:
                st.markdown("#### 📊 요구사항 정리표")
                for history in st.session_state.cot_history:
                    st.markdown(f"**{history.get('step', '')}**")
                    st.markdown(history.get('result', '')[:300] + "...")
                    st.markdown("---")
            
            with tab2:
                st.markdown("#### 🧠 AI 추론 해설")
                for history in st.session_state.cot_history:
                    st.markdown(f"**{history.get('step', '')}**")
                    st.markdown(history.get('result', '')[:300] + "...")
                    st.markdown("---")
            
            with tab3:
                st.markdown("#### 🧾 유사 사례 비교")
                for history in st.session_state.cot_history:
                    st.markdown(f"**{history.get('step', '')}**")
                    st.markdown(history.get('result', '')[:300] + "...")
                    st.markdown("---")
            
            with tab4:
                st.markdown("#### ✅ 전략적 제언 및 시사점")
                for history in st.session_state.cot_history:
                    st.markdown(f"**{history.get('step', '')}**")
                    st.markdown(history.get('result', '')[:300] + "...")
                    st.markdown("---")
    else:
        st.info("�� 분석을 먼저 진행해주세요.")

def render_claude_narrative_tab():
    """Claude Narrative 탭 렌더링"""
    st.header("�� 건축설계 발표용 Narrative 생성 시스템")
    
    # 분석 결과 확인
    if not st.session_state.get('cot_history'):
        st.warning("⚠️ 먼저 분석을 완료해주세요.")
        return
    
    st.info("📝 건축설계 발표용 Narrative를 단계별로 생성하는 구조화된 시스템입니다.")
    
    # STEP 1: 기본 정보 입력
    st.subheader("STEP 1: 기본 정보 입력")
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input("프로젝트명", value=st.session_state.get('project_name', ''))
        building_type = st.text_input("건물 유형", value=st.session_state.get('building_type', ''))
        site_location = st.text_input("대지 위치", value=st.session_state.get('site_location', ''))
        owner = st.text_input("건축주", value=st.session_state.get('owner', ''))
        owner_type = st.selectbox("발주처 특성", ["공공기관", "민간기업", "개인", "교육기관", "의료기관", "문화기관"])
            
    with col2:
        site_area = st.text_input("대지 면적", value=st.session_state.get('site_area', ''))
        building_scale = st.text_input("건물 규모", placeholder="연면적, 층수 등")
        surrounding_env = st.text_area("주변 환경", placeholder="자연환경, 도시환경, 교통, 랜드마크 등")
        regional_context = st.text_area("지역적 맥락", placeholder="역사, 문화, 사회적 특성")
    
    # STEP 2: Narrative 방향 설정
    st.subheader("STEP 2: Narrative 방향 설정")
    
    # 2-1. 감성 ↔ 논리 비율 선택
    st.markdown("#### 2-1. 감성 ↔ 논리 비율 선택")
    emotion_logic_ratio = st.selectbox(
        "감성/논리 비율을 선택하세요:",
        [
            "A. 감성 중심형 (감성 90% / 논리 10%) - 감정적 울림, 서정적 표현, 상징성 중심",
            "B. 균형형 (감성 60% / 논리 40%) - 사용자 경험 중심 + 분석 기반 논리 서술의 조화",
            "C. 전략 중심형 (감성 30% / 논리 70%) - 기능적 해법 + 분석 데이터 기반 논리 중심",
            "D. 데이터 기반형 (감성 10% / 논리 90%) - 통계·규범·정책 중심 논리적 설득"
        ]
    )
    
    # 2-2. 서술 스타일/톤 선택
    st.markdown("#### 2-2. 서술 스타일/톤 선택")
    narrative_tone = st.selectbox(
        "서술 스타일을 선택하세요:",
        [
            "A. 공공적/진정성형 - 지역사회 기여, 지속가능성, 공동체 가치 강조",
            "B. 비즈니스 중심형 - 경제성, 차별화 전략, 고객 경험 중심 강조",
            "C. 미래지향/비전형 - 변화 주도, 혁신, 미래 라이프스타일 제안",
            "D. 문화/상징성형 - 장소성, 역사 해석, 상징적 메시지 중심",
            "E. 사용자 감성형 - 일상 경험과 공간의 만남, 감각 중심"
        ]
    )
    
    # 2-3. 키 메시지 중심 방향 선택
    st.markdown("#### 2-3. 키 메시지 중심 방향 선택")
    key_message_direction = st.selectbox(
        "핵심 메시지 방향을 선택하세요:",
        [
            "A. Vision 중심형 - 이 건축이 실현할 미래를 제시하는 선언적 서술",
            "B. Problem-Solution형 - 이 문제가 있었고, 이렇게 해결했다는 설계 전략 중심",
            "C. User Journey형 - 사용자의 여정은 어떻게 변화하는가? 사용자 감정·동선 중심",
            "D. Context-Driven형 - 이 땅, 이 장소에서의 필연성은? Site 중심 서술",
            "E. Symbolic Message형 - 이 건물은 어떤 메시지를 담고 있는가? 감정적 울림 강조"
        ]
    )
    
    # 2-4. 건축적 가치 우선순위 선택
    st.markdown("#### 2-4. 건축적 가치 우선순위 선택")
    architectural_value = st.selectbox(
        "건축적 가치 우선순위를 선택하세요:",
        [
            "A. 장소성 우선 - Site-specific한 고유성 추구, 맥락적 건축",
            "B. 기능성 우선 - 사용자 니즈와 효율성 중심, 합리적 건축",
            "C. 미학성 우선 - 아름다움과 감동 추구, 조형적 건축",
            "D. 지속성 우선 - 환경과 미래 세대 고려, 친환경 건축",
            "E. 사회성 우선 - 공동체와 소통 중심, 공공적 건축",
            "F. 혁신성 우선 - 새로운 가능성 탐구, 실험적 건축"
        ]
    )
    
    # 2-5. 건축적 내러티브 전개 방식 선택
    st.markdown("#### 2-5. 건축적 내러티브 전개 방식 선택")
    narrative_structure = st.selectbox(
        "내러티브 전개 방식을 선택하세요:",
        [
            "A. 형태 생성 과정형 - 이 형태는 어떻게 탄생했는가? 대지→매스→공간→디테일 순차 전개",
            "B. 공간 경험 여정형 - 사용자는 어떤 공간을 경험하는가? 진입→이동→머무름→떠남의 시퀀스",
            "C. 기능 조직 논리형 - 프로그램들이 어떻게 조직되는가? 기능분석→배치전략→공간구성",
            "D. 구조 시스템형 - 건물은 어떤 원리로 서 있는가? 구조체→공간→형태의 통합적 설명",
            "E. 환경 대응 전략형 - 자연과 건축이 어떻게 만나는가? 미기후→배치→형태→재료 연계",
            "F. 문화적 해석형 - 전통과 현대가 어떻게 만나는가? 역사적 맥락→현대적 번역→공간화"
        ]
    )
    
    # 2-6. 강조할 설계 요소 선택 (복수 선택 가능)
    st.markdown("#### 2-6. 강조할 설계 요소 선택 (복수 선택 가능)")
    design_elements = st.multiselect(
        "강조할 설계 요소를 선택하세요:",
        [
            "매스/형태 - 조형적 아름다움, 상징성으로 시각적 임팩트",
            "공간 구성 - 동선, 기능 배치의 합리성으로 사용성 어필",
            "친환경/지속가능 - 에너지 효율, 친환경 기술로 사회적 가치",
            "기술/혁신 - 신기술 적용, 스마트 시스템으로 선진성 강조",
            "경제성 - 건설비, 운영비 절감으로 실용성 어필",
            "안전성 - 구조적 안정, 방재 계획으로 신뢰성 구축",
            "문화/역사 - 지역성, 전통의 현대적 해석으로 정체성 강화",
            "사용자 경험 - 편의성, 접근성, 쾌적성으로 만족도 제고"
        ]
    )
    
    # STEP 3: Narrative 생성
    st.subheader("STEP 3: Narrative 생성")
    if st.button("🎯 Narrative 생성", type="primary"):
        if not all([project_name, building_type, owner]):
            st.error("❌ 기본 정보를 모두 입력해주세요.")
            return
        
        with st.spinner("Narrative를 생성하고 있습니다..."):
            try:
                # 분석 결과 요약
                analysis_summary = "\n\n".join([
                    f"**{h['step']}**: {h.get('summary', '')}"
                    for h in st.session_state.cot_history
                ])
                
                # Narrative 생성 프롬프트를 소설처럼 감성적이고 몰입감 있게 개선
                narrative_prompt = f"""
당신은 건축설계 발표용 Narrative를 작성하는 소설가입니다. 
기술적 분석이나 딱딱한 설명이 아닌, 소설처럼 감성적이고 몰입감 있는 스토리로 작성해주세요.

프로젝트 정보:
- 프로젝트명: {project_name}
- 건물 유형: {building_type}
- 건축주: {owner}
- 발주처 특성: {owner_type}
- 대지 위치: {site_location}
- 대지 면적: {site_area}
- 건물 규모: {building_scale}
- 주변 환경: {surrounding_env}
- 지역적 맥락: {regional_context}

Narrative 방향 설정:
1. 감성/논리 비율: {emotion_logic_ratio}
2. 서술 스타일: {narrative_tone}
3. 키 메시지 방향: {key_message_direction}
4. 건축적 가치 우선순위: {architectural_value}
5. 내러티브 전개 방식: {narrative_structure}
6. 강조 설계 요소: {', '.join(design_elements)}

분석 결과:
{analysis_summary}

위 정보를 바탕으로 소설처럼 감성적이고 몰입감 있는 Narrative를 작성해주세요.

중요한 지시사항:
1. 소설처럼 감성적이고 몰입감 있는 서술
2. "이 땅에서 발견한 세 가지 진실" 같은 스토리적 접근
3. 구체적인 공간 경험과 사용자 여정을 소설처럼 묘사
4. 건축적 해답을 스토리로 풀어내기
5. 청중의 감정을 움직이는 서술 방식 사용
6. 기술적 설명이 아닌 감성적 서술

예시 스타일:
- "첫 번째 진실 - 자연의 품: 북측 공원과 남측 한강이 품어주는 이 땅은..."
- "자연이 건네는 설계 언어: 북측 공원의 속삭임 '경계를 허물어라...'"
- "100년 헤리티지, 100년 비전: 과거를 품다, 현재를 살다, 미래를 열다"
- "땅에서 자란 나무처럼: 뿌리(Root) - 땅에서 자란 네 그루 나무"
- "매 순간이 특별한 여정: 아침 7시 - 새로운 시작"

다음 구조로 소설처럼 감성적이고 몰입감 있는 Narrative를 작성해주세요:

Part 1.  프로젝트 기본 정보
Part 2.  Core Story: 땅이 말하는 미래
Part 3. 📍 땅이 주는 답: The Rooted Future
Part 4. 🏢 {owner}이 꿈꾸는 미래
Part 5. 💡 [컨셉명] 컨셉의 건축적 구현
Part 6. ️ 건축적 해답: 네 가지 핵심 전략
Part 7. 🎯 공간 시나리오: 하루의 여정
Part 8. 🎯 결론: 왜 이 제안인가?

소설처럼 감성적이고 몰입감 있는 스토리텔링으로 작성해주세요.
"""
                
                # Narrative 생성 함수 호출
                from agent_executor import execute_agent
                narrative_result = execute_agent(narrative_prompt)
                
                # 결과 표시
                st.success("✅ Narrative 생성 완료!")
                st.markdown("### 📝 생성된 Narrative")
                st.markdown(narrative_result)
                
                # 다운로드 버튼
                st.download_button(
                    label="📄 Narrative 다운로드",
                    data=narrative_result,
                    file_name=f"{project_name}_Narrative.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ Narrative 생성 중 오류가 발생했습니다: {e}")
    
    # STEP 4: 피드백 및 수정
    st.subheader("STEP 4: 피드백 및 수정")
    st.info("🔄 생성된 Narrative에 대한 피드백을 받아 수정하는 기능은 향후 구현 예정입니다.")

def render_midjourney_prompt_tab():
    """ArchiRender GPT 탭 렌더링"""
    st.header("🎨 ArchiRender GPT")
    
    # 분석 결과 확인
    if not st.session_state.get('cot_history'):
        st.warning("⚠️ 먼저 분석을 완료해주세요.")
        return
    
    st.info("🎨 Midjourney 이미지 생성 프롬프트를 생성합니다.")
    
    # 이미지 생성 옵션
    st.subheader("이미지 생성 옵션")
    image_type = st.selectbox(
        "이미지 유형",
        ["외관 렌더링", "내부 공간", "마스터플랜", "상세도", "컨셉 이미지", "조감도"]
    )
    
    style_preference = st.multiselect(
        "스타일 선호도",
        ["현대적", "미니멀", "자연친화적", "고급스러운", "기능적", "예술적", "상업적"]
    )
    
    additional_description = st.text_area(
        "추가 설명",
        placeholder="특별히 강조하고 싶은 요소나 스타일을 자유롭게 입력하세요."
    )
    
    # 프롬프트 생성
    if st.button("🎨 프롬프트 생성", type="primary"):
        with st.spinner("이미지 생성 프롬프트를 생성하고 있습니다..."):
            try:
                # 분석 결과 요약
                analysis_summary = "\n\n".join([
                    f"**{h['step']}**: {h.get('summary', '')}"
                    for h in st.session_state.cot_history
                ])
                
                # 이미지 생성 프롬프트
                image_prompt = f"""
프로젝트 정보:
- 프로젝트명: {st.session_state.get('project_name', '')}
- 건물 유형: {st.session_state.get('building_type', '')}
- 대지 위치: {st.session_state.get('site_location', '')}
- 건축주: {st.session_state.get('owner', '')}
- 대지 면적: {st.session_state.get('site_area', '')}

분석 결과:
{analysis_summary}

이미지 생성 요청:
- 이미지 유형: {image_type}
- 스타일: {', '.join(style_preference) if style_preference else '기본'}
- 추가 설명: {additional_description}

위 정보를 바탕으로 Midjourney에서 사용할 수 있는 상세하고 구체적인 이미지 생성 프롬프트를 생성해주세요.
프롬프트는 영어로 작성하고, 건축적 특성을 잘 반영하도록 해주세요.
"""
                
                # Claude API 호출
                from agent_executor import execute_agent
                prompt_result = execute_agent(image_prompt)
                
                # 결과 표시
                st.success("✅ 이미지 생성 프롬프트 생성 완료!")
                st.markdown("### 🎨 생성된 프롬프트")
                st.markdown(prompt_result)
                
                # 다운로드 버튼
                st.download_button(
                    label="📄 프롬프트 다운로드",
                    data=prompt_result,
                    file_name=f"{st.session_state.get('project_name', 'project')}_image_prompt.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"❌ 프롬프트 생성 중 오류가 발생했습니다: {e}")
    
    # 사용 가이드
    st.subheader("📖 사용 가이드")
    st.markdown("""
    1. **프롬프트 복사**: 생성된 프롬프트를 복사합니다.
    2. **Midjourney 접속**: Discord에서 Midjourney 봇을 찾습니다.
    3. **프롬프트 입력**: `/imagine` 명령어와 함께 프롬프트를 입력합니다.
    4. **이미지 생성**: Midjourney가 이미지를 생성할 때까지 기다립니다.
    5. **결과 확인**: 생성된 이미지를 확인하고 필요시 변형을 요청합니다.
    """)

def render_report_generation_tab():
    """보고서 생성 탭 렌더링 - 순서 변경"""
    st.header("📄 보고서 생성")
    
    if not st.session_state.get('cot_history'):
        st.warning("⚠️ 먼저 분석을 완료해주세요.")
        return
    
    st.success("✅ 분석 결과를 바탕으로 다양한 형태의 보고서를 생성할 수 있습니다.")
    
    # 사용자 입력 가져오기
    from user_state import get_user_inputs
    user_inputs = get_user_inputs()
    
    # 분석 결과 수집
    analysis_results = []
    if st.session_state.get('cot_history'):
        for i, history in enumerate(st.session_state.cot_history, 1):
            analysis_results.append({
                'step': history.get('step', f'단계 {i}'),
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
    
    # 1. 문서 보고서 (맨 상단)
    st.subheader("📄 문서 보고서")
    report_type = st.selectbox(
        "보고서 유형",
        ["전체 분석 보고서", "요약 보고서", "전문가 보고서", "클라이언트 보고서"],
        key="report_type_generation"
    )
    
    include_charts = st.checkbox("📊 차트 포함", value=True, key="charts_generation")
    include_recommendations = st.checkbox("💡 권장사항 포함", value=True, key="recommendations_generation")
    include_appendix = st.checkbox("📋 부록 포함", value=False, key="appendix_generation")
    
    if st.button("📄 보고서 생성", type="primary", key="generate_report_generation"):
        with st.spinner("보고서를 생성하고 있습니다..."):
            try:
                # 보고서 내용 생성
                from report_generator import generate_report_content, generate_pdf_report, generate_word_report
                report_content = generate_report_content(
                    report_type, 
                    include_charts, 
                    include_recommendations, 
                    include_appendix
                )
                
                # 다운로드 버튼들
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.download_button(
                        label="📄 TXT 다운로드",
                        data=report_content,
                        file_name=f"{st.session_state.get('project_name', '분석보고서')}_보고서.txt",
                        mime="text/plain"
                    )
                
                with col_b:
                    try:
                        pdf_data = generate_pdf_report(report_content, st.session_state)
                        st.download_button(
                            label="📄 PDF 다운로드",
                            data=pdf_data,
                            file_name=f"{st.session_state.get('project_name', '분석보고서')}_보고서.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"PDF 생성 오류: {e}")
                
                with col_c:
                    try:
                        word_data = generate_word_report(report_content, st.session_state)
                        st.download_button(
                            label="📄 Word 다운로드",
                            data=word_data,
                            file_name=f"{st.session_state.get('project_name', '분석보고서')}_보고서.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                        )
                    except Exception as e:
                        st.error(f"Word 생성 오류: {e}")
                
                # 보고서 내용 미리보기
                st.subheader("📋 보고서 미리보기")
                st.markdown(report_content[:2000] + ("..." if len(report_content) > 2000 else ""))
                
            except Exception as e:
                st.error(f"❌ 보고서 생성 중 오류가 발생했습니다: {e}")

    st.markdown("---")
    
    # 2. 웹페이지 생성 (중간)
    st.subheader("📄 웹페이지 생성")
    from webpage_generator import create_webpage_download_button
    create_webpage_download_button(analysis_results, project_info, show_warning=False)
    
    st.markdown("---")
    
    # 3. 분석 보고서 (맨 하단)
    st.subheader("📊 분석 보고서")
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
    
    # 분석 결과 요약
    st.markdown("#### 📊 분석 결과 요약")
    if st.session_state.get('cot_history'):
        for i, history in enumerate(st.session_state.cot_history, 1):
            st.markdown(f"**{i}. {history.get('step', f'단계 {i}')}**")
            st.markdown(f"요약: {history.get('summary', '')}")
            st.markdown("---")

def parse_analysis_result_by_structure(result: str, output_structure: list) -> dict:
    """완전히 개선된 분석 결과 파싱 함수"""
    parsed_results = {}
    
    # 각 구조별로 정확한 경계 찾기
    for i, structure in enumerate(output_structure, 1):
        # 정확한 마커 패턴들 (우선순위 순)
        markers = [
            f"## {i}. {structure}",
            f"## {structure}",
            f"{i}. {structure}",
            f"### {structure}",
            f"**{structure}**",
            structure
        ]
        
        content = None
        start_idx = -1
        used_marker = None
        
        # 마커 찾기
        for marker in markers:
            start_idx = result.find(marker)
            if start_idx != -1:
                used_marker = marker
                break
        
        if start_idx != -1:
            # 다음 구조의 시작 위치 찾기
            end_idx = len(result)
            
            # 다음 번호의 구조 찾기
            for j, next_structure in enumerate(output_structure[i:], i+1):
                next_markers = [
                    f"## {j}. {next_structure}",
                    f"## {next_structure}",
                    f"{j}. {next_structure}",
                    f"### {next_structure}",
                    f"**{next_structure}**"
                ]
                
                for next_marker in next_markers:
                    next_idx = result.find(next_marker, start_idx + len(used_marker))
                    if next_idx != -1 and next_idx < end_idx:
                        end_idx = next_idx
                        break
                
                if end_idx < len(result):
                    break
            
            # 내용 추출
            content_start = start_idx + len(used_marker)
            content = result[content_start:end_idx].strip()
            
            # 앞뒤 공백 및 불필요한 문자 제거
            content = content.strip()
            if content.startswith('\n'):
                content = content[1:]
            if content.endswith('\n'):
                content = content[:-1]
            
            # 내용이 너무 짧으면 무효로 처리
            if len(content) < 10:
                content = None
        
        # 내용을 찾지 못한 경우
        if not content:
            # 키워드 기반 검색
            keywords = structure.lower().split()
            lines = result.split('\n')
            
            relevant_lines = []
            for line in lines:
                line_lower = line.lower()
                if any(keyword in line_lower for keyword in keywords):
                    relevant_lines.append(line)
            
            if relevant_lines:
                content = '\n'.join(relevant_lines[:10])  # 최대 10줄
            else:
                content = f"⚠️ '{structure}' 구조의 결과를 찾을 수 없습니다."
        
        parsed_results[structure] = content
    
    return parsed_results

def create_analysis_workflow(purpose_enum, objective_enums):
    """워크플로우 생성 함수"""
    system = AnalysisSystem()
    return system.suggest_analysis_steps(purpose_enum, objective_enums)

def validate_user_inputs(user_inputs):
    """사용자 입력 검증 함수"""
    missing_fields = [field for field in REQUIRED_FIELDS if not user_inputs.get(field)]
    return missing_fields

def create_pdf_summary_dict(user_inputs, pdf_summary):
    """PDF 요약 딕셔너리 생성 함수"""
    return {
        "pdf_summary": pdf_summary,
        "project_name": user_inputs.get("project_name", ""),
        "owner": user_inputs.get("owner", ""),
        "site_location": user_inputs.get("site_location", ""),
        "site_area": user_inputs.get("site_area", ""),
        "building_type": user_inputs.get("building_type", ""),
        "project_goal": user_inputs.get("project_goal", "")
    }

def validate_and_fix_prompt(dsl_block: dict) -> dict:
    """DSL 블록 검증 및 수정"""
    content_dsl = dsl_block.get("content_dsl", {})
    output_structure = content_dsl.get("output_structure", [])
    
    if not output_structure:
        st.warning("⚠️ output_structure가 정의되지 않았습니다.")
        return dsl_block
    
    # 중복 제거
    unique_structure = list(dict.fromkeys(output_structure))
    if len(unique_structure) != len(output_structure):
        st.info("ℹ️ 중복된 구조명이 제거되었습니다.")
        content_dsl["output_structure"] = unique_structure
    
    return dsl_block

def generate_optimization_analysis(user_inputs, cot_history):
    """최적화 조건 분석 생성 함수"""
    from agent_executor import execute_agent
    
    # 분석 결과 요약
    analysis_summary = "\n\n".join([
        f"**{h['step']}**: {h.get('result', '')}"
        for h in cot_history
    ])
    
    optimization_prompt = f"""
프로젝트 정보:
- 프로젝트명: {user_inputs.get('project_name', '')}
- 건물 유형: {user_inputs.get('building_type', '')}
- 대지 위치: {user_inputs.get('site_location', '')}
- 건축주: {user_inputs.get('owner', '')}
- 대지 면적: {user_inputs.get('site_area', '')}

분석 결과:
{analysis_summary}

위 정보를 바탕으로 매스별 최적화 조건을 분석해주세요.
"""
    
    return execute_agent(optimization_prompt)

def generate_narrative(user_inputs, cot_history, user_settings):
    """Narrative 생성 함수"""
    from agent_executor import execute_agent
    
    # Implementation for narrative generation
    narrative_prompt = f"""
프로젝트 정보를 바탕으로 건축설계 발표용 Narrative를 생성해주세요.
"""
    
    return execute_agent(narrative_prompt)

def generate_midjourney_prompt(user_inputs, cot_history, image_settings):
    """Midjourney 프롬프트 생성 함수"""
    from agent_executor import execute_agent
    
    # Implementation for midjourney prompt generation
    image_prompt = f"""
프로젝트 정보를 바탕으로 Midjourney 이미지 생성 프롬프트를 생성해주세요.
"""
    
    return execute_agent(image_prompt)

def render_analysis_workflow():
    """분석 워크플로우 렌더링"""
    st.header("🔍 분석 워크플로우")
    
    # 분석이 시작되었는지 확인
    if st.session_state.get('analysis_started', False):
        # 분석 실행 UI 호출
        render_analysis_execution()
        return
    
    # 사용자 입력 가져오기
    user_inputs = get_user_inputs()
    
    # 1단계: 목적과 용도 선택
    st.subheader("📋 1단계: 분석 목적과 용도 선택")
    
    from analysis_system import AnalysisSystem, PurposeType, ObjectiveType
    system = AnalysisSystem()
    
    # 용도 선택
    purpose_options = [purpose.value for purpose in PurposeType]
    selected_purpose = st.selectbox(
        "🏗️ 건물 용도 선택",
        purpose_options,
        key="selected_purpose_workflow"
    )
    
    # 선택된 용도에 따른 목적 옵션 표시
    if selected_purpose:
        purpose_enum = PurposeType(selected_purpose)
        available_objectives = system.get_available_objectives(purpose_enum)
        objective_options = [obj.value for obj in available_objectives]
        
        selected_objectives = st.multiselect(
            "분석 목적 선택 (복수 선택 가능)",
            objective_options,
            key="selected_objectives_workflow"
        )
        
        # 선택된 목적들을 ObjectiveType으로 변환
        objective_enums = [ObjectiveType(obj) for obj in selected_objectives]
        
        # 워크플로우 제안
        if selected_objectives:
            st.success(f"✅ 선택된 용도: {selected_purpose}")
            st.success(f"✅ 선택된 목적: {', '.join(selected_objectives)}")
            
            # 워크플로우 생성
            workflow = system.suggest_analysis_steps(purpose_enum, objective_enums)
            
            # 제안된 단계들 표시 및 편집 기능
            st.subheader("📋 2단계: 분석 단계 편집")
            st.info("제안된 단계들을 자유롭게 편집할 수 있습니다:")
            
            # 편집 가능한 단계 리스트 업데이트 (목적 변경 시마다)
            current_selection = f"{selected_purpose}_{','.join(selected_objectives)}"
            if 'current_selection' not in st.session_state or st.session_state.current_selection != current_selection:
                st.session_state.editable_steps = workflow.steps.copy()
                st.session_state.current_selection = current_selection
            
            # 단계 편집 인터페이스
            st.markdown("#### 📝 현재 분석 단계")
            
            # 각 단계를 편집 가능한 형태로 표시
            for i, step in enumerate(st.session_state.editable_steps):
                with st.expander(f"{i+1}. {step.title}", expanded=True):
                    col_a, col_b, col_c = st.columns([2, 1, 1])
                    
                    with col_a:
                        st.markdown(f"**설명**: {step.description}")
                        if step.is_required:
                            st.caption("🔴 필수 단계")
                        elif step.is_recommended:
                            st.caption("🟡 권장 단계")
                        else:
                            st.caption("🟢 선택 단계")
                    
                    with col_b:
                        if st.button("❌ 제거", key=f"remove_{step.id}_workflow"):
                            st.session_state.editable_steps.pop(i)
                            st.rerun()
                    
                    with col_c:
                        if i > 0:
                            if st.button("⬆️ 위로", key=f"up_{step.id}_workflow"):
                                st.session_state.editable_steps[i], st.session_state.editable_steps[i-1] = \
                                    st.session_state.editable_steps[i-1], st.session_state.editable_steps[i]
                                st.rerun()
                        if i < len(st.session_state.editable_steps) - 1:
                            if st.button("⬇️ 아래로", key=f"down_{step.id}_workflow"):
                                st.session_state.editable_steps[i], st.session_state.editable_steps[i+1] = \
                                    st.session_state.editable_steps[i+1], st.session_state.editable_steps[i]
                                st.rerun()
            
            # 분석 시작 버튼
            if st.button("분석 시작", key="start_analysis_workflow"):
                # 필수 정보 확인
                missing_fields = []
                for field in REQUIRED_FIELDS:
                    if not user_inputs.get(field):
                        missing_fields.append(field)
                
                if missing_fields:
                    st.error(f"❌ 다음 필수 정보를 입력해주세요: {', '.join(missing_fields)}")
                    st.stop()
                
                # PDF 처리 상태 확인
                pdf_summary = st.session_state.get('pdf_summary', '')
                if not pdf_summary:
                    st.error("❌ PDF 처리가 완료되지 않았습니다. PDF를 다시 업로드해주세요.")
                    st.stop()
                
                # 분석 단계 초기화
                st.session_state.analysis_started = True
                st.session_state.current_step_index = 0
                st.session_state.cot_history = []
                st.session_state.workflow_steps = st.session_state.editable_steps
                st.session_state.current_step_outputs = {}
                
                st.success("✅ 분석이 시작되었습니다!")
                st.rerun()

def main():
    """메인 함수"""
    render_tabbed_interface()

if __name__ == "__main__":
    main() 