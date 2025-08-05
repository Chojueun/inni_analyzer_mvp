from utils_pdf_vector import search_pdf_chunks
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
