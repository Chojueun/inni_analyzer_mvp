#!/usr/bin/env python3
"""
API 연결 상태 테스트 스크립트
"""

import os
import sys
from dotenv import load_dotenv
import anthropic
from anthropic import Anthropic

def test_api_connection():
    """API 연결 테스트"""
    print("🔍 API 연결 상태 확인 중...")
    
    # 1. 환경 변수 로드
    load_dotenv()
    
    # 2. API 키 확인
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not anthropic_api_key:
        print("❌ ANTHROPIC_API_KEY를 찾을 수 없습니다.")
        print("💡 .streamlit/secrets.toml 파일을 확인해주세요.")
        return False
    
    if anthropic_api_key == "your_anthropic_api_key_here":
        print("❌ API 키가 기본값으로 설정되어 있습니다.")
        print("💡 실제 API 키로 변경해주세요.")
        return False
    
    print(f"✅ API 키 발견: {anthropic_api_key[:10]}...")
    
    # 3. Anthropic 클라이언트 생성
    try:
        anthropic_client = Anthropic(api_key=anthropic_api_key)
        print("✅ Anthropic 클라이언트 생성 성공")
    except Exception as e:
        print(f"❌ Anthropic 클라이언트 생성 실패: {e}")
        return False
    
    # 4. 간단한 테스트 프롬프트
    test_prompt = "안녕하세요. 간단한 테스트입니다. 'API 연결 성공'이라고만 답해주세요."
    
    try:
        print("🔄 API 호출 테스트 중...")
        response = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[{"role": "user", "content": test_prompt}]
        )
        
        result = response.content[0].text
        print(f"✅ API 응답 수신: {len(result)} 문자")
        print(f"📝 응답 내용: {result}")
        
        if "API 연결 성공" in result:
            print("🎉 API 연결 테스트 성공!")
            return True
        else:
            print("⚠️ 예상치 못한 응답을 받았습니다.")
            return False
            
    except anthropic.AuthenticationError:
        print("❌ API 키 인증 실패 - 올바른 API 키를 설정해주세요")
        return False
    except anthropic.RateLimitError:
        print("❌ Rate limit 도달 - 잠시 후 다시 시도해주세요")
        return False
    except anthropic.APIError as e:
        print(f"❌ API 오류: {e}")
        return False
    except Exception as e:
        print(f"❌ 연결 오류: {e}")
        return False

def test_available_models():
    """사용 가능한 모델 목록 조회"""
    print("\n🔍 사용 가능한 모델 목록 조회 중...")
    
    try:
        load_dotenv()
        anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        
        if not anthropic_api_key or anthropic_api_key == "your_anthropic_api_key_here":
            print("❌ API 키가 설정되지 않았습니다.")
            return
        
        anthropic_client = Anthropic(api_key=anthropic_api_key)
        models = anthropic_client.models.list()
        
        claude_models = [model.id for model in models if 'claude' in model.id]
        
        print(f"✅ {len(claude_models)}개의 Claude 모델 발견:")
        for i, model in enumerate(claude_models, 1):
            print(f"  {i}. {model}")
            
    except Exception as e:
        print(f"❌ 모델 목록 조회 실패: {e}")

def main():
    """메인 함수"""
    print("=" * 50)
    print("🔌 Anthropic Claude API 연결 테스트")
    print("=" * 50)
    
    # API 연결 테스트
    success = test_api_connection()
    
    if success:
        # 모델 목록 조회
        test_available_models()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 모든 테스트가 성공했습니다!")
    else:
        print("❌ 테스트에 실패했습니다.")
    print("=" * 50)

if __name__ == "__main__":
    main()
