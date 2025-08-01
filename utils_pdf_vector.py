#utils_pdf_vector.py

import chromadb
import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer

# 1. 임베딩 모델 로드 (가볍고 무료)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# 2. ChromaDB 인스턴스
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("pdf_chunks")

def search_pdf_chunks(query, top_k=3):
    try:
        q_embed = embedder.encode([query])[0].tolist()
        result = collection.query(query_embeddings=[q_embed], n_results=top_k)
        if result and "documents" in result and result["documents"][0]:
            chunks = result["documents"][0]
            return "\n---\n".join(chunks)
        else:
            return "[PDF 인용 근거 없음]"
    except Exception as e:
        return f"[PDF 검색 오류: {e}]"

def pdf_to_chunks(pdf_path, chunk_size=400):
    doc = fitz.open(pdf_path)
    all_chunks = []
    for page in doc:
        text = page.get_text()
        # 문단 단위로 split, 너무 길면 chunk_size씩 자름
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size].strip()
            if len(chunk) > 50:  # 너무 짧은 것 제외
                all_chunks.append(chunk)
    return all_chunks

def save_pdf_chunks_to_chroma(pdf_path, pdf_id="pdf1"):
    chunks = pdf_to_chunks(pdf_path)
    embeds = embedder.encode(chunks).tolist()
    ids = [f"{pdf_id}_{i}" for i in range(len(chunks))]
    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeds
    )
    print(f"PDF {pdf_id}: {len(chunks)} chunks 저장")

# 예시: save_pdf_chunks_to_chroma("uploaded_file.pdf", pdf_id="projectA")
