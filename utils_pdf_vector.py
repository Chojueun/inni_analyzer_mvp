# utils_pdf_vector.py

# SQLite 버전 문제 해결을 위한 코드
import sys
try:
    import pysqlite3
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    pass

import chromadb
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
import streamlit as st
import os

# 1. 임베딩 모델 로드 (가볍고 무료)
try:
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    #st.success("✅ 임베딩 모델 로드 완료")
except Exception as e:
    st.error(f"❌ 임베딩 모델 로드 실패: {e}")
    embedder = None

# 2. ChromaDB 인스턴스
try:
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection("pdf_chunks")
    #st.success("✅ ChromaDB 연결 완료")
except Exception as e:
    st.error(f"❌ ChromaDB 연결 실패: {e}")
    collection = None

def search_pdf_chunks(query, top_k=3):
    """PDF 벡터 검색 함수 - 오류 처리 강화"""
    
    if not embedder or not collection:
        return "[PDF 검색 시스템 초기화 실패]"
    
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
                formatted_chunks.append(f"📄 청크 {i}:\n{chunk}")
            
            return "\n---\n".join(formatted_chunks)
        else:
            st.info("ℹ️ PDF에서 관련 정보를 찾을 수 없습니다.")
            return "[PDF 인용 근거 없음]"
            
    except Exception as e:
        st.error(f"❌ PDF 검색 오류: {e}")
        return f"[PDF 검색 오류: {e}]"

def pdf_to_chunks(pdf_path, chunk_size=400):
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

def save_pdf_chunks_to_chroma(pdf_path, pdf_id="pdf1"):
    """PDF 청크를 ChromaDB에 저장"""
    
    if not embedder or not collection:
        st.error("❌ 임베딩 모델 또는 ChromaDB가 초기화되지 않았습니다.")
        return False
    
    try:
        # PDF 청크 생성
        chunks = pdf_to_chunks(pdf_path)
        if not chunks:
            st.error("❌ PDF에서 텍스트를 추출할 수 없습니다.")
            return False
        
        # 임베딩 생성
        embeds = embedder.encode(chunks).tolist()
        
        # 고유 ID 생성
        ids = [f"{pdf_id}_{i}" for i in range(len(chunks))]
        
        # ChromaDB에 저장
        collection.add(
            ids=ids,
            documents=chunks,
            embeddings=embeds
        )
        
        st.success(f"✅ PDF {pdf_id}: {len(chunks)}개 청크 저장 완료")
        return True
        
    except Exception as e:
        st.error(f"❌ PDF 저장 오류: {e}")
        return False