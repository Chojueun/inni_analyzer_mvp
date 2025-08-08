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
from analysis_system import AnalysisSystem, AnalysisStep
from agent_executor import (
    run_requirement_table,
    run_ai_reasoning,
    run_precedent_comparison,
    run_strategy_recommendation,
)

def execute_claude_analysis(prompt, description):
    """Claude 분석 실행 함수 - agent_executor의 execute_agent 사용"""
    try:
        result = execute_agent(prompt)
        return result
    except Exception as e:
        st.error(f"분석 실행 오류: {e}")
        return f"{description} 분석 실패"

def render_analysis_workflow():
    """분석 워크플로우 렌더링"""
    st.header("🔍 분석 워크플로우")
    
    # 사용자 입력 가져오기
    user_inputs = get_user_inputs()
    
    # PDF 업로드 상태 확인
    uploaded_pdf = st.session_state.get('uploaded_pdf')
    
    # 1단계: 목적과 용도 선택
    st.subheader("📋 1단계: 분석 목적과 용도 선택")
    
    from analysis_system import AnalysisSystem, PurposeType, ObjectiveType
    system = AnalysisSystem()
    
    # 용도 선택
    purpose_options = [purpose.value for purpose in PurposeType]
    selected_purpose = st.selectbox(
        "🏗️ 건물 용도 선택",
        purpose_options,
        key="selected_purpose"
    )
    
    # 선택된 용도에 따른 목적 옵션 표시
    if selected_purpose:
        purpose_enum = PurposeType(selected_purpose)
        available_objectives = system.get_available_objectives(purpose_enum)
        objective_options = [obj.value for obj in available_objectives]
        
        selected_objectives = st.multiselect(
            " 분석 목적 선택 (복수 선택 가능)",
            objective_options,
            key="selected_objectives"
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
                        if st.button("❌ 제거", key=f"remove_{step.id}"):
                            st.session_state.editable_steps.pop(i)
                            st.rerun()
                    
                    with col_c:
                        if i > 0:
                            if st.button("⬆️ 위로", key=f"up_{step.id}"):
                                st.session_state.editable_steps[i], st.session_state.editable_steps[i-1] = \
                                    st.session_state.editable_steps[i-1], st.session_state.editable_steps[i]
                                st.rerun()
                        if i < len(st.session_state.editable_steps) - 1:
                            if st.button("⬇️ 아래로", key=f"down_{step.id}"):
                                st.session_state.editable_steps[i], st.session_state.editable_steps[i+1] = \
                                    st.session_state.editable_steps[i+1], st.session_state.editable_steps[i]
                                st.rerun()
            
            # 분석 시작 버튼
            if st.button("🚀 분석 시작", key="start_analysis"):
                # 필수 정보 확인
                missing_fields = []
                for field in ["project_name", "building_type", "site_location", "owner", "site_area", "project_goal"]:
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
                
                # 분석 단계 초기화 (current_step_index는 이미 설정되어 있으면 유지)
                if 'current_step_index' not in st.session_state:
                    st.session_state.current_step_index = 0
                st.session_state.cot_history = []
                st.session_state.workflow_steps = st.session_state.editable_steps
                st.success("✅ 분석이 시작되었습니다! 다음 단계로 진행하세요.")
                st.rerun()
    
    # 3단계: 단계별 분석 진행
    if st.session_state.get('workflow_steps'):
        st.subheader("📋 3단계: 단계별 분석 진행")
        
        workflow_steps = st.session_state.workflow_steps
        current_step_index = st.session_state.get('current_step_index', 0)
        
        # 디버깅 정보 추가
        st.sidebar.markdown("### 🔍 디버깅 정보")
        st.sidebar.write(f"현재 단계 인덱스: {current_step_index}")
        st.sidebar.write(f"총 단계 수: {len(workflow_steps)}")
        st.sidebar.write(f"완료된 단계 수: {len(st.session_state.cot_history)}")
        if current_step_index < len(workflow_steps):
            st.sidebar.write(f"현재 단계: {workflow_steps[current_step_index].title}")
        st.sidebar.write(f"분석 완료 상태: {st.session_state.get('current_step_outputs', {}).get('saved', False)}")
        
        if current_step_index < len(workflow_steps):
            current_step = workflow_steps[current_step_index]
            
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
                            tab1, tab2, tab3, tab4 = st.tabs(["📊 요구사항", "🧠 AI 추론", "🧾 사례비교", "✅ 전략제언"])
                            
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
                
                # 진행 상황 표시 (분석 완료 후) - 중복 버튼 제거
                if st.session_state.get('current_step_outputs', {}).get("saved"):
                    st.info("✅ 이 단계의 분석이 완료되었습니다.")
                    
                    # 다음 단계 버튼 추가 (분석 완료 후에도 표시)
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
                    
                    # 완료된 단계들 표시
                    if st.session_state.cot_history:
                        st.markdown("### 📋 완료된 단계들")
                        for i, history in enumerate(st.session_state.cot_history):
                            with st.expander(f"✅ {i+1}. {history['step']}", expanded=False):
                                st.markdown(f"**요약**: {history.get('summary', '')}")
                                st.markdown(f"**인사이트**: {history.get('insight', '')}")
                                st.markdown("---")
                                st.markdown(history.get('result', '')[:500] + ("..." if len(history.get('result', '')) > 500 else ""))
                else:
                    st.info("💡 위의 '분석 실행' 버튼을 클릭하여 분석을 시작하세요.")
            
            # 다음 단계 안내
            if current_step_index < len(workflow_steps) - 1:
                next_step = workflow_steps[current_step_index + 1]
                st.info(f"다음 단계: {next_step.title}")
            else:
                st.success(" 모든 분석이 완료되었습니다!")
                
                # 전체 누적 분석 결과 표시
                if st.session_state.cot_history:
                    st.markdown("### 📊 전체 누적 분석 결과")
                    
                    # 전체 결과를 탭으로 표시
                    result_tabs = st.tabs(["📋 전체 요약", "💡 핵심 인사이트", "📊 상세 결과"])
                    
                    with result_tabs[0]:
                        st.markdown("#### 📋 전체 분석 요약")
                        for i, history in enumerate(st.session_state.cot_history):
                            st.markdown(f"**{i+1}. {history['step']}**")
                            st.markdown(f"요약: {history.get('summary', '')}")
                            st.markdown("---")
                    
                    with result_tabs[1]:
                        st.markdown("#### 💡 핵심 인사이트")
                        for i, history in enumerate(st.session_state.cot_history):
                            st.markdown(f"**{i+1}. {history['step']}**")
                            st.markdown(f"인사이트: {history.get('insight', '')}")
                            st.markdown("---")
                    
                    with result_tabs[2]:
                        st.markdown("#### 📊 상세 분석 결과")
                        for i, history in enumerate(st.session_state.cot_history):
                            with st.expander(f"{i+1}. {history['step']}", expanded=False):
                                st.markdown(history.get('result', ''))
        
        # 전체 진행 상황 표시
        st.subheader(" 전체 진행 상황")
        total_steps = len(workflow_steps)
        completed_steps = len(st.session_state.cot_history)
        progress = completed_steps / total_steps if total_steps > 0 else 0
        
        st.progress(progress, text=f"진행률: {completed_steps}/{total_steps} 단계 완료")
        
        # 완료된 단계들 표시
        if st.session_state.cot_history:
            st.markdown("### ✅ 완료된 단계들")
            for i, history in enumerate(st.session_state.cot_history):
                st.markdown(f"**{i+1}. {history['step']}**")
                st.caption(f"요약: {history.get('summary', '')[:100]}...")

def render_optimization_tab():
    """최적화 조건 탭 렌더링"""
    st.header("🎯 최적화 조건 분석")
    
    # 분석 결과 확인
    if not st.session_state.get('cot_history'):
        st.warning("⚠️ 먼저 분석을 완료해주세요.")
        return
    
    st.info(" 분석 결과를 바탕으로 매스별 최적화 조건을 분석합니다.")
    
    # STEP 1: 최적화 조건 입력
    st.subheader("STEP 1: 최적화 조건 입력")
    
    # 최적화 조건 입력
    optimization_conditions = st.text_area(
        "최적화 조건",
        value=st.session_state.get('optimization_conditions', ''),
        placeholder="예: 예산 제약, 시간 제약, 특별한 요구사항 등",
        help="분석에 적용할 특별한 조건이나 제약사항을 입력하세요."
    )
    
    # 조건 저장
    st.session_state.optimization_conditions = optimization_conditions
    
    # STEP 2: 매스별 최적화 조건 분석 실행
    st.subheader("STEP 2: 매스별 최적화 조건 분석")
    
    if st.button("🚀 매스별 최적화 조건 분석 실행", type="primary"):
        with st.spinner("매스별 최적화 조건을 분석하고 있습니다..."):
            try:
                # 분석 결과 요약
                analysis_summary = "\n\n".join([
                    f"**{h['step']}**: {h.get('summary', '')}"
                    for h in st.session_state.cot_history
                ])
                
                # 매스별 최적화 조건 분석 프롬프트 생성
                optimization_prompt = f"""
프로젝트 정보:
- 프로젝트명: {st.session_state.get('project_name', '')}
- 건물 유형: {st.session_state.get('building_type', '')}
- 대지 위치: {st.session_state.get('site_location', '')}
- 건축주: {st.session_state.get('owner', '')}
- 대지 면적: {st.session_state.get('site_area', '')}

최적화 조건: {optimization_conditions}

기존 분석 결과:
{analysis_summary}

위 정보를 바탕으로 매스별 최적화 조건을 분석해주세요.

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
                        "project_name": st.session_state.get('project_name', ''),
                        "building_type": st.session_state.get('building_type', ''),
                        "site_location": st.session_state.get('site_location', ''),
                        "owner": st.session_state.get('owner', ''),
                        "site_area": st.session_state.get('site_area', '')
                    },
                    "optimization_conditions": optimization_conditions,
                    "analysis_result": optimization_result
                }
                
                # JSON 파일 다운로드 버튼
                st.download_button(
                    label="📄 매스별 최적화 조건 분석 결과 다운로드",
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
        for i, history in enumerate(st.session_state.cot_history):
            with st.expander(f"📋 {i+1}. {history['step']}", expanded=True):
                st.markdown(f"**요약:** {history.get('summary', '')}")
                st.markdown(f"**인사이트:** {history.get('insight', '')}")
                st.markdown("---")
                st.markdown(history.get('result', ''))
        
        # 보고서 생성 섹션 추가
        st.markdown("---")
        st.subheader("📄 보고서 생성")
        
        # 사용자 입력 가져오기
        from user_state import get_user_inputs
        user_inputs = get_user_inputs()
        
        # 분석 결과 수집
        analysis_results = []
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
        
        # 보고서 생성 옵션
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 🌐 웹페이지 생성")
            from webpage_generator import create_webpage_download_button
            create_webpage_download_button(analysis_results, project_info, show_warning=False)
        
        with col2:
            st.markdown("#### 📄 문서 보고서")
            report_type = st.selectbox(
                "보고서 유형",
                ["전체 분석 보고서", "요약 보고서", "전문가 보고서", "클라이언트 보고서"],
                key="report_type_analysis"
            )
            
            include_charts = st.checkbox("📊 차트 포함", value=True, key="charts_analysis")
            include_recommendations = st.checkbox("💡 권장사항 포함", value=True, key="recommendations_analysis")
            include_appendix = st.checkbox("📋 부록 포함", value=False, key="appendix_analysis")
            
            if st.button("📄 보고서 생성", type="primary", key="generate_report_analysis"):
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
        
        with col3:
            st.markdown("#### 📊 전체 분석 결과")
            if st.button("📊 전체 결과 보기", key="view_full_results"):
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
                    tab1, tab2, tab3, tab4 = st.tabs(["📊 요구사항", "🧠 AI 추론", "🧾 사례비교", "✅ 전략제언"])
                    
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
        st.info("📝 분석을 먼저 진행해주세요.")

def render_claude_narrative_tab():
    """Claude Narrative 탭 렌더링"""
    st.header("📝 건축설계 발표용 Narrative 생성 시스템")
    
    # 분석 결과 확인
    if not st.session_state.get('cot_history'):
        st.warning("⚠️ 먼저 분석을 완료해주세요.")
        return
    
    st.info("🎯 건축설계 발표용 Narrative를 생성합니다.")
    
    # STEP 1: 기본 정보 입력
    st.subheader("STEP 1: 기본 정보 입력")
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input("프로젝트명", value=st.session_state.get('project_name', ''))
        building_type = st.text_input("건물 유형", value=st.session_state.get('building_type', ''))
        site_location = st.text_input("대지 위치", value=st.session_state.get('site_location', ''))
    
    with col2:
        owner = st.text_input("건축주", value=st.session_state.get('owner', ''))
        site_area = st.text_input("대지 면적", value=st.session_state.get('site_area', ''))
        project_goal = st.text_area("프로젝트 목표", value=st.session_state.get('project_goal', ''))
    
    # STEP 2: Narrative 방향 설정
    st.subheader("STEP 2: Narrative 방향 설정")
    narrative_style = st.selectbox(
        "Narrative 스타일",
        ["기술적/객관적", "감성적/서술적", "비즈니스 중심", "혁신적/미래지향적"]
    )
    
    target_audience = st.multiselect(
        "대상 청중",
        ["건축주", "투자자", "정부기관", "일반 대중", "전문가", "학계"]
    )
    
    key_message = st.text_area("핵심 메시지", placeholder="이 프로젝트에서 가장 강조하고 싶은 메시지를 입력하세요.")
    
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
                
                # Narrative 생성 프롬프트
                narrative_prompt = f"""
프로젝트 정보:
- 프로젝트명: {project_name}
- 건물 유형: {building_type}
- 건축주: {owner}
- 대지 위치: {site_location}
- 대지 면적: {site_area}
- 프로젝트 목표: {project_goal}

Narrative 요구사항:
- 스타일: {narrative_style}
- 대상 청중: {', '.join(target_audience)}
- 핵심 메시지: {key_message}

분석 결과:
{analysis_summary}

위 정보를 바탕으로 건축설계 발표용 Narrative를 생성해주세요.
8개 섹션으로 구성하여 체계적이고 설득력 있는 Narrative를 작성해주세요.
"""
                
                # Claude API 호출
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
    
    # STEP 4: 피드백 및 수정 (향후 구현)
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
    """보고서 생성 탭 렌더링"""
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
    
    # 보고서 유형 선택
    report_type = st.selectbox(
        "보고서 유형",
        ["전체 분석 보고서", "요약 보고서", "전문가 보고서", "클라이언트 보고서"]
    )
    
    # 추가 옵션
    include_charts = st.checkbox("📊 차트 및 다이어그램 포함", value=True)
    include_recommendations = st.checkbox("💡 권장사항 포함", value=True)
    include_appendix = st.checkbox("📋 부록 포함", value=False)
    
    # 보고서 생성 버튼들
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 웹페이지 생성 및 다운로드
        st.markdown("#### 🌐 웹페이지 생성")
        from webpage_generator import create_webpage_download_button
        create_webpage_download_button(analysis_results, project_info, show_warning=False)
    
    with col2:
        # 전체 분석 보고서
        st.markdown("#### 📋 전체 분석 보고서")
        if st.button("📄 전체 보고서 생성", key="full_report_btn"):
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
                                st.markdown("| 항목 | 내용 | 비고 |")
                                st.markdown("|------|------|------|")
                                st.markdown("| 분석 단계 | " + history.get('step', f'단계 {j+1}') + " | |")
                                if history.get('summary'):
                                    st.markdown("| 요약 | " + history['summary'][:100] + "... | |")
                                if history.get('insight'):
                                    st.markdown("| 인사이트 | " + history['insight'][:100] + "... | |")
                            
                            elif "요약" in structure_name:
                                st.markdown("##### 📝 요약 내용")
                                if history.get('summary'):
                                    st.markdown(history['summary'])
                                else:
                                    st.markdown(history.get('result', '')[:500] + ("..." if len(history.get('result', '')) > 500 else ""))
                            
                            elif "다이어그램" in structure_name:
                                st.markdown("##### 🎨 구조 다이어그램")
                                st.info("분석 결과 구조 다이어그램이 여기에 표시됩니다.")
                                st.markdown("📊 " + history.get('step', f'단계 {j+1}') + " 분석 구조")
                            
                            elif "우선순위" in structure_name:
                                st.markdown("##### ⭐ 중요도별 우선순위")
                                st.markdown("1. **최우선**: " + history.get('step', f'단계 {j+1}') + " 핵심 내용")
                                if history.get('insight'):
                                    st.markdown("2. **고우선**: " + history['insight'][:100] + "...")
                                if history.get('summary'):
                                    st.markdown("3. **중우선**: " + history['summary'][:100] + "...")
                            
                            else:
                                # 기본 표시
                                st.markdown("##### 📋 분석 내용")
                                result_text = history.get('result', '')
                                st.write(result_text[:800] + ("..." if len(result_text) > 800 else ""))
                            
                            # 상세 내용 (접을 수 있는 형태)
                            with st.expander(f" {history.get('step', f'단계 {j+1}')} 상세 내용"):
                                st.write(history.get('result', ''))
                            
                            st.markdown("---")
            else:
                # 기본 탭 (output_structure가 없는 경우)
                result_tabs = st.tabs(["📋 상세 분석", "💡 핵심 인사이트", "📊 요약"])
                
                with result_tabs[0]:
                    # 각 단계별 결과를 구조화된 형태로 표시
                    for i, history in enumerate(st.session_state.cot_history):
                        st.markdown(f"###  단계 {i+1}: {history.get('step', f'단계 {i+1}')}")
                        
                        # 분석 개요
                        col1, col2 = st.columns(2)
                        with col1:
                            st.info(f"**분석 단계**: {history.get('step', f'단계 {i+1}')}")
                        with col2:
                            st.success("**분석 상태**: ✅ 완료")
                        
                        # 주요 내용
                        st.markdown("#### 🔍 주요 내용")
                        st.write(history.get('result', '')[:800] + ("..." if len(history.get('result', '')) > 800 else ""))
                        
                        # 상세 내용 (접을 수 있는 형태)
                        with st.expander(f" {history.get('step', f'단계 {i+1}')} 상세 내용"):
                            st.write(history.get('result', ''))
                        
                        st.markdown("---")
                
                with result_tabs[1]:
                    st.markdown("### 💡 전체 분석 핵심 인사이트")
                    st.success("🔍 모든 분석 단계에서 도출된 핵심 인사이트:")
                    
                    # 각 단계별 핵심 인사이트 요약
                    for i, history in enumerate(st.session_state.cot_history):
                        st.markdown(f"####  단계 {i+1}: {history.get('step', f'단계 {i+1}')}")
                        if history.get('insight'):
                            st.markdown(f"**핵심 인사이트**: {history['insight']}")
                        elif history.get('summary'):
                            st.markdown(f"**핵심 내용**: {history['summary'][:200]}{'...' if len(history['summary']) > 200 else ''}")
                        else:
                            st.markdown(f"**핵심 내용**: {history.get('result', '')[:200]}{'...' if len(history.get('result', '')) > 200 else ''}")
                        st.markdown("---")
                
                with result_tabs[2]:
                    st.markdown("### 📊 전체 분석 요약")
                    
                    # 전체 분석 개요
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"**총 분석 단계**: {len(st.session_state.cot_history)}개")
                    with col2:
                        st.success("**전체 분석 상태**: ✅ 완료")
                    
                    # 각 단계별 요약
                    for i, history in enumerate(st.session_state.cot_history):
                        st.markdown(f"**단계 {i+1}**: {history.get('step', f'단계 {i+1}')}")
                        if history.get('summary'):
                            st.markdown(f"**요약**: {history['summary'][:150]}{'...' if len(history['summary']) > 150 else ''}")
                        else:
                            st.markdown(f"**결과 요약**: {history.get('result', '')[:150]}{'...' if len(history.get('result', '')) > 150 else ''}")
                        st.markdown("---")
    
    with col3:
        # 기존 보고서 생성 기능
        st.markdown("#### 📄 문서 보고서")
        if st.button("📄 보고서 생성", type="primary"):
            with st.spinner("보고서를 생성하고 있습니다..."):
                try:
                    # 보고서 내용 생성
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

def generate_report_content(report_type, include_charts, include_recommendations, include_appendix):
    """보고서 내용 생성"""
    user_inputs = get_user_inputs()
    
    # 기본 정보
    report_content = f"""
# {user_inputs.get('project_name', '프로젝트')} 분석 보고서

## 📋 프로젝트 기본 정보
- **프로젝트명**: {user_inputs.get('project_name', 'N/A')}
- **건축주**: {user_inputs.get('owner', 'N/A')}
- **대지위치**: {user_inputs.get('site_location', 'N/A')}
- **대지면적**: {user_inputs.get('site_area', 'N/A')}
- **건물용도**: {user_inputs.get('building_type', 'N/A')}
- **프로젝트 목표**: {user_inputs.get('project_goal', 'N/A')}

## 📊 분석 결과
"""
    
    # 분석 결과 추가
    if st.session_state.get('cot_history'):
        for i, history in enumerate(st.session_state.cot_history, 1):
            report_content += f"""
### {i}. {history['step']}

**요약**: {history.get('summary', '')}

**인사이트**: {history.get('insight', '')}

**상세 분석**:
{history.get('result', '')}

---
"""
    
    # 추가 섹션들
    if include_charts:
        report_content += """
## 📊 차트 및 다이어그램
(차트 및 다이어그램이 여기에 포함됩니다)
"""
    
    if include_recommendations:
        report_content += """
## 💡 권장사항
분석 결과를 바탕으로 한 권장사항이 여기에 포함됩니다.
"""
    
    if include_appendix:
        report_content += """
## 📋 부록
추가 자료 및 참고문헌이 여기에 포함됩니다.
"""
    
    return report_content

def main():
    """메인 함수"""
    render_tabbed_interface()

if __name__ == "__main__":
    main() 