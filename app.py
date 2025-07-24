import streamlit as st
from agent_executor import InniAgent
from prompt_loader import load_prompt_blocks
from user_state import (
    get_user_inputs, set_pdf_summary,
    get_pdf_summary, save_step_result, init_user_state
)
from utils import extract_text_from_pdf, merge_prompt_content
from dsl_to_prompt import convert_dsl_to_prompt
from streamlit_sortables import sort_items
from io import BytesIO
from reportlab.pdfgen import canvas
from summary_generator import summarize_pdf


init_user_state()
st.set_page_config(page_title="Inni Analyzer MVP", layout="wide")

st.title("📊 Inni Analyzer: GPT-4o 기반 건축 프로젝트 분석")

# ─── 1. 사용자 입력 & PDF 업로드 ─────────────────────────────
st.sidebar.header("📥 프로젝트 기본 정보 입력")
user_inputs = get_user_inputs()
uploaded_pdf = st.sidebar.file_uploader("📎 PDF 업로드", type=["pdf"])
if uploaded_pdf:
    pdf_text    = extract_text_from_pdf(uploaded_pdf)
    pdf_summary = summarize_pdf(pdf_text)   # 이제 .output을 반환하므로 에러 없음
    set_pdf_summary(pdf_summary)
    st.sidebar.success("✅ PDF 요약 완료!")

# ─── 1‑1. 분석 방식 여러 개 선택 ────────────────────────────────────
methods = st.sidebar.multiselect(
    "🔧 분석 방식 (여러 개 선택 가능)",
    ["CoT", "BootstrapFewShot", "ReAct"],
    default=["CoT", "BootstrapFewShot", "ReAct"]
)

# ─── 2. 블럭 로드 (core vs extra) ────────────────────────────
blocks_dict  = load_prompt_blocks()  
core_blocks  = blocks_dict["core"]      # 고정 블럭 리스트
extra_blocks = blocks_dict["extra"]     # 체크박스로 선택할 나머지 블럭
extra_ids    = [b["id"] for b in extra_blocks]
blocks_by_id = {b["id"]: b for b in extra_blocks}

# ─── 3. 화면 상단에 고정 블럭 태그 ───────────────────────────
cols = st.columns(len(core_blocks))
for col, block in zip(cols, core_blocks):
    col.markdown(
        f"<span style='background:#006d77;color:white;"
        f"padding:4px 8px;border-radius:4px;'>{block['title']}</span>",
        unsafe_allow_html=True
    )
st.markdown("---")

# ─── 4. 사이드바: Drag&Drop + 체크박스 ───────────────────────
st.sidebar.markdown("🔍 **블럭 순서 조정 (Drag & Drop)**")
ordered_extra_ids = sort_items(extra_ids, key="block_sorter")

selected_ids = []
for bid in ordered_extra_ids:
    title = blocks_by_id[bid]["title"]
    if st.sidebar.checkbox(title, value=False, key=f"select_{bid}"):
        selected_ids.append(bid)

selected_blocks = [blocks_by_id[sid] for sid in selected_ids]

# ─── 5. 메인에 선택된 블럭 태그 ──────────────────────────────
if selected_blocks:
    cols = st.columns(len(selected_blocks))
    for col, block in zip(cols, selected_blocks):
        col.markdown(
            f"<span style='background:#e63946;color:white;"
            f"padding:4px 8px;border-radius:4px;'>{block['title']}</span>",
            unsafe_allow_html=True
        )
    st.markdown("---")

# ─── 6. 분석 실행 버튼 & 로직 ───────────────────────────────
if selected_blocks and st.button("🚀 선택한 블럭들 분석 실행"):
    st.session_state.cot_history = []
    for idx, block in enumerate(selected_blocks):
        step_id = block["id"]
        title   = block["title"]

        # 이전 코트 히스토리
        prev = "\n".join([f"[{h['step']}] {h['result']}" 
                          for h in st.session_state.cot_history])

        # DSL or 고정 content
        if "content_dsl" in block:
            prompt_tpl = convert_dsl_to_prompt(
                dsl_block=block["content_dsl"],
                user_inputs=user_inputs,
                previous_summary=prev,
                pdf_summary=get_pdf_summary()
            )
        else:
            prompt_tpl = block["content"]

        st.markdown(f"### 📘 Step {idx+1}: {title}")
        st.code(prompt_tpl, language="markdown")

        full_prompt = merge_prompt_content(
            block_prompt=prompt_tpl,
            user_info=user_inputs,
            pdf_summary=get_pdf_summary(),
            step_context=prev
        )

# **여기부터 변경**: 고른 모든 분석 방식(method)에 대해 실행
        for method in methods:
            st.markdown(f"#### ⚙️ 방식: {method}")
            with st.spinner(f"🔎 {method} 분석 중..."):
                agent  = InniAgent(method)
                result = agent.run_analysis(full_prompt)
            st.success(f"✅ {method} 분석 완료!")
            st.markdown(result)
            # 결과 저장 (cot_history에 기록할 때도 방식 구분)
            entry = {
                "step":   f"Step {idx+1} ({method})",
                "title":  block["title"],
                "method": method,
                "prompt": full_prompt,
                "result": result
            }
            st.session_state.cot_history.append(entry)
            save_step_result(f"{block['id']}_{method}", result)

   
    # 전체 흐름 요약
    if len(st.session_state.cot_history) > 1:
        st.markdown("---")
        st.markdown("### 🧠 전체 분석 흐름 요약")
        for i, h in enumerate(st.session_state.cot_history):
            st.markdown(f"**{i+1}. {h['title']}**")
            st.markdown(f"- {h['result'][:200]}...")

# ─── 7. MD / PDF 다운로드 ────────────────────────────────────
cot = st.session_state.cot_history
if cot:
    # Markdown
    md = "# Inni Analyzer 보고서\n\n"
    for s in cot:
        md += f"## {s['title']}\n\n{s['result']}\n\n---\n\n"
    st.sidebar.download_button(
        "📥 Markdown 다운로드",
        data=md, file_name="inni_report.md",
        mime="text/markdown"
    )

    # PDF
    buf = BytesIO()
    c   = canvas.Canvas(buf)
    y   = 800
    c.setFont("Helvetica", 12)
    for s in cot:
        c.drawString(50, y, s["title"])
        y -= 20
        for line in s["result"].split("\n"):
            c.drawString(60, y, line[:80])
            y -= 15
            if y < 50:
                c.showPage(); y = 800
        y -= 10
    c.save(); buf.seek(0)
    st.sidebar.download_button(
        "📥 PDF 다운로드",
        data=buf, file_name="inni_report.pdf",
        mime="application/pdf"
    )
