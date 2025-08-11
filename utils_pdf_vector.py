# utils_pdf_vector.py 
import chromadb
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import streamlit as st
import os
from typing import List, Dict, Optional

# pysqlite3 관련 코드 완전 제거

# 1. 임베딩 모델 로드 (가볍고 무료)
try:
    st.info("🔄 고급 PDF 검색 시스템 초기화 중...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    st.success("✅ 임베딩 모델 로드 완료")
except Exception as e:
    st.error(f"❌ 임베딩 모델 로드 실패: {e}")
    embedder = None

# 2. ChromaDB 인스턴스
try:
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection("pdf_chunks")
    st.success("✅ 벡터 데이터베이스 연결 완료")
except Exception as e:
    st.error(f"❌ ChromaDB 연결 실패: {e}")
    collection = None

def search_pdf_chunks(query: str, pdf_id: str = "default", top_k: int = 3) -> str:
    """고급 PDF 벡터 검색 함수 - 호환성 개선"""
    
    if not embedder or not collection:
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
            return "[간단 검색에서도 관련 정보를 찾을 수 없습니다]"
            
    except Exception as e:
        return f"[검색 오류: {e}]"

def pdf_to_chunks(pdf_path: str, chunk_size: int = 400) -> List[str]:
    """PDF를 청크로 분할"""
    
    if not os.path.exists(pdf_path):
        st.error(f"❌ PDF 파일을 찾을 수 없습니다: {pdf_path}")
        return []
    
    try:
        doc = fitz.open(pdf_path)
        all_chunks = []
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if not text.strip():
                continue
                
            # 문단 단위로 분할
            paragraphs = text.split('\n\n')
            for para in paragraphs:
                para = para.strip()
                if len(para) < 50:  # 너무 짧은 것 제외
                    continue
                    
                # 청크 크기로 자르기
                for i in range(0, len(para), chunk_size):
                    chunk = para[i:i+chunk_size].strip()
                    if len(chunk) > 50:
                        all_chunks.append(chunk)
        
        doc.close()
        st.success(f"✅ PDF 분할 완료: {len(all_chunks)}개 청크")
        return all_chunks
        
    except Exception as e:
        st.error(f"❌ PDF 분할 오류: {e}")
        return []

def save_pdf_chunks_to_chroma(pdf_path: str, pdf_id: str = "default") -> bool:
    """PDF 청크를 ChromaDB에 저장 - 호환성 개선"""
    
    if not embedder or not collection:
        st.warning("⚠️ 고급 저장 시스템 초기화 실패, 간단 저장으로 전환")
        return fallback_to_simple_save(pdf_path, pdf_id)
    
    try:
        # PDF 청크 생성
        chunks = pdf_to_chunks(pdf_path)
        if not chunks:
            st.error("❌ PDF에서 텍스트를 추출할 수 없습니다.")
            return False
        
        # 임베딩 생성
        st.info("🔄 PDF 벡터화 중...")
        embeds = embedder.encode(chunks).tolist()
        
        # 고유 ID 생성
        ids = [f"{pdf_id}_{i}" for i in range(len(chunks))]
        
        # ChromaDB에 저장
        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeds
        )
        
        st.success(f"✅ 고급 PDF 벡터 저장 완료: {pdf_id} ({len(chunks)}개 청크)")
        return True
        
    except Exception as e:
        st.error(f"❌ 고급 PDF 저장 오류: {e}")
        return fallback_to_simple_save(pdf_path, pdf_id)

def fallback_to_simple_save(pdf_path: str, pdf_id: str) -> bool:
    """고급 저장 실패 시 간단 저장으로 폴백"""
    try:
        # PDF 텍스트 추출
        text = extract_text_from_pdf(pdf_path)
        if not text:
            return False
        
        # 세션 상태에 저장
        if 'pdf_chunks' not in st.session_state:
            st.session_state.pdf_chunks = {}
        
        st.session_state.pdf_chunks[pdf_id] = text
        st.success(f"✅ 간단 PDF 텍스트 저장 완료: {len(text)} 문자")
        return True
        
    except Exception as e:
        st.error(f"❌ 간단 PDF 저장 실패: {e}")
        return False

def extract_text_from_pdf(pdf_path: str) -> str:
    """PDF에서 텍스트 추출 (호환성)"""
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

def get_pdf_summary(pdf_id: str = "default") -> str:
    """PDF 요약 (호환성)"""
    try:
        if 'pdf_chunks' not in st.session_state or pdf_id not in st.session_state.pdf_chunks:
            return "[PDF가 로드되지 않았습니다]"
        
        text = st.session_state.pdf_chunks[pdf_id]
        
        if len(text) > 1000:
            summary = text[:1000] + "..."
        else:
            summary = text
        
        return summary
        
    except Exception as e:
        st.error(f"❌ PDF 요약 실패: {e}")
        return f"[요약 오류: {e}]"