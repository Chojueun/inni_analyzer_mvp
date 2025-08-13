from utils_pdf import search_pdf_chunks  # 통합된 PDF 모듈 사용
from search_helper import search_web_serpapi  # 주석 해제

def get_web_search_for_block(block_id: str, user_inputs: dict) -> str:
    """각 블록별로 관련된 웹 검색 수행"""
    
    # 블록별 검색 쿼리 매핑
    search_queries = {
        "requirement_analysis": [
            f"{user_inputs.get('building_type', '건축')} 요구사항 분석 2024",
            f"{user_inputs.get('building_type', '건축')} 설계 가이드라인"
        ],
        "precedent_benchmarking": [
            f"{user_inputs.get('building_type', '건축')} 사례 2024",
            f"{user_inputs.get('building_type', '건축')} 벤치마킹"
        ],
        "design_trend_application": [
            "건축 디자인 트렌드 2024",
            "건축 기술 트렌드 2024"
        ],
        "cost_estimation": [
            "건축 공사비 트렌드 2024",
            "건축 원가 분석 2024"
        ],
        "legal_review": [
            "건축법 개정사항 2024",
            "건축 규제 변경사항 2024"
        ],
        "mass_strategy": [
            "건축 매스 전략 2024",
            "건축 설계 트렌드 2024"
        ],
        "operation_investment_analysis": [
            "건축 운영 효율성 2024",
            "건축 투자 분석 2024"
        ]
    }
    
    queries = search_queries.get(block_id, ["건축 분석 2024"])
    
    all_results = []
    for query in queries:
        try:
            result = search_web_serpapi(query)
            if result and result != "[검색 API 키 없음]":
                all_results.append(f"🔍 검색어: {query}\n{result}")
        except Exception as e:
            print(f"웹 검색 실패 ({query}): {e}")
    
    return "\n\n".join(all_results) if all_results else ""

def convert_dsl_to_prompt(
    dsl_block: dict,
    user_inputs: dict,
    previous_summary: str = "",
    pdf_summary: dict = None,
    site_fields: dict = None,
    include_web_search: bool = True
) -> str:
    """완전히 개선된 DSL을 프롬프트로 변환"""
    
    dsl = dsl_block.get("content_dsl", {})
    prompt_parts = []
    
    # 0. 블록 ID 및 제목 명시 (새로 추가)
    block_id = dsl_block.get("id", "")
    block_title = dsl_block.get("title", "")
    prompt_parts.append(f"# 🎯 현재 분석 블록\n")
    prompt_parts.append(f"**블록 ID:** {block_id}\n")
    prompt_parts.append(f"**블록 제목:** {block_title}\n")
    prompt_parts.append(f"**분석 목적:** 이 블록만의 고유한 분석을 수행하세요.\n\n")
    
    # 1. 기본 역할 및 목표
    prompt_parts.append(f"# 🎯 분석 목표\n{dsl.get('goal', '')}")
    prompt_parts.append(f"# 역할\n{dsl.get('role', '건축 분석 전문가')}")
    
    if dsl.get('context'):
        prompt_parts.append(f"# 📍 맥락\n{dsl['context']}")
    
    # 2. 분석 프레임워크
    framework = dsl.get('analysis_framework', {})
    if framework:
        framework_text = f"# 🔍 분석 프레임워크\n"
        framework_text += f"접근 방식: {framework.get('approach', '')}\n"
        framework_text += f"방법론: {framework.get('methodology', '')}\n"
        
        criteria = framework.get('criteria', [])
        if criteria:
            framework_text += f"\n평가 기준:\n"
            for i, criterion in enumerate(criteria, 1):
                framework_text += f"{i}. {criterion}\n"
        
        prompt_parts.append(framework_text)
    
    # 3. 작업 목록
    tasks = dsl.get('tasks', [])
    if tasks:
        tasks_text = f"# 📋 주요 분석 작업\n"
        for i, task in enumerate(tasks, 1):
            tasks_text += f"{i}. {task}\n"
        prompt_parts.append(tasks_text)
    
    # 4. 품질 기준
    quality = dsl.get('quality_standards', {})
    if quality:
        quality_text = f"# ⚠️ 품질 기준\n"
        
        constraints = quality.get('constraints', [])
        if constraints:
            quality_text += f"제약사항:\n"
            for constraint in constraints:
                quality_text += f"- {constraint}\n"
        
        required_phrases = quality.get('required_phrases', [])
        if required_phrases:
            quality_text += f"\n필수 포함 문구: {', '.join(required_phrases)}\n"
        
        validation_rules = quality.get('validation_rules', [])
        if validation_rules:
            quality_text += f"\n검증 규칙:\n"
            for rule in validation_rules:
                quality_text += f"- {rule}\n"
        
        prompt_parts.append(quality_text)
    
    # 5. 출력 형식
    presentation = dsl.get('presentation', {})
    if presentation:
        presentation_text = f"# 📋 출력 형식\n"
        presentation_text += f"언어 톤: {presentation.get('language_tone', '')}\n"
        presentation_text += f"형식: {presentation.get('target_format', '')}\n"
        
        visual_elements = presentation.get('visual_elements', [])
        if visual_elements:
            presentation_text += f"시각 요소: {', '.join(visual_elements)}\n"
        
        prompt_parts.append(presentation_text)
    
    # 6. 프로젝트 기본 정보
    project_info = f"# 📊 프로젝트 기본 정보\n"
    project_info += f"- 프로젝트명: {user_inputs.get('project_name', 'N/A')}\n"
    project_info += f"- 소유자: {user_inputs.get('owner', 'N/A')}\n"
    project_info += f"- 위치: {user_inputs.get('site_location', 'N/A')}\n"
    project_info += f"- 면적: {user_inputs.get('site_area', 'N/A')}\n"
    project_info += f"- 건물유형: {user_inputs.get('building_type', 'N/A')}\n"
    project_info += f"- 프로젝트 목표: {user_inputs.get('project_goal', 'N/A')}\n"
    prompt_parts.append(project_info)
    
    # 7. 사이트 분석 정보
    if site_fields:
        site_text = f"# 🏗️ 사이트 분석 정보\n"
        for key, value in site_fields.items():
            if value and str(value).strip():
                readable_key = key.replace('_', ' ').title()
                site_text += f"- {readable_key}: {value}\n"
        prompt_parts.append(site_text)
    
    # 8. 출력 구조 - 강화된 버전
    output_structure = dsl.get('output_structure', [])
    if output_structure:
        structure_text = f"# 📋 출력 구조\n"
        structure_text += f"**중요: 이 블록({block_title})의 고유한 분석만 수행하세요.**\n\n"
        structure_text += f"다음 구조로 분석 결과를 제공하세요. 각 구조는 반드시 지정된 형식으로 작성하세요:\n\n"
        
        for i, structure in enumerate(output_structure, 1):
            structure_text += f"## {i}. {structure}\n"
            structure_text += f"[{structure}에 해당하는 내용만 여기에 작성]\n\n"
        
        structure_text += f"⚠️ **중요 지시사항:**\n"
        structure_text += f"1. 각 구조는 반드시 '## 번호. 구조명' 형식으로 시작하세요\n"
        structure_text += f"2. 각 구조의 내용은 해당 구조에만 관련된 내용으로 작성하세요\n"
        structure_text += f"3. 모든 구조를 빠짐없이 작성하되, 내용이 중복되지 않도록 하세요\n"
        structure_text += f"4. 구조 간 구분을 명확히 하세요\n"
        structure_text += f"5. 각 구조는 독립적으로 완성된 내용이어야 합니다\n"
        structure_text += f"6. **이 블록의 고유한 분석만 수행하고, 다른 블록의 내용을 포함하지 마세요**\n\n"
        
        prompt_parts.append(structure_text)
    
    # 9. 이전 분석 결과
    if previous_summary:
        prompt_parts.append(f"# 📚 이전 분석 결과\n{previous_summary}\n")
    
    # 10. PDF 요약
    if pdf_summary:
        prompt_parts.append(f"# 📄 PDF 문서 요약\n{pdf_summary}\n")
    
    # 11. 웹 검색 결과
    if include_web_search:
        web_search_results = get_web_search_for_block(dsl_block.get("id", ""), user_inputs)
        if web_search_results:
            web_search_text = f"# 🌐 최신 웹 검색 결과\n{web_search_results}\n"
            prompt_parts.append(web_search_text)
    
    return "\n\n".join(prompt_parts)

# 단계별 특화된 프롬프트 함수들
def prompt_requirement_table(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    """요구사항 분석 프롬프트 (웹 검색 포함)"""
    base_prompt = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields, include_web_search=True)
    
    # 웹 검색 결과가 있으면 추가 지시사항
    if "🌐 최신 웹 검색 결과" in base_prompt:
        base_prompt += "\n\n⚠️ 위의 최신 웹 검색 결과를 참고하여 요구사항을 분석해주세요. 최신 트렌드와 가이드라인을 반영한 현실적인 요구사항을 제시해주세요."
    
    return base_prompt + "\n\n⚠️ 반드시 '요구사항 정리표' 항목만 표로 생성. 그 외 항목은 출력하지 마세요."

def prompt_ai_reasoning(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    base = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields)
    output_structure = dsl_block.get("content_dsl", {}).get("output_structure", [])
    
    if output_structure and len(output_structure) >= 2:
        target = output_structure[1]  # 두 번째 출력 구조
        return base + f"\n\n⚠️ 반드시 '{target}' 항목만 생성. 그 외 항목은 출력하지 마세요."
    else:
        return base + f"\n\n⚠️ 반드시 'AI 추론 해설' 항목만 생성. 그 외 항목은 출력하지 마세요."

def prompt_precedent_comparison(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    """사례 비교 프롬프트 (웹 검색 포함)"""
    base_prompt = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields, include_web_search=True)
    
    # 웹 검색 결과가 있으면 추가 지시사항
    if "🌐 최신 웹 검색 결과" in base_prompt:
        base_prompt += "\n\n⚠️ 위의 최신 웹 검색 결과에 포함된 사례들을 참고하여 비교 분석해주세요. 최신 사례와 트렌드를 반영한 비교를 제공해주세요."
    
    return base_prompt + "\n\n⚠️ 반드시 '유사 사례 비교' 표 또는 비교 해설만 출력. 그 외 항목은 출력하지 마세요."

def prompt_strategy_recommendation(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    """전략 제언 프롬프트 (웹 검색 포함)"""
    base_prompt = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields, include_web_search=True)
    
    # 웹 검색 결과가 있으면 추가 지시사항
    if "🌐 최신 웹 검색 결과" in base_prompt:
        base_prompt += "\n\n⚠️ 위의 최신 웹 검색 결과를 바탕으로 현실적이고 실행 가능한 전략을 제시해주세요. 최신 트렌드와 시장 동향을 반영한 전략적 제언을 해주세요."
    
    return base_prompt + "\n\n⚠️ 반드시 '전략적 제언 및 시사점'만 출력. 그 외 항목은 출력하지 마세요."

# prompt_claude_narrative 함수 제거 - workflow_ui.py에서 직접 처리
# prompt_midjourney_prompt 함수 제거 - workflow_ui.py에서 직접 처리
