# 📋 Prompt Blocks DSL 전체 내용 종합표

## 🎯 전체 블록 목록 (총 22개)

| 순서 | ID | 제목 | 설명 | 목표 | 역할 | 컨텍스트 |
|------|----|------|------|------|------|----------|
| 1 | principle_notice | 핵심 원칙 선언 및 유의사항 | 모든 분석에 앞서 적용되는 핵심 원칙과 유의사항 | AI 추론 기반 분석의 원칙 수립 | 원칙 수립자 | 모든 분석 전단계 |
| 2 | requirement_analysis | 요구사항 분석 및 분류 | 건축주의 명시적/암묵적 요구사항을 체계적으로 분석하고 분류하여 우선순위 도출 | 건축주 요구사항의 체계적 분석, 분류 및 우선순위 도출 | 요구사항 분석 및 분류 전문가 | 프로젝트 초기 단계에서 전체 설계 방향성의 기준점 마련 |
| 3 | task_comprehension | 과업 이해도 및 설계 주안점 | InnoScan 결과와 과업지시서를 종합 분석해 설계 전제조건, KPI, 제약조건 등을 정리 | 설계 전제조건, KPI, 제약조건, 이해관계자 요구사항 등을 명확히 정리 | 과업 이해도 분석 전문가 | 프로젝트 초기 단계에서 설계 방향성과 성공 기준을 명확히 정의 |
| 4 | site_regulation_analysis | 대지 환경 및 법규 분석 | 대상 대지의 잠재력과 제약사항을 다각적으로 분석해 후속 설계 전략의 현실적 기반을 마련 | 대지 및 인접 환경의 물리적·법적 조건을 종합적으로 분석 | 대지 분석 전문가 | 프로젝트 초기, 설계 가능성의 한계와 기회요소를 사전에 검증 |
| 5 | precedent_benchmarking | 사례 벤치마킹 및 인사이트 | 유사 프로젝트 사례를 분석해 설계 전략의 참고자료와 인사이트를 도출 | 유사 프로젝트 사례 분석을 통한 설계 전략 인사이트 도출 | 사례 분석 전문가 | 설계 전략 수립 전 단계에서 참고자료 확보 |
| 6 | design_trend_application | 디자인 트렌드 적용 | 최신 디자인 트렌드를 분석하고 프로젝트에 적용 가능한 요소들을 선별 | 최신 디자인 트렌드 분석 및 프로젝트 적용 가능 요소 선별 | 디자인 트렌드 전문가 | 설계 컨셉 개발 전 단계에서 트렌드 요소 확보 |
| 7 | mass_strategy | 매스 전략 및 체계 | 건물의 전체적인 매스 전략과 체계를 수립하여 설계의 기본 틀을 마련 | 건물의 전체적인 매스 전략과 체계 수립 | 매스 전략 전문가 | 설계의 기본 틀 마련 단계 |
| 8 | concept_development | 컨셉 개발 및 정립 | 프로젝트의 핵심 컨셉을 개발하고 정립하여 설계 방향성을 명확히 함 | 프로젝트의 핵심 컨셉 개발 및 정립 | 컨셉 개발 전문가 | 설계 방향성 명확화 단계 |
| 9 | schematic_space_plan | 스키매틱 공간 계획 | 건물의 스키매틱 공간 계획을 수립하여 기본 공간 구성을 정리 | 건물의 스키매틱 공간 계획 수립 | 공간 계획 전문가 | 기본 공간 구성 정리 단계 |
| 10 | design_requirement_summary | 설계 요구사항 종합 | 모든 설계 요구사항을 종합하여 최종 설계 가이드라인을 정리 | 모든 설계 요구사항 종합 및 최종 가이드라인 정리 | 설계 요구사항 종합 전문가 | 최종 설계 가이드라인 정리 단계 |
| 11 | area_programming | 면적 프로그래밍 | 각 공간별 적정 면적과 배분 원칙을 수립 | 각 공간별 적정 면적과 배분 원칙 수립 | 면적 프로그래밍 전문가 | 공간별 면적 배분 계획 단계 |
| 12 | cost_estimation | 비용 및 경제성 분석 | 공사비 모델과 변동요인을 분석하여 경제성을 평가 | 공사비 모델과 변동요인 분석 | 비용 분석 전문가 | 경제성 평가 단계 |
| 13 | architectural_branding_identity | 건축 브랜딩 및 아이덴티티 | 브랜딩과 차별화 메시지를 정렬하여 건축적 아이덴티티를 구축 | 브랜딩과 차별화 메시지 정렬 | 브랜딩 전문가 | 건축적 아이덴티티 구축 단계 |
| 14 | ux_circulation_simulation | UX 동선 시뮬레이션 | 시나리오별 동선을 시뮬레이션하여 사용자 경험을 최적화 | 시나리오별 동선 시뮬레이션 | UX 전문가 | 사용자 경험 최적화 단계 |
| 15 | flexible_space_strategy | 가변 공간 전략 | 가변/확장 원칙을 수립하여 유연한 공간 구성을 계획 | 가변/확장 원칙 수립 | 가변 공간 전문가 | 유연한 공간 구성 계획 단계 |
| 16 | doc_collector | 문서 수집 및 목차화 | 관련 문서를 수집하고 목차화하여 분석 기반을 마련 | 관련 문서 수집 및 목차화 | 문서 관리 전문가 | 분석 기반 마련 단계 |
| 17 | context_analyzer | 컨텍스트 분석 | 프로젝트의 컨텍스트를 분석하여 암묵적 의도와 KPI를 보정 | 프로젝트 컨텍스트 분석 | 컨텍스트 분석 전문가 | 암묵적 의도와 KPI 보정 단계 |
| 18 | requirements_extractor | 요구사항 추출 | 요구사항을 분류하고 우선순위를 도출 | 요구사항 분류 및 우선순위 도출 | 요구사항 추출 전문가 | 요구사항 정리 단계 |
| 19 | compliance_analyzer | 규정 준수 분석 | 필수 규정을 체크하고 준수 여부를 분석 | 필수 규정 체크 및 준수 여부 분석 | 규정 준수 전문가 | 규정 준수 확인 단계 |
| 20 | risk_strategist | 리스크 전략가 | 초기 리스크 레지스터를 작성하고 대응 전략을 수립 | 초기 리스크 레지스터 작성 및 대응 전략 수립 | 리스크 관리 전문가 | 리스크 관리 단계 |
| 21 | action_planner | 실행 계획 수립 | 실행 체크리스트를 작성하여 담당자와 기한을 정리 | 실행 체크리스트 작성 | 실행 계획 전문가 | 실행 계획 수립 단계 |
| 22 | competitor_analyzer | 경쟁사 분석 | 경쟁 포지션과 차별화 요소를 분석 | 경쟁 포지션 및 차별화 요소 분석 | 경쟁 분석 전문가 | 경쟁 분석 단계 |
| 23 | proposal_framework | 제안서 프레임워크 | 제안서 와이어프레임과 슬라이드 구조를 설계 | 제안서 와이어프레임 및 슬라이드 구조 설계 | 제안서 전문가 | 제안서 구조 설계 단계 |

---

## 📊 상세 분석 프레임워크

### 🔍 분석 접근법 (Approach)
| 블록 | 접근법 |
|------|--------|
| requirement_analysis | 체계적 요구사항 분석 (Kano 모델 + MoSCoW 우선순위 + 정량적 평가) + 구조화+체크리스트+표 혼합 |
| task_comprehension | 분석+정리형, 근거 기반 서술 |
| site_regulation_analysis | 객관적, 표 기반 요약과 근거 중심 해설 |
| precedent_benchmarking | 사례 분석 + 패턴 도출 + 적용 가능성 평가 |
| design_trend_application | 트렌드 분석 + 적용 가능성 평가 + 우선순위 설정 |
| mass_strategy | 매스 옵션 생성 + 평가 + 최적화 |
| concept_development | 컨셉 생성 + 평가 + 정립 |
| schematic_space_plan | 공간 분석 + 스키매틱 생성 + 평가 |
| design_requirement_summary | 요구사항 종합 + 가이드라인 정리 |
| area_programming | 면적 분석 + 배분 원칙 수립 |
| cost_estimation | 비용 모델링 + 변동요인 분석 |
| architectural_branding_identity | 브랜딩 분석 + 아이덴티티 구축 |
| ux_circulation_simulation | 동선 시뮬레이션 + UX 최적화 |
| flexible_space_strategy | 가변성 분석 + 확장 원칙 수립 |
| doc_collector | 문서 수집 + 목차화 + 분류 |
| context_analyzer | 컨텍스트 분석 + 암묵적 의도 도출 |
| requirements_extractor | 요구사항 추출 + 분류 + 우선순위 |
| compliance_analyzer | 규정 체크 + 준수 여부 분석 |
| risk_strategist | 리스크 식별 + 대응 전략 수립 |
| action_planner | 실행 계획 수립 + 체크리스트 작성 |
| competitor_analyzer | 경쟁 분석 + 차별화 전략 |
| proposal_framework | 제안서 구조 설계 + 와이어프레임 |

### 🛠️ 방법론 (Methodology)
| 블록 | 방법론 |
|------|--------|
| requirement_analysis | 문서 분석 + AI 추론 + 유사 사례 비교 + 이해관계자 관점 분석 + 요구사항 분류 + 우선순위 설정 + 심사 영향 분석 + 충족도 평가 |
| task_comprehension | 문서 분석 + 이해관계자 매핑 + 리스크 분석 |
| site_regulation_analysis | 물리적 환경 분석 + 인프라 평가 + 법규 검토 + SWOT 분석 |
| precedent_benchmarking | 사례 수집 + 패턴 분석 + 적용 가능성 평가 |
| design_trend_application | 트렌드 수집 + 분석 + 적용 가능성 평가 |
| mass_strategy | 매스 옵션 생성 + 평가 + 최적화 |
| concept_development | 컨셉 생성 + 평가 + 정립 |
| schematic_space_plan | 공간 분석 + 스키매틱 생성 + 평가 |
| design_requirement_summary | 요구사항 종합 + 가이드라인 정리 |
| area_programming | 면적 분석 + 배분 원칙 수립 |
| cost_estimation | 비용 모델링 + 변동요인 분석 |
| architectural_branding_identity | 브랜딩 분석 + 아이덴티티 구축 |
| ux_circulation_simulation | 동선 시뮬레이션 + UX 최적화 |
| flexible_space_strategy | 가변성 분석 + 확장 원칙 수립 |
| doc_collector | 문서 수집 + 목차화 + 분류 |
| context_analyzer | 컨텍스트 분석 + 암묵적 의도 도출 |
| requirements_extractor | 요구사항 추출 + 분류 + 우선순위 |
| compliance_analyzer | 규정 체크 + 준수 여부 분석 |
| risk_strategist | 리스크 식별 + 대응 전략 수립 |
| action_planner | 실행 계획 수립 + 체크리스트 작성 |
| competitor_analyzer | 경쟁 분석 + 차별화 전략 |
| proposal_framework | 제안서 구조 설계 + 와이어프레임 |

---

## 📋 출력 구조 (Output Structure)

### 🎯 주요 출력 섹션들
| 블록 | 주요 출력 섹션 |
|------|----------------|
| requirement_analysis | 요구사항 분석, 우선순위 정리, 사례 비교, 전략적 제언, A. 입찰 절차 요구사항, B. 설계 제안 발표 요구사항, C. 시설 계획 요구사항, D. 비용 및 유의사항, 요구사항 우선순위·핵심 체크포인트, 요구사항 충족도 평가, 대안 요구사항 제안 |
| task_comprehension | 키워드 매핑, 이해관계자 요구 매핑, 제약조건·리스크 대응 전략 |
| site_regulation_analysis | 대지 분석 종합, 대지 SWOT 분석, 개략 배치(조닝) 요약 |
| precedent_benchmarking | 사례 분석, 패턴 도출, 적용 가능성 평가 |
| design_trend_application | 트렌드 분석, 적용 가능성 평가, 우선순위 설정 |
| mass_strategy | 매스 옵션, 평가 결과, 최적화 방안 |
| concept_development | 컨셉 문장, 평가 기준, 정립 방안 |
| schematic_space_plan | 공간 구성, 스키매틱, 평가 결과 |
| design_requirement_summary | 요구사항 종합, 가이드라인, 체크리스트 |
| area_programming | 면적 배분, 원칙 정리, 적용 방안 |
| cost_estimation | 비용 모델, 변동요인, 경제성 평가 |
| architectural_branding_identity | 브랜딩 전략, 아이덴티티, 차별화 요소 |
| ux_circulation_simulation | 동선 시뮬레이션, UX 분석, 최적화 방안 |
| flexible_space_strategy | 가변성 분석, 확장 원칙, 적용 방안 |
| doc_collector | 문서 목록, 분류 체계, 분석 기반 |
| context_analyzer | 컨텍스트 분석, 암묵적 의도, KPI 보정 |
| requirements_extractor | 요구사항 분류, 우선순위, 추출 결과 |
| compliance_analyzer | 규정 체크, 준수 여부, 대응 방안 |
| risk_strategist | 리스크 레지스터, 대응 전략, 모니터링 |
| action_planner | 실행 계획, 체크리스트, 담당자 배정 |
| competitor_analyzer | 경쟁 분석, 차별화 전략, 포지셔닝 |
| proposal_framework | 제안서 구조, 와이어프레임, 슬라이드 구성 |

---

## 🎨 프레젠테이션 스타일

### 💬 언어 톤 (Language Tone)
| 블록 | 언어 톤 |
|------|---------|
| requirement_analysis | 객관적이고 실무적인 어조, 전문성 유지하되 이해하기 쉬운 표현, 설계 전략 중심의 건설적 제언, 실무적, 데이터 기반, 체크리스트 스타일 |
| task_comprehension | 객관적이고 실무적인 어조, 전문성 유지하되 이해하기 쉬운 표현 |
| site_regulation_analysis | 객관적, 설계 데이터 기반, 전문적 어조 |
| precedent_benchmarking | 객관적, 사례 기반, 비교 분석적 어조 |
| design_trend_application | 창의적, 트렌드 기반, 적용 중심 어조 |
| mass_strategy | 전략적, 체계적, 최적화 중심 어조 |
| concept_development | 창의적, 비전 중심, 정립적 어조 |
| schematic_space_plan | 체계적, 공간 중심, 설계적 어조 |
| design_requirement_summary | 종합적, 가이드라인 중심, 체크리스트 스타일 |
| area_programming | 정량적, 배분 중심, 원칙적 어조 |
| cost_estimation | 정량적, 경제성 중심, 분석적 어조 |
| architectural_branding_identity | 브랜딩 중심, 차별화 강조, 아이덴티티 어조 |
| ux_circulation_simulation | 사용자 중심, 경험 기반, 최적화 어조 |
| flexible_space_strategy | 유연성 중심, 확장 가능성 강조, 적응적 어조 |
| doc_collector | 체계적, 분류 중심, 관리적 어조 |
| context_analyzer | 분석적, 컨텍스트 중심, 해석적 어조 |
| requirements_extractor | 추출 중심, 분류적, 우선순위 어조 |
| compliance_analyzer | 규정 중심, 준수 강조, 검증적 어조 |
| risk_strategist | 리스크 중심, 대응 강조, 전략적 어조 |
| action_planner | 실행 중심, 계획적, 체크리스트 스타일 |
| competitor_analyzer | 경쟁 중심, 차별화 강조, 분석적 어조 |
| proposal_framework | 제안 중심, 구조적, 프레젠테이션 어조 |

### 🎯 대상 형식 (Target Format)
| 블록 | 대상 형식 |
|------|-----------|
| requirement_analysis | 각 섹션별로 표를 우선 제시한 후, 즉시 하단에 '해설' 소제목으로 4-8문장의 상세 서술 추가. 탭 라벨은 output_structure의 간단한 섹션명만 사용하여 UI 간소화 |
| task_comprehension | 각 섹션별 표 제시 후, 즉시 하단에 '해설' 소제목으로 4~8문장의 상세 서술 추가 |
| site_regulation_analysis | 각 섹션별 표 제시 후, 즉시 하단에 '해설' 소제목으로 4~8문장의 상세 서술 추가 |
| precedent_benchmarking | 표 기반 비교 분석 + 해설 구조 |
| design_trend_application | 트렌드 카드 + 적용 가능성 평가 |
| mass_strategy | 매스 옵션 비교 + 평가 매트릭스 |
| concept_development | 컨셉 카드 + 평가 기준 |
| schematic_space_plan | 스키매틱 도면 + 공간 분석 |
| design_requirement_summary | 종합 가이드라인 + 체크리스트 |
| area_programming | 면적 배분표 + 원칙 정리 |
| cost_estimation | 비용 분석표 + 경제성 평가 |
| architectural_branding_identity | 브랜딩 전략 + 아이덴티티 가이드 |
| ux_circulation_simulation | 동선 다이어그램 + UX 분석 |
| flexible_space_strategy | 가변성 분석 + 확장 원칙 |
| doc_collector | 문서 목록 + 분류 체계 |
| context_analyzer | 컨텍스트 분석 + 암묵적 의도 |
| requirements_extractor | 요구사항 분류 + 우선순위 |
| compliance_analyzer | 규정 체크 + 준수 여부 |
| risk_strategist | 리스크 레지스터 + 대응 전략 |
| action_planner | 실행 계획 + 체크리스트 |
| competitor_analyzer | 경쟁 분석 + 차별화 전략 |
| proposal_framework | 제안서 구조 + 와이어프레임 |

---

## 🔧 품질 기준 (Quality Standards)

### ⚠️ 제약사항 (Constraints)
모든 블록에서 공통적으로 적용되는 제약사항:
- 모든 AI 기반 추론은 반드시 '(AI 추론)' 표시 후 근거와 함께 제시
- 실행 가능하고 구체적인 제언만 포함 (담당자, 일정, 예산 포함)
- 모든 분석 결과는 구체적인 근거와 출처 페이지/원문 인용 필수
- 각 섹션의 표 하단에 해설 추가 (최소 4문장, 최대 8문장, 300-600자)
- 해설에는 분석 방법론, AI 추론 과정, 문서 근거, 결론 및 한계점 포함
- 표 형식만으로 완료하지 말고 반드시 서술형 해설로 보완
- 전체 문서 분량 1000자 이상 작성
- 모든 표는 명확한 매트릭스로 제시하고 각 항목의 근거·출처를 기재
- 누락된 정보 또는 추정치는 반드시 '(AI 추론)'으로 표기하고 근거 기술

### 📝 필수 문구 (Required Phrases)
모든 블록에서 공통적으로 사용되는 필수 문구:
- "(AI 추론): 인공지능 기반 분석임을 명시"
- "실행 가능한 제언: 구체적이고 실현 가능한 권고사항"
- "표 형식으로 정리: 정보의 체계적 구성"
- "근거·출처: 분석 결과의 신뢰성 확보"
- "결론: 핵심 분석 결과 요약"
- "한계와 다음 단계: 분석의 제한점 및 후속 과제"

### ✅ 검증 규칙 (Validation Rules)
각 블록별 특화된 검증 규칙들이 적용되며, 공통적으로:
- 분석 근거의 명확성
- 실현 가능성 검증
- 추론 과정의 투명성
- 결과의 일관성
- 적용 가능성 검증

---

## 🎨 시각적 요소 (Visual Elements)

### 📊 주요 시각화 요소들
| 블록 | 시각적 요소 |
|------|-------------|
| requirement_analysis | 요구사항 매트릭스, 우선순위 다이어그램, 실행 체크리스트, 리스크 맵, 요구사항 분류 매트릭스, 충족도 평가 차트 |
| task_comprehension | 키워드 클라우드, 이해관계자 맵, 리스크 매트릭스 |
| site_regulation_analysis | 대지 분석 다이어그램, SWOT 매트릭스, 조닝 계획도 |
| precedent_benchmarking | 사례 비교표, 패턴 분석 차트, 적용 가능성 매트릭스 |
| design_trend_application | 트렌드 카드, 적용 가능성 평가표, 우선순위 차트 |
| mass_strategy | 매스 옵션 비교표, 평가 매트릭스, 최적화 다이어그램 |
| concept_development | 컨셉 카드, 평가 기준표, 정립 프로세스 |
| schematic_space_plan | 스키매틱 도면, 공간 분석표, 구성 평가 |
| design_requirement_summary | 종합 가이드라인, 체크리스트, 요구사항 맵 |
| area_programming | 면적 배분표, 원칙 정리표, 적용 방안 |
| cost_estimation | 비용 분석표, 경제성 평가 차트, 변동요인 분석 |
| architectural_branding_identity | 브랜딩 전략 맵, 아이덴티티 가이드, 차별화 요소 |
| ux_circulation_simulation | 동선 다이어그램, UX 분석표, 최적화 방안 |
| flexible_space_strategy | 가변성 분석표, 확장 원칙, 적용 방안 |
| doc_collector | 문서 목록, 분류 체계도, 분석 기반 |
| context_analyzer | 컨텍스트 분석 맵, 암묵적 의도 도출, KPI 보정 |
| requirements_extractor | 요구사항 분류표, 우선순위 차트, 추출 결과 |
| compliance_analyzer | 규정 체크표, 준수 여부 분석, 대응 방안 |
| risk_strategist | 리스크 레지스터, 대응 전략 맵, 모니터링 |
| action_planner | 실행 계획표, 체크리스트, 담당자 배정 |
| competitor_analyzer | 경쟁 분석표, 차별화 전략, 포지셔닝 |
| proposal_framework | 제안서 구조도, 와이어프레임, 슬라이드 구성 |

---

## 📝 섹션 템플릿 (Section Templates)

각 블록은 고유한 섹션 템플릿을 가지고 있으며, 각 템플릿은 다음 구조를 포함합니다:

### 📋 표 구조 (Table Structure)
- **table_title**: 표의 제목
- **required_columns**: 필수 컬럼 목록
- **narrative_template**: 서술형 해설 템플릿

### 🔄 해설 템플릿 (Narrative Template)
모든 블록에서 공통적으로 사용되는 해설 템플릿:
"분석 방법론 소개 → (AI 추론) 핵심 인사이트 도출 → 구체적 근거·출처 제시 → 종합 결론 · 분석의 한계점 · 다음 단계 과제"

---

## 🎯 소스 데이터 (Source)

각 블록이 활용하는 소스 데이터:
- **user_inputs**: 사용자 입력 정보
- **pdf_summary**: PDF 요약 정보
- **previous_analysis**: 이전 분석 결과
- **과업지시서**: 과업 관련 문서
- **InnoScan 결과**: InnoScan 분석 결과
- **이해관계자 인터뷰**: 이해관계자 인터뷰 자료

---

## 📊 작업 목록 (Tasks)

각 블록은 고유한 작업 목록을 가지고 있으며, 이는 해당 블록의 핵심 기능을 정의합니다. 작업 목록은 블록별로 4-8개의 세부 작업으로 구성되어 있습니다.

---

*이 표는 prompt_blocks_dsl.json 파일의 모든 블록 내용을 종합적으로 정리한 것입니다. 각 블록은 고유한 ID, 제목, 설명, 목표, 역할, 컨텍스트, 분석 프레임워크, 출력 구조, 품질 기준, 프레젠테이션 스타일, 시각적 요소, 섹션 템플릿을 가지고 있으며, 이는 AI 기반 건축 설계 분석 시스템의 핵심 구성 요소입니다.*
