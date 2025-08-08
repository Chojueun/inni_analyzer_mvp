from utils_pdf_vector_simple import search_pdf_chunks
from search_helper import search_web_serpapi

def convert_dsl_to_prompt(
    dsl_block: dict,
    user_inputs: dict,
    previous_summary: str = "",
    pdf_summary: dict = None,
    site_fields: dict = None
) -> str:
    prompt = ""
    
    # 기본 정보
    goal = dsl_block.get("goal", "")
    role = dsl_block.get("role", "")
    tasks = dsl_block.get("tasks", [])
    language_tone = dsl_block.get("language_tone", "")
    target_format = dsl_block.get("target_format", "")
    required_phrases = dsl_block.get("required_phrases", [])
    constraints = dsl_block.get("constraints", [])
    output_structure = dsl_block.get("output_structure", [])
    
    # 기본 역할 정의
    prompt += f" 당신은 실제 건축 입찰/기획/심사 보고서를 작성하는 AI 분석가입니다.\n"
    prompt += f" 이 단계의 역할: {role}\n"
    prompt += f"\n아래 입력 정보를 바탕으로 **'{goal}'** 분석 보고서를 작성하세요.\n\n"
    
    # 프로젝트 기본 정보
    prompt += "### 📊 프로젝트 기본 정보\n"
    prompt += f"- 프로젝트명: {user_inputs.get('project_name', 'N/A')}\n"
    prompt += f"- 소유자: {user_inputs.get('owner', 'N/A')}\n"
    prompt += f"- 위치: {user_inputs.get('site_location', 'N/A')}\n"
    prompt += f"- 면적: {user_inputs.get('site_area', 'N/A')}\n"
    prompt += f"- 건물유형: {user_inputs.get('building_type', 'N/A')}\n"
    prompt += f"- 프로젝트 목표: {user_inputs.get('project_goal', 'N/A')}\n\n"
    
    # 분석 항목
    if tasks:
        prompt += "### 📂 주요 분석 항목\n"
        for i, task in enumerate(tasks, 1):
            prompt += f"{i}. {task}\n"
        prompt += "\n"
    
    # 출력 구조 (JSON에서 가져옴)
    if output_structure:
        prompt += "### 📋 출력 구조\n"
        for i, structure in enumerate(output_structure, 1):
            prompt += f"{i}. {structure}\n"
        prompt += "\n"
    
    # 제약사항 (JSON에서 가져옴)
    if constraints:
        prompt += "### ⚠️ 분석 제약사항\n"
        for constraint in constraints:
            prompt += f"- {constraint}\n"
        prompt += "\n"
    
    # 언어 톤 및 형식 (JSON에서 가져옴)
    if language_tone:
        prompt += f"### 📋 분석 스타일\n{language_tone}\n\n"
    
    if target_format:
        prompt += f"### 📋 출력 형식\n{target_format}\n\n"
    
    if required_phrases:
        prompt += f"### 📋 필수 포함 문구\n{', '.join(required_phrases)}\n\n"
    
    # PDF 검색 결과
    if dsl_block.get("search_source") == "pdf_vector_db":
        query_template = dsl_block.get("search_query_template", "주요 내용")
        query = query_template.format(**user_inputs)
        try:
            pdf_chunks = search_pdf_chunks(query, top_k=3)
            if pdf_chunks:
                prompt += f"###  PDF 문서 관련 정보\n{pdf_chunks}\n\n"
        except Exception as e:
            pass
    
    return prompt

# 단계별 특화된 프롬프트 함수들
def prompt_requirement_table(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    base = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields)
    output_structure = dsl_block.get("output_structure", [])
    
    if output_structure and len(output_structure) >= 1:
        target = output_structure[0]  # 첫 번째 출력 구조
        return base + f"\n\n⚠️ 반드시 '{target}' 항목만 생성. 그 외 항목은 출력하지 마세요."
    else:
        return base + "\n\n⚠️ 반드시 '요구사항 정리표' 항목만 표로 생성. 그 외 항목은 출력하지 마세요."

def prompt_ai_reasoning(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    base = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields)
    output_structure = dsl_block.get("output_structure", [])
    
    if output_structure and len(output_structure) >= 2:
        target = output_structure[1]  # 두 번째 출력 구조
        return base + f"\n\n⚠️ 반드시 '{target}' 항목만 생성. 그 외 항목은 출력하지 마세요."
    else:
        return base + "\n\n⚠️ 반드시 'AI reasoning' 항목(Chain-of-Thought 논리 해설)만 생성. 그 외 항목은 출력하지 마세요."

def prompt_precedent_comparison(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    base = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields)
    output_structure = dsl_block.get("output_structure", [])
    
    if output_structure and len(output_structure) >= 3:
        target = output_structure[2]  # 세 번째 출력 구조
        return base + f"\n\n⚠️ 반드시 '{target}' 항목만 출력. 그 외 항목은 출력하지 마세요."
    else:
        return base + "\n\n⚠️ 반드시 '유사 사례 비교' 표 또는 비교 해설만 출력. 그 외 항목은 출력하지 마세요."

def prompt_strategy_recommendation(dsl_block, user_inputs, previous_summary="", pdf_summary=None, site_fields=None):
    base = convert_dsl_to_prompt(dsl_block, user_inputs, previous_summary, pdf_summary, site_fields)
    output_structure = dsl_block.get("output_structure", [])
    
    if output_structure and len(output_structure) >= 4:
        target = output_structure[3]  # 네 번째 출력 구조
        return base + f"\n\n⚠️ 반드시 '{target}' 항목만 출력. 그 외 항목은 출력하지 마세요."
    else:
        return base + "\n\n⚠️ 반드시 '전략적 제언 및 시사점'만 출력. 그 외 항목은 출력하지 마세요."

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
