# app.py
import streamlit as st
from agent_executor import InniAgent
from prompt_loader import load_prompt_blocks
from user_state import (
    init_user_state, get_user_inputs, set_pdf_summary,
    get_pdf_summary, save_step_result,
    get_current_step_index, next_step
)
from utils import extract_text_from_pdf, merge_prompt_content
from utils import extract_summary, extract_insight  # 상단 import 필요
from dsl_to_prompt import convert_dsl_to_prompt
from streamlit_sortables import sort_items
from summary_generator import summarize_pdf, extract_site_analysis_fields
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from user_state import append_step_history  # 🔺 파일 상단 import도 추가하세요
from difflib import SequenceMatcher
from utils_pdf_vector import save_pdf_chunks_to_chroma
import dspy
from dotenv import load_dotenv
import os
load_dotenv()
print("ANTHROPIC_API_KEY:", os.environ.get("ANTHROPIC_API_KEY"))

if not getattr(dspy.settings, "lm", None):
    lm = dspy.LM("claude-3-opus", provider="anthropic")
    dspy.configure(lm=lm, track_usage=True)


def is_duplicate_content(prev_result, curr_result):
    # 표(항목, 내용)만 추출해서 유사도 측정
    def table_text(s):
        return "\n".join([line for line in s.split('\n') if '|' in line])
    ratio = SequenceMatcher(None, table_text(prev_result), table_text(curr_result)).ratio()
    return ratio > 0.8  # 유사도 80% 이상이면 중복


# ─── 초기화 ─────────────────────────────────────────────
init_user_state()
st.set_page_config(page_title="Inni Analyzer", layout="wide")
st.title("📊 Inni Analyzer: 흐름＋순서 커스터마이징")

# ─── 1. 사용자 입력 & PDF 업로드 ─────────────────────────
st.sidebar.header("📥 프로젝트 기본 정보 입력")
user_inputs = get_user_inputs()

uploaded_pdf = st.sidebar.file_uploader("📎 PDF 업로드", type=["pdf"])
if uploaded_pdf:
    # ▶ 1. 바이트 데이터 먼저 저장!
    pdf_bytes = uploaded_pdf.read()

    # ▶ 2. 임시파일로 저장
    temp_path = "temp_uploaded.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_bytes)
    save_pdf_chunks_to_chroma(temp_path, pdf_id="projectA")
    st.sidebar.success("✅ PDF 벡터DB 저장 완료!")

    # ▶ 3. PDF 텍스트 추출, 요약 등도 저장한 바이트로!
    from utils import extract_text_from_pdf
    pdf_text = extract_text_from_pdf(pdf_bytes)   # ← pdf_file → pdf_bytes로 수정
    pdf_summary = summarize_pdf(pdf_text)
    set_pdf_summary(pdf_summary)
    st.session_state["site_fields"] = extract_site_analysis_fields(pdf_text)
    st.sidebar.success("✅ PDF 요약 완료!")

# ─── 2. 블럭 로드 & 단계 선택 ───────────────────────────
blocks       = load_prompt_blocks()
extra_blocks = blocks["extra"]
blocks_by_id = {b["id"]: b for b in extra_blocks}

st.sidebar.markdown("🔲 **분석에 포함할 단계 선택**")
selected_ids = []
for blk in extra_blocks:
    if st.sidebar.checkbox(blk["title"], key=f"sel_{blk['id']}"):
        selected_ids.append(blk["id"])


# ─── 3. 선택된 블럭 순서 조정 ────────────────────────────
if selected_ids:
    # ① 선택된 블럭 객체 리스트
    selected_blocks = [blocks_by_id[sid] for sid in selected_ids]

    # ② 제목 문자열 리스트로 변환
    titles = [blk["title"] for blk in selected_blocks]

    # ③ 스트링 리스트를 드래그 가능하게 정렬
    sort_key = "block_sorter_" + "_".join(selected_ids)
    ordered_titles = sort_items(titles, key=sort_key)

    # ④ 정렬된 제목 순서대로 블럭 객체 재구성
    ordered_blocks = [next(blk for blk in selected_blocks if blk["title"] == t)
                      for t in ordered_titles]

    # ⑤ 화면에 박스로 표시
    cols = st.columns(len(ordered_blocks))
    for col, blk in zip(cols, ordered_blocks):
        col.markdown(
            f"<div style='background:#e63946; color:white; "
            f"padding:8px; border-radius:4px; text-align:center;'>"
            f"{blk['title']}</div>",
            unsafe_allow_html=True,
        )
    st.markdown("---")
else:
    ordered_blocks = []


# ─── 4. 누적된 이전 분석 결과 ───────────────────────────
if st.session_state.cot_history:
    st.markdown("### 🧠 누적 분석 결과")
    for entry in st.session_state.cot_history:
        st.markdown(f"#### {entry['step']}")
        st.markdown(f"**요약:** {entry.get('summary', '')}")
        st.markdown(f"**인사이트:** {entry.get('insight', '')}")
        st.markdown(f"---\n{entry['result']}")
        st.markdown("---")

# ─── 5. 명령어 기반 분석 흐름 ─────────────────────────────
cmd = st.text_input("▶ 명령어 입력 (예: 시작 / 분석 진행 / N단계 진행 / 보고서 생성)")

if cmd.strip() == "시작":
    st.session_state.current_step_index = 0
    st.session_state.cot_history = []
    st.success("모든 입력이 완료되었습니다. ‘분석 진행’을 입력하세요.")

elif cmd.strip() == "분석 진행" or cmd.strip().endswith("단계 진행"):
    # 실행할 단계 번호 결정
    if cmd.strip() == "분석 진행":
        idx = get_current_step_index()
    else:
        try:
            idx = int(cmd.strip().replace("단계 진행", "")) - 1
        except ValueError:
            st.error("‘N단계 진행’ 형식으로 입력해주세요.")
            idx = None

    # 유효성 검사
    if idx is not None and 0 <= idx < len(ordered_blocks):
        blk = ordered_blocks[idx]

        # 이전 결과 전체 병합
        prev = "\n".join(f"[{h['step']}] {h['result']}"
                         for h in st.session_state.cot_history)

        site_fields = None
        if blk["id"] == "site_and_regulation_analysis":
            site_fields = st.session_state.get("site_fields")
            # 디버깅: site_fields 상태 확인
            st.info(f"🔍 두 번째 단계 실행 - site_fields: {site_fields is not None}")

        prompt_tpl = convert_dsl_to_prompt(
            dsl_block=blk["content_dsl"],
            user_inputs=user_inputs,
            previous_summary=prev,
            pdf_summary=get_pdf_summary(),
            site_fields=site_fields
        )

        # 전체 프롬프트 합성
        full_prompt = merge_prompt_content(
            block_prompt=prompt_tpl,
            user_info=user_inputs,
            pdf_summary=get_pdf_summary(),
            step_context=prev
        )

        # 화면에 표시
        st.markdown(f"### ▶ {blk['title']}")
        st.code(full_prompt, language="markdown")

        # GPT 분석 실행
        with st.spinner("🔎 분석 중..."):
            result = InniAgent("CoT").run_analysis(full_prompt)
        # 🟦 중복 감지/Refine(이전 단계와 표 내용 80% 이상 동일시)
        if st.session_state.cot_history:
            prev = st.session_state.cot_history[-1]["result"]
            if is_duplicate_content(prev, result):
                st.warning("이전 단계와 분석 내용이 너무 유사합니다. 본 단계만의 신규 데이터·비교·분석을 추가하세요.")
                # Self-Refine: GPT에게 "이전 단계와 중복 금지, 반드시 신규 분석" 지시문 추가 후 재호출
                new_prompt = full_prompt + "\n\n⚠️ 반드시 직전 단계 표/내용과 중복 없이 본 단계 고유의 비교, 수치, 법규, 리스크, 차별화 분석만 포함하세요."
                result = InniAgent("CoT").run_analysis(new_prompt)


        # 중복 검사
        if st.session_state.cot_history:
            prev_result = st.session_state.cot_history[-1]['result']
            if is_duplicate_content(prev_result, result):
                st.warning("이전 결과와 유사한 내용이 있습니다. 중복 방지를 위해 결과를 수정해주세요.")
                st.stop()

        st.success("✅ 분석 완료")
        st.markdown(result)

        # 결과 누적
        st.session_state.cot_history.append({
            "step": blk["title"],
            "result": result,
            "summary": extract_summary(result),
            "insight": extract_insight(result)
        })
        save_step_result(blk["id"], result)

        # ⬇️ step_history에도 요약 및 인사이트 포함해 누적
        append_step_history(
            step_id=blk["id"],
            title=blk["title"],
            prompt=full_prompt,
            result=result
        )

        # 단계 인덱스 업데이트
        if cmd.strip() == "분석 진행":
            next_step()
        else:
            st.session_state.current_step_index = idx + 1

        # 다음 안내
        if st.session_state.current_step_index < len(ordered_blocks):
            st.info(
                f"■ ‘{blk['title']}’ 완료. 다음: "
                f"‘{st.session_state.current_step_index+1}단계 진행’"
            )
        else:
            st.info("■ 모든 단계 완료! ‘보고서 생성’을 입력하세요.")
    else:
        st.warning("유효한 단계가 아닙니다. 선택된 단계와 순서를 확인해주세요.")

elif cmd.strip() == "보고서 생성":
    cot = st.session_state.cot_history
    if cot:
        # Markdown 다운로드
        md = "# Inni Analyzer 보고서\n\n"
        for s in cot:
            md += f"## {s['step']}\n\n{s['result']}\n\n---\n\n"
        st.sidebar.download_button("📥 Markdown 다운로드", md, "inni_report.md", "text/markdown")

        # PDF 다운로드
        buf = BytesIO()
        # 한글 폰트 등록
        pdfmetrics.registerFont(TTFont('NanumGothic', 'NanumGothicCoding.ttf'))
        c = canvas.Canvas(buf)
        y = 800
        c.setFont('NanumGothic', 12)
        for s in cot:
            c.drawString(50, y, s["step"])
            y -= 20
            for line in s["result"].split("\n"):
                c.drawString(60, y, line[:80])
                y -= 15
                if y < 50:
                    c.showPage()
                    y = 800
            y -= 10
        c.save()
        buf.seek(0)
        st.sidebar.download_button("📥 PDF 다운로드", buf, "inni_report.pdf", "application/pdf")
        st.success("보고서가 생성되었습니다.")
    else:
        st.warning("분석된 결과가 없습니다. 먼저 단계를 실행해주세요.")
