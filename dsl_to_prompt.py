from utils_pdf_vector import search_pdf_chunks  # 고급 버전으로 변경
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
    include_web_search: bool = True  # 웹 검색 포함 여부
) -> str:
    """최적화된 DSL을 프롬프트로 변환 (웹 검색 포함)"""
    
    dsl = dsl_block.get("content_dsl", {})
    prompt_parts = []
    
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
    
    # 7. 사이트 분석 정보 (site_fields 활용)
    if site_fields:
        site_text = f"# 🏗️ 사이트 분석 정보\n"
        for key, value in site_fields.items():
            if value and str(value).strip():  # 빈 값이 아닌 경우만
                # 키 이름을 더 읽기 쉽게 변환
                readable_key = key.replace('_', ' ').title()
                site_text += f"- {readable_key}: {value}\n"
        prompt_parts.append(site_text)
    
    # 8. 출력 구조
    output_structure = dsl.get('output_structure', [])
    if output_structure:
        structure_text = f"# 📋 출력 구조\n"
        for i, structure in enumerate(output_structure, 1):
            structure_text += f"{i}. {structure}\n"
        prompt_parts.append(structure_text)
    
    # 9. 이전 분석 결과 (있는 경우)
    if previous_summary:
        prompt_parts.append(f"# 📚 이전 분석 결과\n{previous_summary}\n")
    
    # 10. PDF 요약 (있는 경우)
    if pdf_summary:
        prompt_parts.append(f"# 📄 PDF 문서 요약\n{pdf_summary}\n")
    
    # 11. PDF 검색 결과 (기존 기능 유지)
    if dsl_block.get("search_source") == "pdf_vector_db":
        query_template = dsl_block.get("search_query_template", "주요 내용")
        query = query_template.format(**user_inputs)
        try:
            pdf_chunks = search_pdf_chunks(query, top_k=3)
            if pdf_chunks:
                prompt_parts.append(f"# PDF 문서 관련 정보\n{pdf_chunks}\n")
        except Exception as e:
            pass
    
    # 웹 검색 결과 추가 (새로 추가)
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

def prompt_claude_narrative(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    """건축설계 발표용 Narrative 생성 시스템 전용 프롬프트 생성"""
    base = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields)
    
    # Narrative 특화 프롬프트 추가
    narrative_prompt = """
### 🎭 건축설계 발표용 Narrative 생성 가이드라인

당신은 건축설계 발표 전문가로서 프로젝트의 스토리텔링과 내러티브를 창작하고 개발합니다.

**Narrative 생성 원칙:**
1. **감성적 연결**: 사용자의 감정적 울림을 자극하는 서술
2. **문화적 맥락**: 지역성과 문화적 특성을 반영
3. **사용자 중심**: 사용자 경험과 니즈에 집중
4. **미래 지향**: 지속가능하고 혁신적인 미래 비전 제시

**8단계 구조화된 Narrative 구성:**
1. **Part 1. 📋 프로젝트 기본 정보**: 프로젝트 정보 자동 정리
2. **Part 2. 🎯 Core Story: 완벽한 교집합의 발견**: 선택사항 반영한 핵심 스토리
3. **Part 3. 📍 땅이 주는 답**: Context-Driven 방식 적용
4. **Part 4. 🏢 발주처가 원하는 미래**: Vision 중심 구성
5. **Part 5. 💡 컨셉의 탄생**: 키워드 기반 전개
6. **Part 6. 🏛️ 교집합이 만든 건축적 해답**: 선택된 전개 방식 적용
7. **Part 7. 🎯 Winning Narrative 구성**: 선택된 톤과 스타일 적용
8. **Part 8. 🎯 결론: 완벽한 선택의 이유**: 최종 메시지 정리

**선택사항 반영 가이드:**
- 감성/논리 비율에 따른 톤 조정
- 서술 스타일과 키 메시지 방향 적용
- 건축적 가치 우선순위 반영
- 내러티브 전개 방식 적용
- 강조할 설계 요소 반영

**출력 요구사항:**
- 8단계 구조화된 Narrative 준수
- 선택된 방향성에 따른 일관성 있는 톤과 스타일
- 설득력 있고 감동적인 발표용 톤
- 프로젝트의 실제 조건과 연결
- 다양한 이해관계자 관점 포함
"""
    
    return base + narrative_prompt

def prompt_midjourney_prompt(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    """ArchiRender GPT 전용 프롬프트 생성"""
    base = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields)
    
    # ArchiRender GPT 특화 프롬프트 추가
    archirender_prompt = """
### 🎨 ArchiRender GPT - 건축 이미지 생성 가이드라인

당신은 건축 이미지 생성 전문가로서 설계 초기단계 시각화를 담당합니다.

**이미지 종류별 분석 항목 체계:**

**🏙 조감도 참조 항목:**
- 대지 위치, 대지 형상, 도로 조건, 코너 입지 여부
- 주변 시설, 경관 요소, 시간대 설정, 활동성 묘사

**🧱 입면도 참조 항목:**
- 파사드 구성, 층별 전시 요소 (조감도 항목 전체 포함)

**🖼 출력 이미지 종류:**
- 조감도 (Bird's-eye View)
- 입면도 (정면도, 배면도, 측면도)
- 사실적 CG 이미지 (원근 뷰 렌더링, 야간 조명, 도시 반사, 유리 외피, 쇼윈도우 강조 등)

**건축적 정확성과 시각적 임팩트 가이드라인:**
1. **건축적 정확성**: 실제 건축물의 구조와 형태를 정확히 반영
2. **시각적 임팩트**: 조형적 아름다움과 상징성을 강조
3. **환경적 맥락**: 주변 환경과의 조화로운 관계 표현
4. **기술적 완성도**: 고품질 렌더링과 사실적 표현

**Midjourney 최적화 키워드:**
- **스타일**: architectural photography, professional rendering, hyperrealistic
- **카메라**: wide angle, aerial view, close-up, interior shot
- **조명**: natural lighting, golden hour, dramatic shadows
- **품질**: high quality, detailed, 8k, professional
- **아트스타일**: architectural visualization, photorealistic, modern design

**프롬프트 구조:**
```
[이미지 종류] + [건축 스타일] + [공간 유형] + [재료/텍스처] + [조명/분위기] + [환경/맥락] + [기술적 키워드] + [이미지 비율]
```

**출력 요구사항:**
- 구체적이고 실행 가능한 Midjourney 프롬프트
- 이미지 비율과 조명 조건을 반드시 반영
- 건축적 정확성과 시각적 임팩트를 모두 갖춘 고품질 프롬프트
- 한글/영어 순으로 프롬프트 제공
- 프로젝트의 실제 조건과 일치
"""
    
    return base + archirender_prompt
