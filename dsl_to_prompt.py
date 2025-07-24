def convert_dsl_to_prompt(dsl_block: dict, user_inputs: dict, previous_summary: str = "", pdf_summary: str = "") -> str:
    prompt = "📌 (AI 추론을 통한 분석 결과:)\n\n"
    
    # 작업 목표
    for task in dsl_block.get("tasks", []):
        prompt += f"- {task}\n"

    # 입력 정보
    prompt += "\n■ 입력 정보\n"
    for src in dsl_block.get("source", []):
        if src == "pdf_summary":
            prompt += f"- PDF 요약: {pdf_summary[:300]}...\n"
        elif src == "previous_summary":
            prompt += f"- 이전 결과 요약: {previous_summary[:300]}...\n"
        elif src.startswith("user_inputs."):
            key = src.split(".")[1]
            val = user_inputs.get(key, "")
            prompt += f"- {key}: {val}\n"
        elif src == "user_inputs":
            for key, val in user_inputs.items():
                prompt += f"- {key}: {val}\n"

    return prompt.strip()
