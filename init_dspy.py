
# init_dspy.py
import dspy
import os
import streamlit as st
from dotenv import load_dotenv
from agent_executor import RequirementTableSignature  # 이것만 필요

load_dotenv()

# Streamlit Secrets에서 API 키 가져오기 (우선순위)
try:
    anthropic_api_key = st.secrets.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        # 환경 변수에서 가져오기 (로컬 개발용)
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
except:
    # 환경 변수에서 가져오기 (로컬 개발용)
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

# API 키 확인
if not anthropic_api_key:
    print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다!")
    print("💡 Streamlit Cloud에서는 Settings → Secrets에서 설정하세요.")
    print("💡 로컬 개발에서는 .streamlit/secrets.toml 파일을 사용하세요.")
    raise ValueError("ANTHROPIC_API_KEY를 설정해주세요.")

if not getattr(dspy.settings, "lm", None):
    try:
        lm = dspy.LM(
            "claude-3-5-sonnet-20241022",  # 올바른 모델명
            provider="anthropic",
            api_key=anthropic_api_key,
            max_tokens=4000
        )
        dspy.configure(lm=lm, track_usage=True)
        print("✅ Claude 모델이 성공적으로 설정되었습니다.")
    except Exception as e:
        print(f"❌ Claude 모델 설정 실패: {e}")
        raise

# 사용 가능한 Claude 모델들
available_models = [
    "claude-3-5-sonnet-20241022",  # 최신 Sonnet
    "claude-3-5-haiku-20241022",   # 빠른 Haiku
    "claude-3-opus-20240229",      # 강력한 Opus
    "claude-3-sonnet-20240229",    # 균형잡힌 Sonnet
    "claude-3-haiku-20240307"      # 가벼운 Haiku
]

def get_optimal_model(task_type: str) -> str:
    """작업 유형에 따른 최적 모델 선택"""
    model_mapping = {
        "quick_analysis": "claude-3-5-haiku-20241022",  # 빠른 분석
        "detailed_analysis": "claude-3-5-sonnet-20241022",  # 상세 분석
        "complex_analysis": "claude-3-opus-20240229",  # 복잡한 분석
        "cost_sensitive": "claude-3-haiku-20240307"  # 비용 민감
    }
    return model_mapping.get(task_type, "claude-3-5-sonnet-20241022")

def configure_model(model_name: str):
    """모델 동적 변경"""
    if model_name not in available_models:
        raise ValueError(f"지원하지 않는 모델: {model_name}")
    
    try:
        lm = dspy.LM(
            model_name,
            provider="anthropic",
            api_key=anthropic_api_key,
            max_tokens=4000
        )
        dspy.configure(lm=lm, track_usage=True)
        print(f"✅ 모델이 {model_name}로 변경되었습니다.")
    except Exception as e:
        print(f"❌ 모델 변경 실패: {e}")
        raise

def run_analysis_with_optimal_model(task_type: str, prompt: str, signature_class=None):
    """작업 유형에 따른 최적 모델로 분석 실행"""
    optimal_model = get_optimal_model(task_type)
    
    # 모델 변경
    configure_model(optimal_model)
    
    # 분석 실행 (기본값 또는 지정된 Signature 사용)
    if signature_class is None:
        signature_class = RequirementTableSignature  # 기본값
    
    result = dspy.Predict(signature_class)(input=prompt)
    return result

# 모델 정보 제공 함수
def get_model_info():
    """모델별 정보 반환"""
    return {
        "claude-3-5-sonnet-20241022": {
            "name": "Claude 3.5 Sonnet",
            "speed": "보통",
            "power": "높음", 
            "cost": "보통",
            "best_for": "일반적인 분석"
        },
        "claude-3-5-haiku-20241022": {
            "name": "Claude 3.5 Haiku",
            "speed": "빠름",
            "power": "보통",
            "cost": "낮음",
            "best_for": "빠른 응답 필요"
        },
        "claude-3-opus-20240229": {
            "name": "Claude 3 Opus", 
            "speed": "느림",
            "power": "매우 높음",
            "cost": "높음",
            "best_for": "복잡한 분석"
        },
        "claude-3-sonnet-20240229": {
            "name": "Claude 3 Sonnet",
            "speed": "보통", 
            "power": "높음",
            "cost": "보통",
            "best_for": "균형잡힌 분석"
        },
        "claude-3-haiku-20240307": {
            "name": "Claude 3 Haiku",
            "speed": "빠름",
            "power": "보통", 
            "cost": "낮음",
            "best_for": "경제적인 분석"
        }
    }
