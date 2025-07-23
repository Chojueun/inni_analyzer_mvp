# agent_executor.py
import os
import dspy
from dspy import Module, Signature, InputField, OutputField
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# ✅ 최신 DSPy 방식: LM() 사용
if not dspy.settings.lm:
    lm = dspy.LM("openai/gpt-4o", api_key=api_key)
    dspy.configure(lm=lm)

# 분석 Signature 정의
class AnalysisSignature(Signature):
    input = InputField(desc="분석 프롬프트")
    output = OutputField(desc="분석 결과")

# 분석 에이전트 정의
class InniAgent(Module):
    def __init__(self):
        super().__init__()
        self.analysis_module = dspy.Predict(AnalysisSignature)

    def run_analysis(self, full_prompt: str) -> str:
        result = self.analysis_module(input=full_prompt)
        return result.output