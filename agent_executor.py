# agent_executor.py
import os
import dspy
from dotenv import load_dotenv

# 환경변수 로딩
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

# DeepSeek용 LM 설정
if not dspy.settings.lm:  # 이미 설정되어 있는 경우 재설정하지 않음
    lm = dspy.OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",
        model="deepseek-chat"
    )
    dspy.configure(lm=lm)


# 시그니처 정의
class PromptSignature(dspy.Signature):
    prompt = dspy.InputField(desc="Full analysis prompt")
    output = dspy.OutputField(desc="AI-generated response")

# 예측 모듈 정의
class RunAnalysisModule(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predictor = dspy.Predict(PromptSignature)

    def forward(self, prompt: str):
        prediction = self.predictor(prompt=prompt)
        return prediction.output

# 외부에서 사용할 에이전트
class InniAgent:
    def __init__(self):
        self.analysis_module = RunAnalysisModule()

    def run_analysis(self, full_prompt: str):
        return self.analysis_module(full_prompt)
