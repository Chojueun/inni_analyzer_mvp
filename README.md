Inni Analyzer MVP

GPT-4o 기반 건축 프로젝트 분석 도구

프로젝트 개요

Inni Analyzer는 사용자가 업로드한 PDF(과업지시서, RFP 등)와 기본 프로젝트 정보를 바탕으로, 건축 프로젝트의 단계별 심층 분석을 자동화하는 Streamlit 애플리케이션입니다. DSPy(Declarative Self‑improving Python)를 활용해 여러 체인(CoT, BootstrapFewShot, ReAct) 방식으로 분석을 수행하고, 각 단계 결과를 체인 오브 사고(Chain‑of‑Thought) 방식으로 누적·요약합니다.

주요 기능

PDF 요약: 원문 PDF 텍스트를 추출 후 DSPy CoT 기반 요약 모듈로 간결하게 압축

분석 블럭: 프로젝트 정보 요약, 법적 조건 분석, 시장 조사 등 JSON으로 정의된 다수 블럭

체인 방식 선택: CoT, BootstrapFewShot, ReAct 중 필요에 따라 멀티 선택

블럭 순서 조정: Drag & Drop + 체크박스로 단계별 실행 순서 변경

분석 실행: 선택된 블럭과 방식별로 GPT 분석 동시 실행 및 결과 비교

체인 누적: 각 단계 결과를 session_state에 저장, 전체 흐름을 Chain‑of‑Thought로 요약

결과 다운로드: Markdown 및 PDF 형태로 전체 분석 리포트 다운로드

파일 구조

inni_analyzer_mvp/
├─ app.py               # Streamlit UI 및 실행 로직
├─ agent_executor.py    # DSPy Module, CoT/Bootstrap/ReAct 체인 정의
├─ dsl_to_prompt.py     # DSL 블럭 → 프롬프트 변환 함수
├─ prompt_loader.py     # 고정(core) 블럭 + 선택(extra) 블럭 로드
├─ summary_generator.py # DSPy CoT 기반 PDF 요약 시그니처
├─ user_state.py        # Streamlit session_state 초기화/저장 함수
├─ utils.py             # PDF 추출, 텍스트 정제, 프롬프트 병합 헬퍼
├─ prompt_blocks_dsl.json  # 분석 블럭 DSL 정의 파일
├─ requirements.txt     # 의존성 목록
└─ README.md            # 프로젝트 문서 (현재 파일)

설치 및 실행

# 1. 레포지토리 클론 및 환경 설정
git clone https://github.com/your_org/inni_analyzer_mvp.git
cd inni_analyzer_mvp
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\activate

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경변수 설정
# 프로젝트 루트에 .env 파일을 생성하고 OpenAI API 키를 추가
echo "OPENAI_API_KEY=your_api_key_here" > .env

# 4. 앱 실행
streamlit run app.py

사용 방법

    사이드바에서 프로젝트 기본 정보 입력 (건축주, 대상지, 목표 등)

    PDF 업로드 후 자동 요약 완료 메시지 확인

    분석 방식(CoT, BootstrapFewShot, ReAct) 멀티 선택

    블럭 순서 조정 및 체크박스로 분석 대상 블럭 선택

    메인 화면에서 🚀 분석 실행 버튼 클릭

    각 단계별 결과를 확인하고, 하단에서 Markdown/PDF 리포트 다운로드

확장 및 커스터마이징

    블럭 추가: prompt_blocks_dsl.json 에 DSL 형식으로 블럭 정의 추가

    분석 체인: agent_executor.py 에 ReAct 외 추가 DSPy 체인 로직 구현

    UI 커스터마이징: Streamlit 컴포넌트 교체 및 스타일링

    RAG 연동: search_helper.py 에 검색 API 통합 후 툴 호출

라이선스

     프로젝트의 모든 권리는 프로젝트 작성자 조주은에게 있습니다. 2025.