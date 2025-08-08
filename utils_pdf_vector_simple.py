# utils_pdf_vector_simple.py
# ChromaDB 없이 작동하는 간단한 PDF 검색 시스템

import fitz  # PyMuPDF
import streamlit as st
import os
import re
from typing import List, Dict

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF에서 텍스트 추출"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        st.error(f"❌ PDF 텍스트 추출 실패: {e}")
        return ""

def simple_text_search(text: str, query: str, max_results: int = 3) -> str:
    """간단한 텍스트 검색"""
    if not text or not query:
        return "[검색할 내용이 없습니다]"
    
    try:
        # 쿼리를 키워드로 분할
        keywords = re.findall(r'\w+', query.lower())
        
        # 문단으로 분할
        paragraphs = text.split('\n\n')
        
        # 각 문단의 관련성 점수 계산
        scored_paragraphs = []
        for para in paragraphs:
            if len(para.strip()) < 50:
                continue
                
            para_lower = para.lower()
            score = sum(1 for keyword in keywords if keyword in para_lower)
            
            if score > 0:
                scored_paragraphs.append((score, para.strip()))
        
        # 점수순으로 정렬
        scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
        
        # 상위 결과 반환
        results = []
        for i, (score, para) in enumerate(scored_paragraphs[:max_results], 1):
            # 너무 긴 문단은 잘라서 표시
            if len(para) > 500:
                para = para[:500] + "..."
            results.append(f"📄 관련 문단 {i} (관련도: {score}):\n{para}")
        
        if results:
            return "\n---\n".join(results)
        else:
            return "[관련 정보를 찾을 수 없습니다]"
            
    except Exception as e:
        st.error(f"❌ 텍스트 검색 오류: {e}")
        return f"[검색 오류: {e}]"

def save_pdf_chunks_to_chroma(pdf_path: str, pdf_id: str = "default") -> bool:
    """PDF 청크 저장 (간단한 버전)"""
    try:
        # PDF 텍스트 추출
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return False
        
        # 세션 상태에 저장
        if 'pdf_chunks' not in st.session_state:
            st.session_state.pdf_chunks = {}
        
        st.session_state.pdf_chunks[pdf_id] = text
        st.success(f"✅ PDF 텍스트 저장 완료: {len(text)} 문자")
        return True
        
    except Exception as e:
        st.error(f"❌ PDF 저장 실패: {e}")
        return False

def search_pdf_chunks(query: str, pdf_id: str = "default", top_k: int = 3) -> str:
    """PDF 청크 검색 (간단한 버전)"""
    try:
        # 저장된 PDF 텍스트 가져오기
        if 'pdf_chunks' not in st.session_state or pdf_id not in st.session_state.pdf_chunks:
            return "[PDF가 로드되지 않았습니다. 먼저 PDF를 업로드해주세요.]"
        
        text = st.session_state.pdf_chunks[pdf_id]
        return simple_text_search(text, query, top_k)
        
    except Exception as e:
        st.error(f"❌ PDF 검색 실패: {e}")
        return f"[검색 오류: {e}]"

def get_pdf_summary(pdf_id: str = "default") -> str:
    """PDF 요약 (간단한 버전)"""
    try:
        if 'pdf_chunks' not in st.session_state or pdf_id not in st.session_state.pdf_chunks:
            return "[PDF가 로드되지 않았습니다]"
        
        text = st.session_state.pdf_chunks[pdf_id]
        
        # 간단한 요약 생성 (처음 1000자)
        if len(text) > 1000:
            summary = text[:1000] + "..."
        else:
            summary = text
        
        return summary
        
    except Exception as e:
        st.error(f"❌ PDF 요약 실패: {e}")
        return f"[요약 오류: {e}]"
