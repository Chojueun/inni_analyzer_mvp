#agent_executor.py
import dspy
from dspy import Module, Signature, InputField, OutputField
from dspy.teleprompt.bootstrap import BootstrapFewShot
from dspy.predict.react import ReAct
from init_dspy import *


# ✅ Signature: 입력/출력 정의
class AnalysisSignature(Signature):
    input = InputField(desc="고도화된 분석 프롬프트. 사용자 입력, PDF 요약, 이전 단계 요약, 분석 목표와 tasks 포함")

    requirement_table = OutputField(desc="요구사항 정리 또는 핵심 요약 표 형식 출력. 항목별로 명확한 구분과 단위 포함")
    ai_reasoning = OutputField(desc="Chain-of-Thought 기반 추론 해설. 각 항목별 논리 전개 및 AI 추론 명시")
    precedent_comparison = OutputField(desc="유사 사례 비교. 유사성과 차별점, 시사점 중심. 표 또는 요약 문단 포함")
    strategy_recommendation = OutputField(desc="전략적 제언 및 우선순위 정리. 실행 가능한 제안 포함")


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
        try:
            # DSPy 설정 재확인 및 강제 재설정
            if not dspy.settings.lm:
                print("⚠️ DSPy LM 재설정 시도")
                try:
                    # 기존 설정 완전 초기화
                    dspy.settings.configure(lm=None, track_usage=False)
                    
                    # 새로운 LM 설정
                    lm = dspy.LM("openai/gpt-4o", api_key=api_key)
                    dspy.configure(lm=lm, track_usage=True)
                    
                    if dspy.settings.lm:
                        print("✅ LM 재설정 성공")
                    else:
                        print("❌ LM 재설정 실패")
                        return "분석 중 오류가 발생했습니다. DSPy LM 설정을 확인해주세요."
                        
                except Exception as e:
                    print(f"❌ LM 재설정 실패: {e}")
                    return "분석 중 오류가 발생했습니다. DSPy 설정을 확인해주세요."

            agent = InniAgent(method)
            result = agent.analysis_module(input=full_prompt)

            # 결과 조립
            output = (
                "📊 요구사항 정리표\n" + result.requirement_table.strip() + "\n\n" +
                "🧠 AI 추론 해설\n" + result.ai_reasoning.strip() + "\n\n" +
                "🧾 유사 사례 비교\n" + result.precedent_comparison.strip() + "\n\n" +
                "✅ 전략적 제언 및 시사점\n" + result.strategy_recommendation.strip()
            )

            # 실패(빈 결과) 시 순차 재시도
            if not output.strip():
                print("⚠️ 빈 결과 감지, 재시도 중...")
                # BootstrapFewShot → ReAct 순으로 재시도
                if self.method != "BootstrapFewShot":
                    print("⚠️ 재시도: BootstrapFewShot 사용")
                    result = BootstrapFewShot(AnalysisSignature)(input=full_prompt)
                if not result.output:
                    print("⚠️ 재시도: ReAct 사용")
                    result = ReAct(AnalysisSignature)(input=full_prompt)
                output = result.output

            # 디버깅·로깅
            if hasattr(result, 'reasoning'):
                print(f"\n🧠 [Reasoning]\n{result.reasoning}")
            if hasattr(result, 'get_lm_usage'):
                print(f"\n📊 [Token Usage]\n{result.get_lm_usage()}")

            return output

        except Exception as e:
            print(f"❌ 분석 실패: {e}")
            return f"분석 중 오류가 발생했습니다: {str(e)}"
