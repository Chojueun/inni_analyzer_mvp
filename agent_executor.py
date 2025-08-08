# agent_executor.py
import dspy
from dspy import Module, Signature, InputField, OutputField
from dspy.teleprompt.bootstrap import BootstrapFewShot
from dspy.predict.react import ReAct
from init_dspy import *

# --- 요구사항표 Signature & 함수
class RequirementTableSignature(Signature):
    input = InputField(desc="분석 목표, PDF, 맥락 등")
    requirement_table = OutputField(desc="요구사항 정리 또는 핵심 요약 표 형식 출력. 항목별 구분 및 단위 포함")

def run_requirement_table(full_prompt):
    try:
        result = dspy.Predict(RequirementTableSignature)(input=full_prompt)
        value = getattr(result, "requirement_table", "")
        if not value or value.strip() == "" or "error" in value.lower():
            return "⚠️ 결과 생성 실패: 요구사항표가 정상적으로 생성되지 않았습니다."
        return value
    except Exception as e:
        return f"❌ 오류: {e}"

# --- AI Reasoning Signature & 함수
class AIReasoningSignature(Signature):
    input = InputField(desc="분석 목표, PDF, 맥락 등")
    ai_reasoning = OutputField(desc="Chain-of-Thought 기반 추론 해설. 각 항목별 논리 전개 및 AI 추론 명시")

def run_ai_reasoning(full_prompt):
    try:
        result = dspy.Predict(AIReasoningSignature)(input=full_prompt)
        value = getattr(result, "ai_reasoning", "")
        if not value or value.strip() == "" or "error" in value.lower():
            return "⚠️ 결과 생성 실패: AI reasoning이 정상적으로 생성되지 않았습니다."
        return value
    except Exception as e:
        return f"❌ 오류: {e}"

# --- 사례 비교 Signature & 함수
class PrecedentComparisonSignature(Signature):
    input = InputField(desc="분석 목표, PDF, 맥락 등")
    precedent_comparison = OutputField(desc="유사 사례 비교. 표 또는 요약 문단 포함")

def run_precedent_comparison(full_prompt):
    try:
        result = dspy.Predict(PrecedentComparisonSignature)(input=full_prompt)
        value = getattr(result, "precedent_comparison", "")
        if not value or value.strip() == "" or "error" in value.lower():
            return "⚠️ 결과 생성 실패: 유사 사례 비교가 정상적으로 생성되지 않았습니다."
        return value
    except Exception as e:
        return f"❌ 오류: {e}"

# --- 전략 제언 Signature & 함수
class StrategyRecommendationSignature(Signature):
    input = InputField(desc="분석 목표, PDF, 맥락 등")
    strategy_recommendation = OutputField(desc="전략적 제언 및 우선순위 정리. 실행 가능한 제안 포함")

def run_strategy_recommendation(full_prompt):
    try:
        result = dspy.Predict(StrategyRecommendationSignature)(input=full_prompt)
        value = getattr(result, "strategy_recommendation", "")
        if not value or value.strip() == "" or "error" in value.lower():
            return "⚠️ 결과 생성 실패: 전략 제언이 정상적으로 생성되지 않았습니다."
        return value
    except Exception as e:
        return f"❌ 오류: {e}"

# --- 최적화 조건 분석 Signature & 함수
class OptimizationConditionSignature(Signature):
    input = InputField(desc="분석 목표, 프로그램, 조건, 분석 텍스트 등")
    optimization_analysis = OutputField(desc="최적화 조건 분석 결과. 목적, 중요도, 고려사항 포함")

def execute_agent(prompt):
    """일반적인 AI 에이전트 실행 함수"""
    try:
        result = dspy.Predict(OptimizationConditionSignature)(input=prompt)
        value = getattr(result, "optimization_analysis", "")
        if not value or value.strip() == "" or "error" in value.lower():
            return "⚠️ 결과 생성 실패: AI 분석이 정상적으로 생성되지 않았습니다."
        return value
    except Exception as e:
        return f"❌ 오류: {e}"

# --- Narrative 생성 Signature & 함수
class NarrativeGenerationSignature(Signature):
    input = InputField(desc="프로젝트 정보, Narrative 방향 설정, 분석 결과 등")
    narrative_story = OutputField(desc="소설처럼 감성적이고 몰입감 있는 건축설계 발표용 Narrative. 스토리텔링 중심의 서술")

def generate_narrative(prompt):
    """Narrative 생성 함수 - 소설처럼 감성적이고 몰입감 있는 스토리텔링"""
    try:
        result = dspy.Predict(NarrativeGenerationSignature)(input=prompt)
        value = getattr(result, "narrative_story", "")
        if not value or value.strip() == "" or "error" in value.lower():
            return "⚠️ 결과 생성 실패: Narrative가 정상적으로 생성되지 않았습니다."
        return value
    except Exception as e:
        return f"❌ 오류: {e}"

# --- 전체 합치기용 (실제 사용은 버튼 분할이 안전!)
def run_full_analysis(full_prompt):
    req = run_requirement_table(full_prompt)
    ai = run_ai_reasoning(full_prompt)
    pre = run_precedent_comparison(full_prompt)
    strat = run_strategy_recommendation(full_prompt)
    output = (
        "📊 요구사항 정리표\n" + req + "\n\n" +
        "🧠 AI 추론 해설\n" + ai + "\n\n" +
        "🧾 유사 사례 비교\n" + pre + "\n\n" +
        "✅ 전략적 제언 및 시사점\n" + strat
    )
    return output
