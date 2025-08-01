# search_helper.py
import requests
import os

SERP_API_KEY = os.environ.get("SERP_API_KEY")

def search_web_serpapi(query):
    params = {
        "q": query,
        "api_key": SERP_API_KEY,
        "engine": "google",
        "num": 3
    }
    resp = requests.get("https://serpapi.com/search", params=params)
    data = resp.json()
    if "organic_results" in data:
        results = data["organic_results"]
        return "\n---\n".join([f"{r['title']}\n{r.get('snippet', '')}" for r in results])
    else:
        return "[검색 결과 없음]"