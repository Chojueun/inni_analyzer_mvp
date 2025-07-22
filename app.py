import streamlit as st
# from pdf_parser import parse_pdf   # <<<<< 일단 주석!
# from llm_executor import run_daji_analysis   # <<<<< 일단 주석!
from openai import OpenAI
import openai
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.title("Inni Analyzer MVP (기본 실행)")

uploaded_file = st.file_uploader("PDF 파일 업로드", type=["pdf"])

if uploaded_file:
    with open("temp.pdf", "wb") as f:
        f.write(uploaded_file.read())

    st.write("PDF 업로드 완료!")

    if st.button("기본 분석 실행"):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "당신은 건축 분석 AI입니다."},
                {"role": "user", "content": "대지 분석 보고서를 생성하세요. PDF 내용은 생략하고 테스트만 합니다."}
            ]
        )
        st.markdown("## 분석 결과")
        st.write(response.choices[0].message.content)

