# ArchInsight - AI-driven Project Insight & Workflow

건축 프로젝트 분석을 위한 AI 기반 워크플로우 시스템입니다.

## 주요 기능

- **프로젝트 정보 입력**: 프로젝트명, 건축주, 대지위치, 건물용도 등 기본 정보 입력
- **PDF 문서 분석**: 업로드된 PDF 문서의 텍스트 추출 및 벡터 데이터베이스 저장
- **AI 기반 분석**: DSPy를 활용한 건축 프로젝트 분석
- **워크플로우 관리**: 용도별, 목적별 맞춤형 분석 단계 구성
- **보고서 생성**: PDF, Word, TXT 형식의 분석 보고서 생성
- **웹페이지 생성**: Card 형식의 반응형 웹페이지 생성

## 설치 방법

1. 의존성 설치:
```bash
pip install -r requirements.txt
```

2. 환경 변수 설정:
```bash
# .env 파일 생성
ANTHROPIC_API_KEY=your_anthropic_api_key
SERP_API_KEY=your_serpapi_key
```

3. 애플리케이션 실행:
```bash
streamlit run app.py
```

## 사용 방법

1. **프로젝트 정보 입력**: 프로젝트 기본 정보와 PDF 문서 업로드
2. **용도 및 목적 선택**: 건축 용도와 분석 목적 선택
3. **워크플로우 구성**: 자동 제안된 분석 단계를 필요에 따라 수정
4. **분석 실행**: 각 단계별로 AI 분석 수행
5. **결과 확인**: 분석 결과를 다양한 형식으로 다운로드

## 파일 구조

- `app.py`: 메인 애플리케이션
- `workflow_ui.py`: 워크플로우 UI 관리
- `analysis_system.py`: 분석 시스템 핵심 로직
- `agent_executor.py`: AI 에이전트 실행
- `dsl_to_prompt.py`: DSL을 프롬프트로 변환
- `utils.py`: 유틸리티 함수들
- `utils_pdf_vector.py`: PDF 벡터 처리
- `report_generator.py`: 보고서 생성
- `webpage_generator.py`: 웹페이지 생성
- `user_state.py`: 사용자 상태 관리
- `summary_generator.py`: 요약 생성
- `search_helper.py`: 웹 검색 도우미
- `init_dspy.py`: DSPy 초기화

## 주요 기술 스택

- **Streamlit**: 웹 인터페이스
- **DSPy**: AI 프롬프트 관리
- **Anthropic Claude**: AI 모델
- **ChromaDB**: 벡터 데이터베이스
- **PyMuPDF**: PDF 처리
- **ReportLab**: PDF 생성
- **python-docx**: Word 문서 생성

## 라이선스

MIT License