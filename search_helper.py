# search_helper.py
import requests

def search_web(query: str) -> str:
    """
    웹 검색 또는 문서 검색 기능을 위한 placeholder 함수.
    향후 RAG 등과 연동 시 여기에 구현.
    현재는 더미 응답 반환.
    """
    # 향후 검색 API 연동 시 여기에 로직 추가
    # 예: SerpAPI, Bing, Naver, Arxiv 등
    
    dummy_result = f"[검색 결과: '{query}'에 대한 요약 정보는 추후 구현 예정입니다.]"
    return dummy_result
