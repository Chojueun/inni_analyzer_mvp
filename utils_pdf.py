"""
통합 PDF 처리 모듈
- PDF 텍스트 추출
- PDF 저장 및 검색
- PDF 요약 정보 관리
"""

import streamlit as st
import fitz  # PyMuPDF
import re
from typing import List, Dict, Any

# 전역 변수 (벡터 시스템용)
embedder = None
collection = None
chroma_client = None

def initialize_vector_system():
    """벡터 시스템 초기화 - 간단 검색만 사용"""
    global embedder, collection, chroma_client
    
    # 고급 벡터 시스템 완전 비활성화
    embedder = None
    collection = None
    chroma_client = None
    
    # 메시지 제거 - 조용히 True 반환
    return True

def extract_text_from_pdf(pdf_input, input_type="path") -> str:
    """
    통합된 PDF 텍스트 추출 함수
    
    Args:
        pdf_input: PDF 파일 경로(str) 또는 바이트(bytes)
        input_type: "path" 또는 "bytes"
    
    Returns:
        str: 추출된 텍스트
    """
    try:
        if input_type == "path":
            # 파일 경로로부터 텍스트 추출
            doc = fitz.open(pdf_input)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text() + "\n"
            
            doc.close()
            return text
            
        elif input_type == "bytes":
            # 바이트로부터 텍스트 추출
            with fitz.open(stream=pdf_input, filetype="pdf") as doc:
                return "\n".join([page.get_text() for page in doc])
        else:
            raise ValueError("input_type must be 'path' or 'bytes'")
            
    except Exception as e:
        st.error(f"❌ PDF 텍스트 추출 오류: {e}")
        return ""

def save_pdf_chunks_to_chroma(pdf_path: str, pdf_id: str = "default") -> bool:
    """
    PDF 청크를 간단 저장으로 처리
    
    Args:
        pdf_path: PDF 파일 경로
        pdf_id: PDF 식별자
    
    Returns:
        bool: 저장 성공 여부
    """
    try:
        # PDF 텍스트 추출
        text = extract_text_from_pdf(pdf_path, "path")
        
        if not text:
            st.error("❌ PDF 텍스트 추출 실패")
            return False
        
        # 세션 상태에 저장
        if 'pdf_chunks' not in st.session_state:
            st.session_state.pdf_chunks = {}
        
        st.session_state.pdf_chunks[pdf_id] = text
        st.success(f"✅ PDF가 저장되었습니다. (간단 모드)")
        return True
        
    except Exception as e:
        st.error(f"❌ PDF 저장 오류: {e}")
        return False

def search_pdf_chunks(query: str, pdf_id: str = "default", top_k: int = 3) -> str:
    """
    PDF 검색 함수 - 간단 검색만 사용
    
    Args:
        query: 검색 쿼리
        pdf_id: PDF 식별자
        top_k: 반환할 결과 수
    
    Returns:
        str: 검색 결과
    """
    return fallback_to_simple_search(query, pdf_id, top_k)

def fallback_to_simple_search(query: str, pdf_id: str, top_k: int) -> str:
    """
    간단 검색 - 키워드 기반 검색
    
    Args:
        query: 검색 쿼리
        pdf_id: PDF 식별자
        top_k: 반환할 결과 수
    
    Returns:
        str: 검색 결과
    """
    try:
        # PDF 텍스트 확인
        if 'pdf_chunks' not in st.session_state or pdf_id not in st.session_state.pdf_chunks:
            return "[PDF가 로드되지 않았습니다. 먼저 PDF를 업로드해주세요.]"
        
        text = st.session_state.pdf_chunks[pdf_id]
        
        # 키워드 기반 검색
        keywords = re.findall(r'\w+', query.lower())
        paragraphs = text.split('\n\n')
        
        scored_paragraphs = []
        for para in paragraphs:
            if len(para.strip()) < 50:
                continue
                
            para_lower = para.lower()
            score = sum(1 for keyword in keywords if keyword in para_lower)
            
            if score > 0:
                scored_paragraphs.append((score, para.strip()))
        
        scored_paragraphs.sort(key=lambda x: x[0], reverse=True)
        
        results = []
        for i, (score, para) in enumerate(scored_paragraphs[:top_k], 1):
            if len(para) > 500:
                para = para[:500] + "..."
            results.append(f"�� 간단 검색 결과 {i} (관련도: {score}):\n{para}")
        
        if results:
            return "\n---\n".join(results)
        else:
            return "[관련 정보를 찾을 수 없습니다.]"
            
    except Exception as e:
        st.error(f"❌ 검색 오류: {e}")
        return "[검색 중 오류가 발생했습니다.]"

def get_pdf_summary(pdf_id: str = "default") -> str:
    """
    PDF 요약 정보 반환
    
    Args:
        pdf_id: PDF 식별자
    
    Returns:
        str: PDF 요약 정보
    """
    if 'pdf_chunks' not in st.session_state or pdf_id not in st.session_state.pdf_chunks:
        return "[PDF 정보가 없습니다.]"
    
    text = st.session_state.pdf_chunks[pdf_id]
    return text[:1000] + "..." if len(text) > 1000 else text

def pdf_to_chunks(pdf_path: str, chunk_size: int = 400) -> List[str]:
    """
    PDF를 청크로 분할
    
    Args:
        pdf_path: PDF 파일 경로
        chunk_size: 청크 크기
    
    Returns:
        List[str]: 분할된 청크들
    """
    try:
        doc = fitz.open(pdf_path)
        chunks = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # 텍스트를 문장 단위로 분할
            sentences = text.split('. ')
            
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) < chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
            
            # 마지막 청크 추가
            if current_chunk:
                chunks.append(current_chunk.strip())
        
        doc.close()
        return chunks
        
    except Exception as e:
        st.error(f"❌ PDF 청크 분할 오류: {e}")
        return []

def get_pdf_summary_from_session() -> str:
    """
    세션에서 PDF 요약 정보 가져오기 (user_state.py 호환성)
    
    Returns:
        str: PDF 요약 정보
    """
    return st.session_state.get('pdf_summary', '')

def set_pdf_summary_to_session(summary: str):
    """
    세션에 PDF 요약 정보 설정 (user_state.py 호환성)
    
    Args:
        summary: PDF 요약 정보
    """
    st.session_state.pdf_summary = summary
