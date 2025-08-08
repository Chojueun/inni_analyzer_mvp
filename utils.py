
#utils.py

import fitz  # PyMuPDF
import re
from typing import Dict, Optional, List
import streamlit as st
import json
import time
from datetime import datetime


def extract_summary(result: str) -> str:
    """
    전체 Claude 출력 텍스트에서 300자 내외 요약을 자동 추출
    """
    # 1. ‘요구사항 분석’ 또는 ‘핵심 요약표’ 섹션이 있으면 우선 추출
    if "요구사항 분석" in result:
        m = re.search(r"(요구사항 분석.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()[:300]
    elif "요약" in result:
        m = re.search(r"(요약.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()[:300]

    # 2. 앞부분 300자 기본 제공
    return result.strip()[:300] + "..."

def extract_insight(result: str) -> str:
    """
    GPT 출력 텍스트에서 전략 제언 또는 시사점 섹션을 추출
    """
    if "전략적 제언" in result:
        m = re.search(r"(전략적 제언.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()
    elif "시사점" in result:
        m = re.search(r"(시사점.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()
    elif "Insight" in result:
        m = re.search(r"(Insight.*?)\n\n", result, re.DOTALL)
        if m:
            return m.group(1).strip()

    # fallback
    return "※ 전략적 제언 항목이 명확히 감지되지 않았습니다."


def extract_text_from_pdf(pdf_bytes) -> str:
    """
    PDF 바이트에서 전체 텍스트를 추출한다.
    """
    import fitz
    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join([page.get_text() for page in doc])

def calculate_claude_cost(input_tokens, output_tokens, model="claude-3-5-sonnet-20241022"):
    """Claude API 사용 비용 계산 (USD 기준)"""
    # Anthropic Claude 3.5 Sonnet 가격 (2024년 기준)
    pricing = {
        "claude-3-5-sonnet-20241022": {
            "input": 3.00,  # $3.00 per 1M input tokens
            "output": 15.00  # $15.00 per 1M output tokens
        },
        "claude-3-5-haiku-20241022": {
            "input": 0.25,  # $0.25 per 1M input tokens
            "output": 1.25  # $1.25 per 1M output tokens
        },
        "claude-3-opus-20240229": {
            "input": 15.00,  # $15.00 per 1M input tokens
            "output": 75.00  # $75.00 per 1M output tokens
        },
        "claude-3-sonnet-20240229": {
            "input": 3.00,  # $3.00 per 1M input tokens
            "output": 15.00  # $15.00 per 1M output tokens
        },
        "claude-3-haiku-20240307": {
            "input": 0.25,  # $0.25 per 1M input tokens
            "output": 1.25  # $1.25 per 1M output tokens
        }
    }
    
    if model not in pricing:
        model = "claude-3-5-sonnet-20241022"  # 기본값
    
    model_pricing = pricing[model]
    
    # 토큰당 비용 계산 (1M 토큰당 가격을 토큰당 가격으로 변환)
    input_cost_per_token = model_pricing["input"] / 1_000_000
    output_cost_per_token = model_pricing["output"] / 1_000_000
    
    # 총 비용 계산
    total_input_cost = input_tokens * input_cost_per_token
    total_output_cost = output_tokens * output_cost_per_token
    total_cost = total_input_cost + total_output_cost
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "input_cost": total_input_cost,
        "output_cost": total_output_cost,
        "total_cost": total_cost,
        "model": model
    }

def display_usage_info(usage_data, operation_name="AI 분석"):
    """사용량 정보를 Streamlit에 표시"""
    if not usage_data:
        return
    
    # 비용 계산
    cost_info = calculate_claude_cost(
        usage_data.get("input_tokens", 0),
        usage_data.get("output_tokens", 0),
        usage_data.get("model", "claude-3-5-sonnet-20241022")
    )
    
    # 사용량 정보 표시 (더 눈에 띄게)
    st.success(f"✅ {operation_name} 완료!")
    
    with st.expander(f"💰 {operation_name} 사용량 정보", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("입력 토큰", f"{cost_info['input_tokens']:,}")
            st.metric("출력 토큰", f"{cost_info['output_tokens']:,}")
        
        with col2:
            st.metric("입력 비용", f"${cost_info['input_cost']:.4f}")
            st.metric("출력 비용", f"${cost_info['output_cost']:.4f}")
        
        with col3:
            st.metric("총 비용", f"${cost_info['total_cost']:.4f}")
            st.metric("모델", cost_info['model'])
        
        # 한국어 비용 표시
        krw_rate = 1300  # USD to KRW 환율 (대략적)
        krw_cost = cost_info['total_cost'] * krw_rate
        
        st.info(f"💡 예상 한국 원화 비용: 약 {krw_cost:,.0f}원 (환율: 1 USD = {krw_rate:,} KRW)")

def get_dspy_usage():
    """DSPy에서 사용량 정보 가져오기"""
    try:
        import dspy
        if hasattr(dspy.settings, 'lm') and dspy.settings.lm:
            # DSPy의 사용량 정보 접근 시도
            if hasattr(dspy.settings.lm, 'usage'):
                return dspy.settings.lm.usage
            elif hasattr(dspy.settings.lm, '_usage'):
                return dspy.settings.lm._usage
    except Exception as e:
        st.warning(f"사용량 정보를 가져올 수 없습니다: {e}")
    
    return None

def track_api_call(operation_name="AI 분석"):
    """API 호출 추적을 위한 데코레이터 스타일 함수"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 실행 시간 계산
            execution_time = time.time() - start_time
            
            # 사용량 정보 가져오기
            usage_data = get_dspy_usage()
            
            # 사용량 정보 표시
            if usage_data:
                display_usage_info(usage_data, operation_name)
            
            # 실행 시간 표시
            st.caption(f"⏱️ 실행 시간: {execution_time:.2f}초")
            
            return result
        return wrapper
    return decorator
