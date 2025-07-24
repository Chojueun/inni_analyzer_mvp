import os
import dspy
from dspy import Module, Signature, InputField, OutputField
from dspy.teleprompt.bootstrap import BootstrapFewShot
from dspy.predict.react import ReAct
from dotenv import load_dotenv

# ✅ 환경변수 로드
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")

# ✅ LLM 구성 및 Usage 트래킹 설정
if not dspy.settings.lm:
    lm = dspy.LM("openai/gpt-4o", api_key=api_key)
    dspy.configure(lm=lm, track_usage=True)

# ✅ Signature: 입력/출력 정의
class AnalysisSignature(Signature):
    """
    건축 프로젝트 분석에 필요한 전체 프롬프트를 입력받아
    Chain-of-Thought reasoning과 최종 결과를 생성한다.
    """
    input = InputField(desc="전체 분석 프롬프트 (사용자 입력 + PDF 요약 + 선택 블럭)")
    reasoning = OutputField(desc="Chain-of-Thought 추론 과정")
    output = OutputField(desc="최종 분석 결과")

# ✅ 에이전트 정의 (CoT 기반)
class InniAgent(Module):
    def __init__(self, method="CoT"):
        super().__init__()
        self.method = method
        if method == "ReAct":
            self.analysis_module = ReAct(AnalysisSignature, tools=[])
        elif method == "BootstrapFewShot":
            self.analysis_module = BootstrapFewShot(AnalysisSignature)
        else:
            self.analysis_module = dspy.ChainOfThought(AnalysisSignature)

    def run_analysis(self, full_prompt: str, method="CoT") -> str:
        agent = InniAgent(method)
        try:
            result = agent.analysis_module(input=full_prompt)
            output = result.output

            # 실패(빈 결과) 시 순차 재시도
            if not output:
                # BootstrapFewShot → ReAct 순으로 재시도
                if self.method != "BootstrapFewShot":
                    print("⚠️ 재시도: BootstrapFewShot 사용")
                    result = BootstrapFewShot(AnalysisSignature)(input=full_prompt)
                if not result.output:
                    print("⚠️ 재시도: ReAct 사용")
                    result = ReAct(AnalysisSignature)(input=full_prompt)
                output = result.output

            # 디버깅·로깅
            print(f"\n🧠 [Reasoning]\n{result.reasoning}")
            print(f"\n📊 [Token Usage]\n{result.get_lm_usage()}")

            return output

        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            return "분석 중 오류가 발생했습니다. 입력 프롬프트를 확인해주세요."
