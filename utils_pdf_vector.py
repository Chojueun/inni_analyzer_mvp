# utils_pdf_vector.py 
import chromadb
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import streamlit as st
import os
from typing import List, Dict, Optional

# pysqlite3 관련 코드 완전 제거

# 전역 변수 초기화
embedder = None
collection = None
chroma_client = None

def initialize_vector_system():
    """벡터 시스템 초기화 - 필요할 때만 호출"""
    global embedder, collection, chroma_client
    
    if embedder is not None and collection is not None:
        return True
    
    try:
        # 1. 임베딩 모델 로드 (가볍고 무료)
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # 2. ChromaDB 인스턴스
        chroma_client = chromadb.Client()
        collection = chroma_client.get_or_create_collection("pdf_chunks")
        
        return True
    except Exception as e:
        st.error(f"❌ 벡터 시스템 초기화 실패: {e}")
        return False

def search_pdf_chunks(query: str, pdf_id: str = "default", top_k: int = 3) -> str:
    """고급 PDF 벡터 검색 함수 - 호환성 개선"""
    
    # 벡터 시스템 초기화
    if not initialize_vector_system():
        st.warning("⚠️ 고급 검색 시스템 초기화 실패, 간단 검색으로 전환")
        return fallback_to_simple_search(query, pdf_id, top_k)
    
    try:
        # 쿼리 임베딩 생성
        q_embed = embedder.encode([query])[0].tolist()
        
        # 벡터 검색 실행
        result = collection.query(
            query_embeddings=[q_embed], 
            n_results=top_k
        )
        
        # 결과 처리
        if (result and "documents" in result and 
            result["documents"][0] and len(result["documents"][0]) > 0):
            
            chunks = result["documents"][0]
            formatted_chunks = []
            
            for i, chunk in enumerate(chunks, 1):
                # 청크 길이 제한 (너무 길면 잘라서 표시)
                if len(chunk) > 500:
                    chunk = chunk[:500] + "..."
                formatted_chunks.append(f"📄 고급 검색 결과 {i}:\n{chunk}")
            
            return "\n---\n".join(formatted_chunks)
        else:
            st.info("ℹ️ 고급 검색에서 관련 정보를 찾을 수 없습니다.")
            return "[고급 검색 결과 없음]"
            
    except Exception as e:
        st.error(f"❌ 고급 PDF 검색 오류: {e}")
        return fallback_to_simple_search(query, pdf_id, top_k)

def fallback_to_simple_search(query: str, pdf_id: str, top_k: int) -> str:
    """고급 검색 실패 시 간단 검색으로 폴백"""
    try:
        # 간단 검색 로직
        if 'pdf_chunks' not in st.session_state or pdf_id not in st.session_state.pdf_chunks:
            return "[PDF가 로드되지 않았습니다. 먼저 PDF를 업로드해주세요.]"
        
        text = st.session_state.pdf_chunks[pdf_id]
        
        # 키워드 기반 검색
        import re
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
            results.append(f"📄 간단 검색 결과 {i} (관련도: {score}):\n{para}")
        
        if results:
            return "\n---\n".join(results)
        else:
            return "[관련 정보를 찾을 수 없습니다.]"
            
    except Exception as e:
        st.error(f"❌ 간단 검색 오류: {e}")
        return "[검색 오류가 발생했습니다.]"

def pdf_to_chunks(pdf_path: str, chunk_size: int = 400) -> List[str]:
    """PDF를 청크로 분할"""
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

def save_pdf_chunks_to_chroma(pdf_path: str, pdf_id: str = "default") -> bool:
    """PDF 청크를 ChromaDB에 저장"""
    try:
        # 벡터 시스템 초기화
        if not initialize_vector_system():
            st.warning("⚠️ 벡터 시스템 초기화 실패, 간단 저장으로 전환")
            return fallback_to_simple_save(pdf_path, pdf_id)
        
        # PDF를 청크로 분할
        chunks = pdf_to_chunks(pdf_path)
        
        if not chunks:
            st.error("❌ PDF 청크 분할 실패")
            return False
        
        # 청크를 세션 상태에 저장 (간단 검색용)
        if 'pdf_chunks' not in st.session_state:
            st.session_state.pdf_chunks = {}
        
        st.session_state.pdf_chunks[pdf_id] = "\n\n".join(chunks)
        
        # ChromaDB에 저장
        try:
            # 임베딩 생성
            embeddings = embedder.encode(chunks)
            
            # ChromaDB에 저장
            collection.add(
                embeddings=embeddings.tolist(),
                documents=chunks,
                ids=[f"{pdf_id}_{i}" for i in range(len(chunks))]
            )
            
            st.success(f"✅ PDF 청크 {len(chunks)}개가 ChromaDB에 저장되었습니다.")
            return True
            
        except Exception as e:
            st.error(f"❌ ChromaDB 저장 실패: {e}")
            return fallback_to_simple_save(pdf_path, pdf_id)
        
    except Exception as e:
        st.error(f"❌ PDF 저장 오류: {e}")
        return False

def fallback_to_simple_save(pdf_path: str, pdf_id: str) -> bool:
    """ChromaDB 저장 실패 시 간단 저장으로 폴백"""
    try:
        # PDF 텍스트 추출
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            return False
        
        # 세션 상태에 저장
        if 'pdf_chunks' not in st.session_state:
            st.session_state.pdf_chunks = {}
        
        st.session_state.pdf_chunks[pdf_id] = text
        st.success(f"✅ PDF가 간단 모드로 저장되었습니다.")
        return True
        
    except Exception as e:
        st.error(f"❌ 간단 저장 실패: {e}")
        return False

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF에서 텍스트 추출"""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text += page.get_text() + "\n"
        
        doc.close()
        return text
        
    except Exception as e:
        st.error(f"❌ PDF 텍스트 추출 오류: {e}")
        return ""

def get_pdf_summary(pdf_id: str = "default") -> str:
    """PDF 요약 정보 반환"""
    if 'pdf_chunks' not in st.session_state or pdf_id not in st.session_state.pdf_chunks:
        return "[PDF 정보가 없습니다.]"
    
    text = st.session_state.pdf_chunks[pdf_id]
    return text[:1000] + "..." if len(text) > 1000 else text