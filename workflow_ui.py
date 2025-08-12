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
from user_state import get_user_inputs, get_pdf_summary
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
from summary_generator import analyze_pdf_comprehensive, get_pdf_quality_report
from prompt_loader import load_prompt_blocks
from agent_executor import *
from dsl_to_prompt import convert_dsl_to_prompt
from user_state import save_step_result, append_step_history
from utils import extract_summary, extract_insight
from typing import List

# 파일 상단에 상수 정의
REQUIRED_FIELDS = ["project_name", "building_type", "site_location", "owner", "site_area", "project_goal"]
FEEDBACK_TYPES = ["추가 분석 요청", "수정 요청", "다른 관점 제시", "구조 변경", "기타"]

def execute_claude_analysis(prompt, description):
    """Claude 분석 실행 함수 - agent_executor의 execute_agent 사용"""
    try:
        result = execute_agent(prompt)
        return result
    except Exception as e:
        st.error(f"분석 실행 오류: {e}")
        return f"{description} 분석 실패"

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
            if not step.is_required:  # 필수 단계는 제거 불가
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
            if i > 0:  # 첫 번째가 아닌 경우에만
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
            if i < len(all_steps) - 1:  # 마지막이 아닌 경우에만
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

def render_analysis_execution():
    """분석 실행 UI - 단계별 진행 방식"""
    if not st.session_state.get('analysis_started', False):
        return

    st.title("🏗️ 건축 분석 워크플로우")
    st.subheader("### 분석 실행")

    # 간단 검색 시스템 초기화
    try:
        from utils_pdf_vector import initialize_vector_system
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
        from prompt_loader import load_prompt_blocks
        blocks = load_prompt_blocks()
        extra_blocks = blocks.get("extra", [])
        blocks_by_id = {b["id"]: b for b in extra_blocks}

        ordered_blocks = []
        for step in current_steps:
            if step.id in blocks_by_id:
                ordered_blocks.append(blocks_by_id[step.id])

        st.session_state.ordered_blocks = ordered_blocks
        
    except Exception as e:
        st.error(f"❌ 프롬프트 블록 로드 실패: {e}")
        return

    # 3) 진행 표시
    current_step_index = st.session_state.get('current_step_index', 0)
    total_steps = len(ordered_blocks)

    if total_steps == 0:
        st.warning("⚠️ 실행할 분석 단계가 없습니다.")
        return

    progress_percentage = ((current_step_index + 1) / total_steps) * 100
    st.progress(progress_percentage / 100)
    st.write(f"**진행 상황**: {current_step_index + 1} / {total_steps}")

    # 4) 현재 단계 표시 및 실행
    if current_step_index < len(ordered_blocks):
        current_block = ordered_blocks[current_step_index]
        
        st.markdown(f"### 🔍 현재 단계: {current_block['title']}")
        st.markdown(f"**설명**: {current_block.get('description', '설명 없음')}")
        
        # 현재 단계의 분석 상태 확인
        current_step_id = current_block['id']
        step_completed = any(h['step'] == current_block['title'] for h in st.session_state.get('cot_history', []))
        
        if not step_completed:
            # 분석 실행 버튼
            if st.button(f"🚀 {current_block['title']} 분석 실행", type="primary", key=f"analyze_{current_step_id}_{current_step_index}"):
                try:
                    # PDF 요약 정보 가져오기
                    pdf_summary = get_pdf_summary()
                    if not pdf_summary:
                        st.error("❌ PDF 요약 정보가 없습니다. PDF를 다시 업로드해주세요.")
                        return
                    
                    # 사용자 입력 정보 가져오기
                    user_inputs = get_user_inputs()
                    
                    # 분석 실행
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
                            save_step_result(current_step_id, result)
                            append_step_history(current_step_id, current_block['title'], prompt, result)
                            
                            # cot_history에도 추가 (기존 호환성 유지)
                            if 'cot_history' not in st.session_state:
                                st.session_state.cot_history = []
                            st.session_state.cot_history.append({
                                'step': current_block['title'],
                                'result': result
                            })
                            
                            st.success(f"✅ {current_block['title']} 분석 완료!")
                            st.rerun()
                        else:
                            st.error(f"❌ {current_block['title']} 분석 실패")
                        
                except Exception as e:
                    st.error(f"❌ 분석 실행 오류: {e}")
                    import traceback
                    st.code(traceback.format_exc())
        else:
            # 이미 완료된 단계 - 결과 표시 및 컨트롤 버튼들
            st.success(f"✅ {current_block['title']} - 분석 완료")
            
            # 결과 표시 - output_structure 기반 탭으로 변경
            step_result = next((h['result'] for h in st.session_state.cot_history if h['step'] == current_block['title']), "")
            
            # DSL에서 output_structure 가져오기
            output_structure = current_block.get("content_dsl", {}).get("output_structure", [])
            
            if output_structure:
                # 결과를 구조별로 파싱
                parsed_results = parse_analysis_result_by_structure(step_result, output_structure)
                
                # output_structure 기반 탭 생성
                result_tabs = st.tabs(output_structure)
                
                for i, (tab, structure_name) in enumerate(zip(result_tabs, output_structure)):
                    with tab:
                        st.markdown(f"### {structure_name}")
                        st.markdown(parsed_results.get(structure_name, "결과를 찾을 수 없습니다."))
            else:
                # output_structure가 없는 경우 기본 expander 사용
                with st.expander(f"📋 {current_block['title']} - 분석 결과", expanded=True):
                    st.markdown(step_result)
            
            # 컨트롤 버튼들
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔄 다시 분석", key=f"reanalyze_{current_step_id}_{current_step_index}"):
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
                                
                                save_step_result(current_step_id, new_result)
                                st.success("✅ 재분석 완료!")
                                st.rerun()
                            else:
                                st.error("❌ 재분석 실패")
                    except Exception as e:
                        st.error(f"❌ 재분석 오류: {e}")
            
            with col2:
                if st.button("💬 피드백", key=f"feedback_{current_step_id}_{current_step_index}"):
                    st.session_state.show_feedback = True
                    st.rerun()
            
            with col3:
                if current_step_index > 0:
                    if st.button("⬅️ 이전 단계", key=f"prev_{current_step_id}_{current_step_index}"):
                        st.session_state.current_step_index = current_step_index - 1
                        st.rerun()
            
            with col4:
                if current_step_index < len(ordered_blocks) - 1:
                    if st.button("➡️ 다음 단계", key=f"next_{current_step_id}_{current_step_index}"):
                        st.session_state.current_step_index = current_step_index + 1
                        st.rerun()
                else:
                    if st.button("🏁 완료", key=f"finish_{current_step_id}_{current_step_index}"):
                        st.success("모든 분석이 완료되었습니다!")
                        st.session_state.analysis_completed = True
            
            # 피드백 입력 (필요시)
            if st.session_state.get('show_feedback', False):
                with st.expander("💬 피드백 입력", expanded=True):
                    feedback_text = st.text_area(
                        f"{current_block['title']} 분석 결과에 대한 피드백을 입력하세요:",
                        key=f"feedback_input_{current_step_id}_{current_step_index}"
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📤 피드백 전송", key=f"send_feedback_{current_step_id}_{current_step_index}"):
                            st.success("피드백이 전송되었습니다!")
                            st.session_state.show_feedback = False
                            st.rerun()
                    
                    with col2:
                        if st.button("❌ 취소", key=f"cancel_feedback_{current_step_id}_{current_step_index}"):
                            st.session_state.show_feedback = False
                            st.rerun()
    
    else:
        st.success("모든 분석이 완료되었습니다!")
        if st.button("📊 결과 보고서 생성"):
            st.info("보고서 생성 기능은 별도로 구현됩니다.")

def render_sidebar_all_steps(workflow: AnalysisWorkflow = None):
    """사이드바에 전체 분석 단계 표시 (통합)"""
    st.sidebar.markdown("### 📋 전체 분석 단계")
    
    # AnalysisSystem 초기화
    system = AnalysisSystem()
    
    # 현재 워크플로우에 있는 단계들의 ID 목록
    current_step_ids = set()
    if workflow:
        all_steps = workflow.steps + workflow.custom_steps
        current_step_ids = {step.id for step in all_steps}
    
    # 1. 필수 단계들 표시
    st.sidebar.markdown("#### 🔴 필수 단계")
    for step in system.required_steps:
        if step.id in current_step_ids:
            st.sidebar.markdown(f"~~{step.title}~~ *(선택됨)*")
        else:
            if st.sidebar.button(f"➕ {step.title}", key=f"add_required_{step.id}"):
                if workflow:
                    workflow.steps.append(step)
                    # 세션 상태 업데이트
                    st.session_state.workflow_steps = workflow.steps + workflow.custom_steps
                    st.session_state.current_workflow = workflow
                    st.sidebar.success(f"'{step.title}' 추가됨!")
                    st.rerun()
                else:
                    st.sidebar.error("워크플로우가 준비되지 않았습니다.")
    
    # 2. 권장 단계들 표시 (목적별로 그룹화)
    st.sidebar.markdown("#### 🟡 권장 단계")
    for objective, steps in system.recommended_steps.items():
        st.sidebar.markdown(f"**{objective.value}:**")
        for step in steps:
            if step.id in current_step_ids:
                st.sidebar.markdown(f"~~{step.title}~~ *(선택됨)*")
            else:
                if st.sidebar.button(f"➕ {step.title}", key=f"add_recommended_{step.id}"):
                    if workflow:
                        workflow.steps.append(step)
                        # 세션 상태 업데이트
                        st.session_state.workflow_steps = workflow.steps + workflow.custom_steps
                        st.session_state.current_workflow = workflow
                        st.sidebar.success(f"'{step.title}' 추가됨!")
                        st.rerun()
                    else:
                        st.sidebar.error("워크플로우가 준비되지 않았습니다.")
    
    # 3. 선택 단계들 표시
    st.sidebar.markdown("#### 🟢 선택 단계")
    for step in system.optional_steps:
        if step.id in current_step_ids:
            st.sidebar.markdown(f"~~{step.title}~~ *(선택됨)*")
        else:
            if st.sidebar.button(f"➕ {step.title}", key=f"add_optional_{step.id}"):
                if workflow:
                    workflow.custom_steps.append(step)
                    # 세션 상태 업데이트
                    st.session_state.workflow_steps = workflow.steps + workflow.custom_steps
                    st.session_state.current_workflow = workflow
                    st.sidebar.success(f"'{step.title}' 추가됨!")
                    st.rerun()
                else:
                    st.sidebar.error("워크플로우가 준비되지 않았습니다.")
    
    # 4. 추가 선택 단계들 (prompt_loader에서)
    try:
        from prompt_loader import load_prompt_blocks
        blocks = load_prompt_blocks()
        extra_blocks = blocks.get("extra", [])
        
        if extra_blocks:
            st.sidebar.markdown("#### 🔵 추가 단계")
            for block in extra_blocks:
                block_id = block["id"]
                if block_id in current_step_ids:
                    st.sidebar.markdown(f"~~{block['title']}~~ *(선택됨)*")
                else:
                    if st.sidebar.button(f"➕ {block['title']}", key=f"add_extra_{block_id}"):
                        if workflow:
                            from analysis_system import AnalysisStep
                            new_step = AnalysisStep(
                                id=block_id,
                                title=block['title'],
                                description=block.get('description', ''),
                                is_optional=True,
                                order=len(workflow.steps) + len(workflow.custom_steps) + 1,
                                category=block.get('category', '추가')
                            )
                            workflow.custom_steps.append(new_step)
                            # 세션 상태 업데이트
                            st.session_state.workflow_steps = workflow.steps + workflow.custom_steps
                            st.session_state.current_workflow = workflow
                            st.sidebar.success(f"'{block['title']}' 추가됨!")
                            st.rerun()
                        else:
                            st.sidebar.error("워크플로우가 준비되지 않았습니다.")
    except Exception as e:
        st.sidebar.error(f"추가 단계 로드 오류: {e}")

def render_analysis_workflow():
    """분석 워크플로우 렌더링"""
    st.header("🔍 분석 워크플로우")
    
    # 사이드바에 전체 상태 정보 추가
    st.sidebar.markdown("### 📊 전체 상태")
    st.sidebar.write(f"워크플로우 단계: {len(st.session_state.get('workflow_steps', []))}")
    st.sidebar.write(f"현재 단계 인덱스: {st.session_state.get('current_step_index', 'N/A')}")
    st.sidebar.write(f"완료된 단계: {len(st.session_state.get('cot_history', []))}")
    st.sidebar.write(f"편집 가능한 단계: {len(st.session_state.get('editable_steps', []))}")
    
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
            " 분석 목적 선택 (복수 선택 가능)",
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
            
            # 편집 가능한 단계 리스트 초기화
            if 'editable_steps' not in st.session_state:
                st.session_state.editable_steps = workflow.steps.copy()
            
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
            if st.button(" 분석 시작", key="start_analysis_workflow"):
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
                st.session_state.current_step_index = 0
                st.session_state.cot_history = []
                st.session_state.workflow_steps = st.session_state.editable_steps
                st.session_state.current_step_outputs = {}
                
                # 디버깅 정보 추가
                st.success("✅ 분석이 시작되었습니다!")
                st.info(f"📋 총 {len(st.session_state.workflow_steps)}개 단계가 설정되었습니다.")
                st.info(f"🔍 첫 번째 단계: {st.session_state.workflow_steps[0].title}")
                
                # 사이드바에 상태 표시
                st.sidebar.success("✅ 분석 시작됨")
                st.sidebar.write(f"총 단계: {len(st.session_state.workflow_steps)}")
                st.sidebar.write(f"현재 단계: 0")
                st.sidebar.write(f"첫 번째 단계: {st.session_state.workflow_steps[0].title}")
                
                st.rerun()
    
    # 3단계: 단계별 분석 진행
    if st.session_state.get('workflow_steps') and len(st.session_state.workflow_steps) > 0:
        st.subheader("📋 3단계: 단계별 분석 진행")
        
        workflow_steps = st.session_state.workflow_steps
        current_step_index = st.session_state.get('current_step_index', 0)
        
        # 디버깅 정보 추가
        st.sidebar.markdown("### 🔍 디버깅 정보")
        st.sidebar.write(f"워크플로우 단계 존재: ✅")
        st.sidebar.write(f"현재 단계 인덱스: {current_step_index}")
        st.sidebar.write(f"총 단계 수: {len(workflow_steps)}")
        st.sidebar.write(f"완료된 단계 수: {len(st.session_state.cot_history)}")
        
        if current_step_index < len(workflow_steps):
            current_step = workflow_steps[current_step_index]
            st.sidebar.write(f"현재 단계: {current_step.title}")
            st.sidebar.write(f"분석 완료 상태: {st.session_state.get('current_step_outputs', {}).get('saved', False)}")
            
            st.markdown(f"### 🔍 현재 단계: {current_step.title}")
            st.info(f"설명: {current_step.description}")
            
            # 이전 단계 결과들
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
            
            # PDF 요약을 딕셔너리 형태로 변환
            pdf_summary = st.session_state.get('pdf_summary', '')
            pdf_summary_dict = {
                "pdf_summary": pdf_summary,
                "project_name": user_inputs.get("project_name", ""),
                "owner": user_inputs.get("owner", ""),
                "site_location": user_inputs.get("site_location", ""),
                "site_area": user_inputs.get("site_area", ""),
                "building_type": user_inputs.get("building_type", ""),
                "project_goal": user_inputs.get("project_goal", "")
            }
            
            # 현재 단계에 해당하는 프롬프트 블록 찾기
            from prompt_loader import load_prompt_blocks
            blocks = load_prompt_blocks()
            extra_blocks = blocks["extra"]
            
            # 현재 단계 ID에 해당하는 블록 찾기
            current_block = None
            for block in extra_blocks:
                if block["id"] == current_step.id:
                    current_block = block
                    break
            
            if current_block:
                # 분석 실행 버튼
                if st.button(f"🔍 {current_step.title} 분석 실행", key=f"analyze_{current_step.id}"):
                    with st.spinner(f"{current_step.title} 분석 중..."):
                        # 통합 프롬프트 생성
                        from dsl_to_prompt import convert_dsl_to_prompt
                        base_prompt = convert_dsl_to_prompt(current_block["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                        
                        # output_structure에 따라 분석 실행
                        results = {}
                        output_structure = current_block["content_dsl"].get("output_structure", [])
                        
                        if output_structure:
                            # output_structure에 따라 순차 실행
                            for i, structure in enumerate(output_structure):
                                if i == 0:
                                    from dsl_to_prompt import prompt_requirement_table
                                    from agent_executor import run_requirement_table
                                    prompt = prompt_requirement_table(current_block["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                                    results[f"result_{i}"] = run_requirement_table(prompt)
                                    time.sleep(2)  # 2초 대기
                                elif i == 1:
                                    from dsl_to_prompt import prompt_ai_reasoning
                                    from agent_executor import run_ai_reasoning
                                    prompt = prompt_ai_reasoning(current_block["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                                    results[f"result_{i}"] = run_ai_reasoning(prompt)
                                    time.sleep(2)  # 2초 대기
                                elif i == 2:
                                    from dsl_to_prompt import prompt_precedent_comparison
                                    from agent_executor import run_precedent_comparison
                                    prompt = prompt_precedent_comparison(current_block["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                                    results[f"result_{i}"] = run_precedent_comparison(prompt)
                                    time.sleep(2)  # 2초 대기
                                elif i == 3:
                                    from dsl_to_prompt import prompt_strategy_recommendation
                                    from agent_executor import run_strategy_recommendation
                                    prompt = prompt_strategy_recommendation(current_block["content_dsl"], user_inputs, prev, pdf_summary_dict, site_fields)
                                    results[f"result_{i}"] = run_strategy_recommendation(prompt)
                                    time.sleep(2)  # 2초 대기
                        else:
                            # 기본 4개 분석 (fallback)
                            from agent_executor import run_requirement_table, run_ai_reasoning, run_precedent_comparison, run_strategy_recommendation
                            prompt_req = base_prompt + "\n\n⚠️ 반드시 '요구사항 정리표' 항목만 표로 생성. 그 외 항목은 출력하지 마세요."
                            results["requirement_table"] = run_requirement_table(prompt_req)
                            
                            prompt_reason = base_prompt + "\n\n⚠️ 반드시 'AI reasoning' 항목(Chain-of-Thought 논리 해설)만 생성. 그 외 항목은 출력하지 마세요."
                            results["ai_reasoning"] = run_ai_reasoning(prompt_reason)
                            
                            prompt_precedent = base_prompt + "\n\n⚠️ 반드시 '유사 사례 비교' 표 또는 비교 해설만 출력. 그 외 항목은 출력하지 마세요."
                            results["precedent_comparison"] = run_precedent_comparison(prompt_precedent)
                            
                            prompt_strategy = base_prompt + "\n\n⚠️ 반드시 '전략적 제언 및 시사점'만 출력. 그 외 항목은 출력하지 마세요."
                            results["strategy_recommendation"] = run_strategy_recommendation(prompt_strategy)
                        
                        # 결과를 session_state에 저장
                        st.session_state.current_step_outputs = results
                        st.session_state.current_step_outputs["saved"] = True
                        
                        # output_structure에 따라 탭으로 결과 표시
                        st.markdown(f"### 📋 {current_step.title} 분석 결과")
                        
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
                                if "requirement_table" in results:
                                    st.markdown(results["requirement_table"])
                            
                            with tab2:
                                st.markdown("#### 🧠 AI 추론 해설")
                                if "ai_reasoning" in results:
                                    st.markdown(results["ai_reasoning"])
                            
                            with tab3:
                                st.markdown("#### 🧾 유사 사례 비교")
                                if "precedent_comparison" in results:
                                    st.markdown(results["precedent_comparison"])
                            
                            with tab4:
                                st.markdown("#### ✅ 전략적 제언 및 시사점")
                                if "strategy_recommendation" in results:
                                    st.markdown(results["strategy_recommendation"])
                        
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
                        
                        # 결과를 히스토리에 저장
                        from user_state import save_step_result, append_step_history
                        from utils import extract_summary, extract_insight
                        
                        st.session_state.cot_history.append({
                            "step": current_step.title,
                            "result": full_result,
                            "summary": extract_summary(full_result),
                            "insight": extract_insight(full_result)
                        })
                        
                        save_step_result(current_step.id, full_result)
                        append_step_history(
                            step_id=current_step.id,
                            title=current_step.title,
                            prompt="통합 분석",
                            result=full_result
                        )
                        
                        st.success("✅ 분석이 완료되었습니다!")
                
                # 진행 상황 표시 (분석 완료 후)
                if st.session_state.get('current_step_outputs', {}).get("saved"):
                    st.info("✅ 이 단계의 분석이 완료되었습니다.")
                    
                    # 피드백 시스템 추가
                    st.markdown("---")
                    st.markdown("### 💬 분석 결과 피드백 및 수정")
                    
                    # 피드백 입력
                    feedback_input = st.text_area(
                        "분석 결과에 대한 피드백이나 수정 요청을 입력하세요:",
                        placeholder="예: 이 부분을 더 자세히 분석해주세요, 다른 관점도 제시해주세요, 표 구조를 바꿔주세요 등",
                        key=f"feedback_input_{current_step.id}"
                    )
                    
                    feedback_type = st.selectbox(
                        "피드백 유형:",
                        FEEDBACK_TYPES,
                        key=f"feedback_type_{current_step.id}"
                    )
                    
                    if st.button("💬 피드백 제출", key=f"submit_feedback_{current_step.id}"):
                        if feedback_input.strip():
                            with st.spinner("피드백을 처리하고 있습니다..."):
                                try:
                                    # 피드백 처리 프롬프트 생성
                                    current_results = st.session_state.current_step_outputs
                                    original_result = current_results.get("original_result", "")
                                    if not original_result:
                                        # 원본 결과가 없으면 현재 결과를 원본으로 저장
                                        original_result = "\n\n".join([
                                            f"**{key}**: {value}" 
                                            for key, value in current_results.items() 
                                            if key != "saved" and key != "original_result" and key != "updated_result" and key != "feedback_applied"
                                        ])
                                        st.session_state.current_step_outputs["original_result"] = original_result
                                    
                                    feedback_prompt = f"""
기존 분석 결과:
{original_result}

사용자 피드백:
- 유형: {feedback_type}
- 내용: {feedback_input}

위 피드백을 바탕으로 기존 분석 결과를 수정하거나 보완해주세요.
피드백의 의도를 정확히 파악하여 적절한 수정을 제시해주세요.

요청사항:
1. 기존 분석 결과를 바탕으로 사용자의 피드백을 반영한 수정된 분석을 제공해주세요.
2. 피드백 유형에 따라 적절한 수정 방향을 제시해주세요:
   - 추가 분석 요청: 더 자세한 분석이나 새로운 관점 추가
   - 수정 요청: 기존 내용의 오류나 부족한 부분 수정
   - 다른 관점 제시: 새로운 시각이나 접근 방법 제시
   - 구조 변경: 분석 구조나 형식의 변경
   - 기타: 특별한 요청사항에 따른 맞춤형 수정
3. 수정된 결과는 기존 분석의 맥락을 유지하면서 피드백을 반영한 형태로 제공해주세요.
"""
                                    
                                    # 피드백 처리 실행
                                    from agent_executor import execute_agent
                                    updated_result = execute_agent(feedback_prompt)
                                    
                                    # 업데이트된 결과 저장
                                    st.session_state.current_step_outputs["updated_result"] = updated_result
                                    st.session_state.current_step_outputs["feedback_applied"] = True
                                    
                                    # 피드백 히스토리에 추가
                                    if "feedback_history" not in st.session_state:
                                        st.session_state.feedback_history = []
                                    
                                    st.session_state.feedback_history.append({
                                        "step": current_step.title,
                                        "feedback_type": feedback_type,
                                        "feedback_content": feedback_input,
                                        "ai_response": updated_result,
                                        "timestamp": time.time()
                                    })
                                    
                                    # cot_history 업데이트 (마지막 항목을 업데이트된 결과로 교체)
                                    if st.session_state.cot_history:
                                        st.session_state.cot_history[-1]["result"] = updated_result
                                        # utils에서 함수들을 안전하게 import하여 사용
                                        try:
                                            from utils import extract_summary, extract_insight
                                            st.session_state.cot_history[-1]["summary"] = extract_summary(updated_result)
                                            st.session_state.cot_history[-1]["insight"] = extract_insight(updated_result)
                                        except Exception as summary_error:
                                            st.warning(f"⚠️ 요약 생성 중 오류: {summary_error}")
                                            st.session_state.cot_history[-1]["summary"] = updated_result[:300] + "..."
                                            st.session_state.cot_history[-1]["insight"] = "요약 생성 실패"
                                    
                                    st.success("✅ 피드백이 처리되었습니다!")
                                    st.info(" 피드백이 적용된 결과가 아래에 표시됩니다.")
                                    
                                    # 피드백 적용된 결과 즉시 표시
                                    st.markdown("#### ✨ 피드백 적용된 결과")
                                    st.markdown(updated_result)
                                    
                                except Exception as e:
                                    st.error(f"❌ 피드백 처리 중 오류가 발생했습니다: {e}")
                                    st.error("오류 상세 정보:")
                                    st.error(f"- 함수: execute_agent")
                                    st.error(f"- 매개변수: {len(feedback_prompt)} 문자")
                                    st.error(f"- 피드백 유형: {feedback_type}")
                                    st.error(f"- 피드백 내용: {feedback_input[:100]}...")
                                    st.error(f"- 오류 타입: {type(e).__name__}")
                                    st.error(f"- 오류 위치: {e.__traceback__.tb_lineno if hasattr(e, '__traceback__') else 'N/A'}")
                        else:
                            st.warning("⚠️ 피드백 내용을 입력해주세요.")
                    
                    # 피드백 히스토리 표시
                    if st.session_state.get("feedback_history"):
                        st.markdown("#### 📋 피드백 히스토리")
                        for i, feedback in enumerate(st.session_state.feedback_history[-3:], 1):  # 최근 3개만 표시
                            with st.expander(f"피드백 {i}: {feedback['feedback_type']}", expanded=False):
                                st.markdown(f"**피드백**: {feedback['feedback_content']}")
                                st.markdown(f"**AI 응답**: {feedback['ai_response'][:300]}...")
                    
                    # 다시 분석 버튼 (원본 결과로 되돌리기)
                    if st.session_state.get('current_step_outputs', {}).get("feedback_applied"):
                        if st.button("🔄 원본 결과로 되돌리기", key=f"revert_original_{current_step.id}"):
                            st.session_state.current_step_outputs["feedback_applied"] = False
                            if st.session_state.cot_history:
                                # 원본 결과로 되돌리기
                                original_result = st.session_state.current_step_outputs.get("original_result", "")
                                if original_result:
                                    try:
                                        from utils import extract_summary, extract_insight
                                        st.session_state.cot_history[-1]["result"] = original_result
                                        st.session_state.cot_history[-1]["summary"] = extract_summary(original_result)
                                        st.session_state.cot_history[-1]["insight"] = extract_insight(original_result)
                                    except Exception as summary_error:
                                        st.warning(f"⚠️ 원본 요약 생성 중 오류: {summary_error}")
                                        st.session_state.cot_history[-1]["result"] = original_result
                                        st.session_state.cot_history[-1]["summary"] = original_result[:300] + "..."
                                        st.session_state.cot_history[-1]["insight"] = "원본 요약 생성 실패"
                            st.rerun()
                    
                    # 다음 단계 버튼 추가
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("🔄 다시 분석", key=f"reanalyze_{current_step.id}_completed"):
                            st.rerun()
                    
                    with col2:
                        if current_step_index < len(workflow_steps) - 1:
                            if st.button("➡️ 다음 단계", key=f"next_{current_step.id}_completed"):
                                st.session_state.current_step_index = current_step_index + 1
                                # 다음 단계를 위해 current_step_outputs 초기화
                                st.session_state.current_step_outputs = {}
                                st.rerun()
                        else:
                            if st.button("🏁 분석 완료", key=f"finish_{current_step.id}_completed"):
                                st.session_state.current_step_index = current_step_index + 1
                                st.rerun()
                    
                    # 완료된 단계들 표시 (피드백 적용 상태 포함)
                    if st.session_state.cot_history:
                        st.markdown("### 📋 완료된 단계들")
                        for i, history in enumerate(st.session_state.cot_history):
                            # 피드백 적용 여부 확인
                            feedback_applied = st.session_state.get('current_step_outputs', {}).get("feedback_applied", False)
                            step_title = f"✅ {i+1}. {history['step']}"
                            if feedback_applied and i == len(st.session_state.cot_history) - 1:
                                step_title += " (피드백 적용됨)"
                            
                            with st.expander(step_title, expanded=False):
                                st.markdown(f"**요약**: {history.get('summary', '')}")
                                st.markdown(f"**인사이트**: {history.get('insight', '')}")
                                st.markdown("---")
                                
                                # 피드백이 적용된 경우 원본과 업데이트된 결과 모두 표시
                                if feedback_applied and i == len(st.session_state.cot_history) - 1:
                                    st.markdown("#### 📝 원본 결과")
                                    original_result = st.session_state.current_step_outputs.get("original_result", "")
                                    st.markdown(original_result[:500] + ("..." if len(original_result) > 500 else ""))
                                    st.markdown("---")
                                    st.markdown("#### ✨ 피드백 적용된 결과")
                                    updated_result = st.session_state.current_step_outputs.get("updated_result", "")
                                    st.markdown(updated_result[:500] + ("..." if len(updated_result) > 500 else ""))
                                else:
                                    st.markdown(history.get('result', '')[:500] + ("..." if len(history.get('result', '')) > 500 else ""))
                else:
                    st.info("💡 위의 '분석 실행' 버튼을 클릭하여 분석을 시작하세요.")
        
        # 다음 단계 안내
        if current_step_index < len(workflow_steps) - 1:
            next_step = workflow_steps[current_step_index + 1]
            st.info(f"다음 단계: {next_step.title}")
        else:
            st.success("🎉 모든 분석이 완료되었습니다!")

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
                
                # 분석 결과 요약
                analysis_summary = "\n\n".join([
                    f"**{h['step']}**: {h.get('summary', '')}"
                    for h in st.session_state.cot_history
                ])
                
                # 매스별 최적화 조건 분석 프롬프트 생성
                optimization_prompt = f"""
프로젝트 정보:
- 프로젝트명: {user_inputs.get('project_name', '')}
- 건물 유형: {user_inputs.get('building_type', '')}
- 대지 위치: {user_inputs.get('site_location', '')}
- 건축주: {user_inputs.get('owner', '')}
- 대지 면적: {user_inputs.get('site_area', '')}
- 프로젝트 목표: {user_inputs.get('project_goal', '')}

기존 분석 결과:
{analysis_summary}

위 정보를 바탕으로 매스별 최적화 조건을 자동으로 분석해주세요.

분석 요청사항:
1. **매스별 중요 프로그램 식별**: 각 매스에서 어떤 프로그램이 가장 중요한지 분석
2. **매스별 최적화 조건**: 각 매스의 특성에 따른 최적화 조건 제시
3. **프로그램별 우선순위**: 매스 내에서 프로그램들의 우선순위 분석

각 매스별로 다음 항목들을 분석해주세요:

1. **인지성**: 외부 인식, 동선 유도
2. **프라이버시**: 외부 시야 차단 필요성
3. **프로그램 연계 필요성**: 다른 공간과의 인접 배치 필요성
4. **보안성**: 출입구·코어·방문자 제어
5. **조망/채광 민감도**: 전망 확보, 자연광 필요 여부
6. **향후 확장 가능성**: 평면 또는 프로그램 확장 가능성
7. **동선 분리성**: 방문객 vs 연수생 vs 운영자
8. **구조적 유연성**: 스팬, 기둥 배치, 무주공간 등 구조 제약 수준
9. **이용 시간대 특성**: 주간/야간 사용 구분, 겹침 여부
10. **대지 조건 연계성**: 경사, 조망, 레벨차 등 대지와의 물리적 적합성

각 항목에 대해 다음을 포함해주세요:
- 목적 (purpose)
- 중요도 (importance: 높음/중간/낮음)
- 고려사항 (considerations)
- 해당 매스에서의 특별한 고려사항
"""
                
                # 최적화 조건 분석 실행 (API 연결)
                from agent_executor import execute_agent
                optimization_result = execute_agent(optimization_prompt)
                
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
                    label="�� 매스별 최적화 조건 분석 결과 다운로드",
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
    """분석 결과를 output_structure에 맞게 파싱"""
    parsed_results = {}
    
    # 각 구조별로 결과에서 해당 부분 추출
    for structure in output_structure:
        # 구조명을 키워드로 사용하여 결과에서 해당 부분 찾기
        if structure in result:
            # 구조명 이후부터 다음 구조명 이전까지 추출
            start_idx = result.find(structure)
            if start_idx != -1:
                # 다음 구조명 찾기
                next_structure = None
                for next_struct in output_structure:
                    if next_struct != structure:
                        next_idx = result.find(next_struct, start_idx + len(structure))
                        if next_idx != -1:
                            if next_structure is None or next_idx < next_structure[1]:
                                next_structure = (next_struct, next_idx)
                
                if next_structure:
                    end_idx = next_structure[1]
                else:
                    end_idx = len(result)
                
                parsed_results[structure] = result[start_idx:end_idx].strip()
            else:
                parsed_results[structure] = "해당 구조의 결과를 찾을 수 없습니다."
        else:
            # 구조명이 직접 포함되지 않은 경우 전체 결과 사용
            parsed_results[structure] = result
    
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

def main():
    """메인 함수"""
    render_tabbed_interface()

if __name__ == "__main__":
    main() 