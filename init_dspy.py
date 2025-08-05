
# init_dspy.py
import dspy
import os
from dotenv import load_dotenv

load_dotenv()
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

# API 키 확인
if not anthropic_api_key:
    print("❌ ANTHROPIC_API_KEY가 설정되지 않았습니다!")
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
