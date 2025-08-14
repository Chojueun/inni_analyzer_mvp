
# init_dspy.py
import dspy
import os
import time
import random
from dotenv import load_dotenv
from agent_executor import RequirementTableSignature 
import anthropic
from anthropic import Anthropic

load_dotenv()

# Anthropic API 키 설정
anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    print("💡 로컬 개발에서는 .streamlit/secrets.toml 파일을 사용하세요.")
    raise ValueError("ANTHROPIC_API_KEY를 설정해주세요.")

# Anthropic SDK 클라이언트 추가
anthropic_client = Anthropic(api_key=anthropic_api_key)

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

def get_available_models_sdk():
    """Anthropic SDK로 사용 가능한 모델 조회"""
    try:
        models = anthropic_client.models.list()
        sdk_models = [model.id for model in models if 'claude' in model.id]
        print(f"✅ SDK에서 {len(sdk_models)}개 모델 조회됨")
        return sdk_models
    except Exception as e:
        print(f"⚠️ SDK 모델 목록 조회 실패: {e}")
        return available_models  # 폴백

def execute_with_sdk_with_retry(prompt: str, model: str = None, max_retries: int = 3):
    """Anthropic SDK로 직접 실행 - 재시도 로직 포함"""
    if model is None:
        model = "claude-3-5-sonnet-20241022"
    
    for attempt in range(max_retries):
        try:
            response = anthropic_client.messages.create(
                model=model,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
            
        except anthropic.RateLimitError:
            wait_time = (2 ** attempt) + random.uniform(0, 1)  # 지수 백오프
            print(f"⚠️ Rate limit 도달. {wait_time:.1f}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
            
        except anthropic.APIError as e:
            if "overloaded_error" in str(e) or "Overloaded" in str(e):
                wait_time = (3 ** attempt) + random.uniform(1, 3)  # 과부하 시 더 긴 대기
                print(f"⚠️ API 과부하. {wait_time:.1f}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                return f"❌ API 오류: {e}"
                
        except Exception as e:
            if attempt == max_retries - 1:  # 마지막 시도
                return f"❌ 오류: {e}"
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            print(f"⚠️ 일반 오류. {wait_time:.1f}초 후 재시도... (시도 {attempt + 1}/{max_retries})")
            time.sleep(wait_time)
    
    return "❌ 최대 재시도 횟수 초과. 잠시 후 다시 시도해주세요."

def execute_with_sdk(prompt: str, model: str = None):
    """Anthropic SDK로 직접 실행 - 기존 함수 호환성 유지"""
    return execute_with_sdk_with_retry(prompt, model, max_retries=3)

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
    """모델 동적 변경 - 스레드 안전 버전"""
    if model_name not in available_models:
        raise ValueError(f"지원하지 않는 모델: {model_name}")
    
    try:
        # 기존 설정 제거
        if hasattr(dspy.settings, "lm"):
            delattr(dspy.settings, "lm")
        
        # 새 모델 설정
        lm = dspy.LM(
            model_name,
            provider="anthropic",
            api_key=anthropic_api_key,
            max_tokens=8000
        )
        dspy.configure(lm=lm, track_usage=True)
        print(f"✅ 모델이 {model_name}로 변경되었습니다.")
    except Exception as e:
        print(f"❌ 모델 변경 실패: {e}")
        # 기본 모델로 복구
        try:
            lm = dspy.LM(
                "claude-3-5-sonnet-20241022",
                provider="anthropic",
                api_key=anthropic_api_key,
                max_tokens=5000
            )
            dspy.configure(lm=lm, track_usage=True)
        except:
            pass
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
