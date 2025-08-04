#dsl_to_prompt.py
from utils_pdf_vector import search_pdf_chunks
from search_helper import search_web_serpapi

def generate_output_header(dsl_block: dict) -> str:
    outputs = dsl_block.get("output_structure", [])
    if not outputs:
        return ""
    text = "\n\n📑 [출력 예시 구조]\n"
    for i, section in enumerate(outputs, 1):
        text += (
            f"\n{i}. [{section}]\n"
            "- 표로 주요 항목(항목/내용/근거·출처) 반드시 작성\n"
            "- 해당 표 아래에 요약적 해설, 실제 문서 근거 인용, AI추론, 실행 전략, 차별화 포인트를 꼭 추가\n"
        )
    return text

def convert_dsl_to_prompt(
    dsl_block: dict,
    user_inputs: dict,
    previous_summary: str = "",
    pdf_summary: dict = None,
    site_fields: dict = None
) -> str:
    prompt = ""

    # 1. PDF RAG 근거 자동 추가
    if dsl_block.get("search_source") == "pdf_vector_db":
        query_template = dsl_block.get("search_query_template", "주요 내용")
        query = query_template.format(**user_inputs)
        pdf_chunks = search_pdf_chunks(query, top_k=2)
        prompt += f"[PDF 인용 근거]\n{pdf_chunks}\n\n"

    # 2. 웹/뉴스 RAG 근거 자동 추가 (SerpAPI)
    if dsl_block.get("search_source") == "serpapi_web":
        query_template = dsl_block.get("search_query_template", "최신 트렌드")
        query = query_template.format(**user_inputs)
        serp_results = search_web_serpapi(query)
        prompt += f"[웹 인용 근거]\n{serp_results}\n\n"

    # 3. 그 외 기존 프롬프트(분석 지시어, 표, 설명 등) 그대로 이어 붙임
    goal = dsl_block.get("goal", "")
    tasks = dsl_block.get("tasks", [])
    sources = dsl_block.get("source", [])

    prompt += f"📌 당신은 실제 건축 입찰/기획/심사 보고서를 작성하는 AI 분석가입니다.\n"
    if "role" in dsl_block:
        prompt += f"🔄 이 단계의 역할: {dsl_block['role']}\n"
    prompt += f"\n아래 입력 정보를 바탕으로 **‘{goal}’** 분석 보고서를 작성하세요.\n\n"

    # 필요에 따라 기존 표/요약 등 삽입 (아래는 예시, 자유롭게 더 붙이면 됨)
    if isinstance(pdf_summary, dict) and pdf_summary:
        prompt += "### 📊 [입력/문서 기반 주요 데이터 요약표]\n"
        prompt += "| 항목 | 내용 |\n|------|------|\n"
        for k, v in pdf_summary.items():
            prompt += f"| {k} | {str(v).strip()} |\n"
        prompt += "\n"

    # 분석 항목, 지시사항 등 (아래는 예시)
    if tasks:
        prompt += "📂 [주요 분석 항목]\n"
        for i, task in enumerate(tasks, 1):
            prompt += f"{i}. {task}\n"
        prompt += "\n"

    prompt += (
        "### [출력 강제 지시]\n"
        "- 각 항목은 반드시 [문서 근거(페이지·원문·수치 등), 표(항목/내용/근거), 요약 해설, AI추론, 실행 가능한 전략 제언, 차별화 포인트]를 포함해야 합니다.\n"
        "- 모든 표는 항목/내용/근거 컬럼을 포함, 실행 전략 및 차별화 포인트는 별도 소제목과 체크리스트로 구분\n"
        "\n⚠️ 본 결과물은 실제 심사·입찰에 사용할 수 있을 만큼 근거, 수치, 전략, 차별화가 반드시 명확해야 합니다.\n"
    )

    return prompt.strip()