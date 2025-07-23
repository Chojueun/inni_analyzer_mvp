def format_result(result: str) -> str:
    if "취소선" in result or "~~" in result:
        result = result.replace("~~", "").replace("취소선", "")
    return result.strip()
