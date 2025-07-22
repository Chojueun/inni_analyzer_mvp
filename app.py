import streamlit as st
import os
import requests
from dotenv import load_dotenv

# .env에서 API 키 불러오기
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")

st.title("Inni Analyzer MVP - DeepSeek 버전")

uploaded_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())
    st.success("PDF 업로드 완료!")

    if st.button("기본 분석 실행"):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        data = {
            "model": "deepseek-chat",  # 또는 deepseek-llm
            "messages": [
                {"role": "system", "content": "당신은 건축 전문가입니다. 분석 리포트를 써주세요."},
                {"role": "user", "content": "대지 분석 보고서를 써줘. PDF 내용은 생략하고 샘플만 출력해줘."}
            ]
        }

        res = requests.post("https://api.deepseek.com/v1/chat/completions", headers=headers, json=data)

        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"]
            st.markdown("## 분석 결과")
            st.write(content)
        else:
            st.error(f"오류 발생: {res.status_code}")
            st.text(res.text)
