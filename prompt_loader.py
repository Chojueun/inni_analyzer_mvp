#prompt_loader.py

import json
import os

# ✅ 핵심 원칙 선언 블록 (항상 맨 앞에 삽입됨)
CORE_PRINCIPLES_BLOCK = {
    "id": "core_principles",
    "title": "핵심 원칙 선언 및 유의사항",
    "description": "모든 분석에 앞서 적용되는 핵심 원칙과 유의사항입니다.",
    "content": """📌 (AI 추론을 통한 분석 결과:)

1. **건축주 중심 접근**: 입력된 정보를 바탕으로 건축주의 명시적, 암묵적 니즈를 모두 파악합니다.
2. **데이터 기반 추론**: '~인 것으로 보입니다', '~를 원하시는 것 같습니다' 등 부드러운 표현을 사용하되, 모든 추론은 분석된 데이터에 근거합니다.
3. **사례 기반 제안**: 구체적인 국내외 사례 조사를 통해 실증적 근거를 제시합니다.
4. **단계별 심화 분석**: 각 단계의 분석 결과를 다음 단계에 누적 반영하여 분석의 깊이를 더합니다.

🛑 유의사항:
- **AI 추론 명시**: 추론 또는 분석 결과에는 반드시 "(AI 추론을 통한 분석 결과:)" 문구를 명시합니다.
- **실행 가능한 제언만 제시**: 현실적으로 구현 가능한 전략만 포함합니다.
- **검증된 출처만 활용**: 개인 블로그는 제외하고, 신뢰할 수 있는 공식 보고서나 통계만 활용합니다.
- **텍스트 정확성 유지**: 줄그어진 부분, 오타 없이 깔끔한 최종 텍스트만 출력합니다.
"""
}


def load_prompt_blocks(json_path="prompt_blocks_dsl.json"):
    """
    고정 블럭(core)은 따로, 나머지 분석 블럭은 따로 리턴.
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # 고정 블럭만
    core = [CORE_PRINCIPLES_BLOCK]
    # JSON에 정의된 나머지 블럭
    extra = data["blocks"] if isinstance(data, dict) else []
    return {
        "core": core,      # 리스트 형태
        "extra": extra     # 리스트 형태
    }



def dsl_to_content(dsl: dict) -> str:
    """
    content_dsl 형식을 일반 텍스트 content로 변환
    """
    lines = [f"📌 (AI 추론을 통한 분석 결과:)"]

    if "goal" in dsl:
        lines.append(f"\n🎯 목표: {dsl['goal']}")
    
    if "source" in dsl:
        sources = ", ".join(dsl["source"])
        lines.append(f"\n📂 정보 출처: {sources}")
    
    if "tasks" in dsl:
        lines.append("\n📝 주요 분석 항목:")
        for t in dsl["tasks"]:
            lines.append(f"- {t}")
    
    if "constraints" in dsl:
        cons = ", ".join(dsl["constraints"])
        lines.append(f"\n⚠️ 유의사항: {cons}")
    
    if "style" in dsl:
        lines.append(f"\n💡 스타일 지침: {dsl['style']}")

    return "\n".join(lines)