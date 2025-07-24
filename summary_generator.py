# summary_generator.py

import dspy
from dspy import Signature, InputField, OutputField

class PDFSummarizer(Signature):
    """
    DSPy 시그니처로, PDF 원문(text)을 받아
    요약(summary)을 반환합니다.
    """
    # 입력: 원문 텍스트
    text: str = InputField(desc="PDF에서 추출한 전체 텍스트")
    # 출력: 요약문
    summary: str = OutputField(desc="텍스트 요약 결과")

# Predict 객체 생성
summarizer = dspy.Predict(PDFSummarizer)

def summarize_pdf(text: str) -> str:
    """
    DSPy Predict를 통해 요약을 생성하고,
    result.summary 속성을 반환합니다.
    """
    result = summarizer(text=text)
    return result.summary
