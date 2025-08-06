#analysis_system.py

"""
분석 시스템 핵심 구조
- 용도/목적 분류
- 단계 자동 제안
- 필수 단계 포함
- 번외 항목 추가
- 순서 변경 및 추가/삭제
- 전체 순서 확정 및 분석 실행
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class PurposeType(Enum):
    """용도 분류"""
    OFFICE = "Office"
    RESIDENTIAL = "주거"
    COMMERCIAL = "상업"
    CULTURAL = "문화"
    EDUCATIONAL = "교육"
    MEDICAL = "의료"
    INDUSTRIAL = "산업"
    MIXED_USE = "복합용도"
    OTHER = "기타"

class ObjectiveType(Enum):
    """목적 분류"""
    MARKET_ANALYSIS = "상권분석"
    DESIGN_GUIDELINE = "Design가이드라인"
    MASS_STRATEGY = "Mass"
    COST_ANALYSIS = "원가분석"
    OPERATION_STRATEGY = "운영전략"
    BRANDING = "브랜딩"
    LEGAL_REVIEW = "법적검토"
    SPACE_PLANNING = "공간계획"
    OTHER = "기타"

@dataclass
class AnalysisStep:
    """분석 단계 정보"""
    id: str
    title: str
    description: str
    is_required: bool = False
    is_recommended: bool = False
    is_optional: bool = False
    order: int = 0
    category: str = ""
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class AnalysisWorkflow:
    """분석 워크플로우"""
    purpose: PurposeType
    objective: ObjectiveType
    steps: List[AnalysisStep]
    custom_steps: List[AnalysisStep] = None
    
    def __post_init__(self):
        if self.custom_steps is None:
            self.custom_steps = []

class AnalysisSystem:
    """분석 시스템 핵심 클래스"""
    
    def __init__(self):
        self.purpose_objective_mapping = self._load_purpose_objective_mapping()
        self.required_steps = self._load_required_steps()
        self.recommended_steps = self._load_recommended_steps()
        self.optional_steps = self._load_optional_steps()
        
    def _load_purpose_objective_mapping(self) -> Dict[PurposeType, List[ObjectiveType]]:
        """용도별 목적 매핑 로드"""
        return {
            PurposeType.OFFICE: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY
            ],
            PurposeType.RESIDENTIAL: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.COST_ANALYSIS
            ],
            PurposeType.COMMERCIAL: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.BRANDING,
                ObjectiveType.OPERATION_STRATEGY
            ],
            PurposeType.CULTURAL: [
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.BRANDING,
                ObjectiveType.SPACE_PLANNING
            ],
            PurposeType.EDUCATIONAL: [
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY
            ],
            PurposeType.MEDICAL: [
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.LEGAL_REVIEW,
                ObjectiveType.COST_ANALYSIS
            ],
            PurposeType.INDUSTRIAL: [
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.LEGAL_REVIEW,
                ObjectiveType.COST_ANALYSIS
            ],
            PurposeType.MIXED_USE: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY
            ]
        }
    
    def _load_required_steps(self) -> List[AnalysisStep]:
        """필수 단계 로드"""
        return [
            AnalysisStep(
                id="requirement_analysis",
                title="건축주 요구사항 분석",
                description="건축주의 명시적/암묵적 요구사항을 모두 파악하여 프로젝트의 근본적인 목표와 방향성 설정",
                is_required=True,
                order=1,
                category="기초"
            ),
            AnalysisStep(
                id="site_regulation_analysis", 
                title="대지 환경 및 법규 분석",
                description="대상 대지의 잠재력과 제약사항을 다각적으로 분석해 후속 설계 전략의 현실적 기반을 마련",
                is_required=True,
                order=2,
                category="기초"
            ),
            AnalysisStep(
                id="task_comprehension",
                title="과업 이해도 및 설계 주안점", 
                description="InnoScan 결과와 과업지시서를 종합 분석해 설계 전제조건, KPI, 제약조건 등을 정리",
                is_required=True,
                order=3,
                category="기초"
            )
        ]
    
    def _load_recommended_steps(self) -> Dict[ObjectiveType, List[AnalysisStep]]:
        """목적별 권장 단계 로드"""
        return {
            ObjectiveType.MARKET_ANALYSIS: [
                AnalysisStep(
                    id="precedent_benchmarking",
                    title="선진사례 벤치마킹 및 최적 운영전략",
                    description="국내외 유사 프로젝트 사례를 심층 분석해 차별화 요소와 최적 운영 방안을 도출",
                    is_recommended=True,
                    order=4,
                    category="분석"
                )
            ],
            ObjectiveType.DESIGN_GUIDELINE: [
                AnalysisStep(
                    id="design_trend_application",
                    title="통합 디자인 트렌드 적용 전략",
                    description="건축·인테리어·조경 분야의 핵심 트렌드와 실현 가능한 적용 전략을 제시",
                    is_recommended=True,
                    order=4,
                    category="설계"
                ),
                AnalysisStep(
                    id="mass_strategy",
                    title="건축설계 방향 및 매스(Mass) 전략",
                    description="전 단계 분석 결과를 통합해 건축설계의 핵심 컨셉과 최적 매스 전략을 도출",
                    is_recommended=True,
                    order=5,
                    category="설계"
                )
            ],
            ObjectiveType.MASS_STRATEGY: [
                AnalysisStep(
                    id="mass_strategy",
                    title="건축설계 방향 및 매스(Mass) 전략",
                    description="전 단계 분석 결과를 통합해 건축설계의 핵심 컨셉과 최적 매스 전략을 도출",
                    is_recommended=True,
                    order=4,
                    category="설계"
                ),
                AnalysisStep(
                    id="schematic_space_plan",
                    title="평면·단면 스키매틱 및 공간 계획",
                    description="주요 프로그램별 공간·면적 배치, 단면 연계, 실별 수용 인원 등 공간계획을 스키매틱으로 도출",
                    is_recommended=True,
                    order=5,
                    category="설계"
                )
            ],
            ObjectiveType.COST_ANALYSIS: [
                AnalysisStep(
                    id="cost_estimation",
                    title="공사비 예측 및 원가 검토",
                    description="연면적, 용도, 적용 공법 등 입력값을 바탕으로 개략 공사비와 비용구조를 산출",
                    is_recommended=True,
                    order=4,
                    category="경제성"
                ),
                AnalysisStep(
                    id="operation_investment_analysis",
                    title="운영 및 투자 효율성 분석",
                    description="운영비, 관리비, 투자수익률 등 주요 재무지표 기반으로 경제성·운영효율성을 평가",
                    is_recommended=True,
                    order=5,
                    category="경제성"
                )
            ],
            ObjectiveType.OPERATION_STRATEGY: [
                AnalysisStep(
                    id="operation_investment_analysis",
                    title="운영 및 투자 효율성 분석",
                    description="운영비, 관리비, 투자수익률 등 주요 재무지표 기반으로 경제성·운영효율성을 평가",
                    is_recommended=True,
                    order=4,
                    category="운영"
                ),
                AnalysisStep(
                    id="ux_circulation_simulation",
                    title="사용자 동선 분석 및 시나리오별 공간 최적화 전략",
                    description="사용자 유형별 동선/체류 시나리오와 AI 기반 시뮬레이션 결과를 바탕으로 공간·동선 최적화 전략을 제시",
                    is_recommended=True,
                    order=5,
                    category="운영"
                )
            ],
            ObjectiveType.BRANDING: [
                AnalysisStep(
                    id="architectural_branding_identity",
                    title="건축적 차별화·브랜딩·정체성 전략",
                    description="상징성, 로컬리티, 테마, 감성 건축 등 차별화 포인트를 반영한 프로젝트 고유의 브랜딩 및 정체성 전략을 도출",
                    is_recommended=True,
                    order=4,
                    category="브랜딩"
                )
            ],
            ObjectiveType.LEGAL_REVIEW: [
                AnalysisStep(
                    id="legal_review_analysis",
                    title="법적 검토 및 규제 분석",
                    description="관련 법규, 규제, 인허가 요건 등을 종합적으로 검토하여 프로젝트의 법적 실현 가능성을 평가",
                    is_recommended=True,
                    order=4,
                    category="법규"
                )
            ],
            ObjectiveType.SPACE_PLANNING: [
                AnalysisStep(
                    id="area_programming",
                    title="면적 산출 및 공간 배분 전략",
                    description="수요 기반 분석과 시장/법적 기준을 바탕으로 최적의 공간구성과 면적 배분안을 도출",
                    is_recommended=True,
                    order=4,
                    category="공간계획"
                ),
                AnalysisStep(
                    id="schematic_space_plan",
                    title="평면·단면 스키매틱 및 공간 계획",
                    description="주요 프로그램별 공간·면적 배치, 단면 연계, 실별 수용 인원 등 공간계획을 스키매틱으로 도출",
                    is_recommended=True,
                    order=5,
                    category="공간계획"
                )
            ]
        }
    
    def _load_optional_steps(self) -> List[AnalysisStep]:
        """번외 단계 로드"""
        return [
            AnalysisStep(
                id="concept_development",
                title="설계 컨셉 도출 및 평가",
                description="키워드/요구/KPI를 조합해 설계 컨셉을 도출하고 평가 기준까지 체계화",
                is_optional=True,
                order=6,
                category="설계"
            ),
            AnalysisStep(
                id="flexible_space_strategy",
                title="가변형 공간·프로그램 유연성 및 확장성 설계 전략",
                description="프로그램 변화·미래 수요 대응을 위한 가변형 공간, 다목적 영역, Flexible Mass/Plan 설계 방안을 제시",
                is_optional=True,
                order=7,
                category="설계"
            ),
            AnalysisStep(
                id="design_requirement_summary",
                title="최종 설계 요구사항 및 가이드라인",
                description="분석 결과를 바탕으로 실제 설계에 적용 가능한 요구사항과 가이드라인을 구조화",
                is_optional=True,
                order=8,
                category="종합"
            )
        ]
    
    def get_available_objectives(self, purpose: PurposeType) -> List[ObjectiveType]:
        """용도에 따른 사용 가능한 목적 목록 반환"""
        return self.purpose_objective_mapping.get(purpose, [])
    
    def suggest_analysis_steps(self, purpose: PurposeType, objectives: List[ObjectiveType]) -> AnalysisWorkflow:
        """용도와 목적에 따른 분석 단계 자동 제안"""
        # 필수 단계 포함
        steps = self.required_steps.copy()
        
        # 목적별 권장 단계 추가
        for objective in objectives:
            if objective in self.recommended_steps:
                steps.extend(self.recommended_steps[objective])
        
        # 중복 제거 및 순서 정렬
        unique_steps = []
        seen_ids = set()
        for step in steps:
            if step.id not in seen_ids:
                unique_steps.append(step)
                seen_ids.add(step.id)
        
        # 순서별 정렬
        unique_steps.sort(key=lambda x: x.order)
        
        return AnalysisWorkflow(
            purpose=purpose,
            objective=objectives[0] if objectives else ObjectiveType.OTHER,
            steps=unique_steps
        )
    
    def add_optional_step(self, workflow: AnalysisWorkflow, step_id: str) -> AnalysisWorkflow:
        """번외 단계 추가"""
        optional_step = next((step for step in self.optional_steps if step.id == step_id), None)
        if optional_step:
            workflow.custom_steps.append(optional_step)
        return workflow
    
    def remove_step(self, workflow: AnalysisWorkflow, step_id: str) -> AnalysisWorkflow:
        """단계 제거 (필수 단계는 제거 불가)"""
        workflow.steps = [step for step in workflow.steps if not (step.id == step_id and not step.is_required)]
        workflow.custom_steps = [step for step in workflow.custom_steps if step.id != step_id]
        return workflow
    
    def reorder_steps(self, workflow: AnalysisWorkflow, new_order: List[str]) -> AnalysisWorkflow:
        """단계 순서 변경"""
        # 모든 단계를 하나의 리스트로 합치기
        all_steps = workflow.steps + workflow.custom_steps
        
        # 새로운 순서에 따라 재정렬
        ordered_steps = []
        for step_id in new_order:
            step = next((s for s in all_steps if s.id == step_id), None)
            if step:
                ordered_steps.append(step)
        
        # 필수 단계와 나머지 단계 분리
        required_steps = [step for step in ordered_steps if step.is_required]
        other_steps = [step for step in ordered_steps if not step.is_required]
        
        workflow.steps = required_steps
        workflow.custom_steps = other_steps
        
        return workflow
    
    def get_final_workflow(self, workflow: AnalysisWorkflow) -> List[AnalysisStep]:
        """최종 워크플로우 반환 (모든 단계 포함)"""
        all_steps = workflow.steps + workflow.custom_steps
        all_steps.sort(key=lambda x: x.order)
        return all_steps
    
    def export_workflow_config(self, workflow: AnalysisWorkflow) -> Dict:
        """워크플로우 설정 내보내기"""
        return {
            "purpose": workflow.purpose.value,
            "objective": workflow.objective.value,
            "steps": [
                {
                    "id": step.id,
                    "title": step.title,
                    "description": step.description,
                    "is_required": step.is_required,
                    "is_recommended": step.is_recommended,
                    "is_optional": step.is_optional,
                    "order": step.order,
                    "category": step.category
                }
                for step in self.get_final_workflow(workflow)
            ]
        }
    
    def import_workflow_config(self, config: Dict) -> AnalysisWorkflow:
        """워크플로우 설정 가져오기"""
        purpose = PurposeType(config["purpose"])
        objective = ObjectiveType(config["objective"])
        
        steps = []
        for step_config in config["steps"]:
            step = AnalysisStep(
                id=step_config["id"],
                title=step_config["title"],
                description=step_config["description"],
                is_required=step_config["is_required"],
                is_recommended=step_config["is_recommended"],
                is_optional=step_config["is_optional"],
                order=step_config["order"],
                category=step_config["category"]
            )
            steps.append(step)
        
        return AnalysisWorkflow(
            purpose=purpose,
            objective=objective,
            steps=steps
        )

# 사용 예시
if __name__ == "__main__":
    system = AnalysisSystem()
    
    # 용도와 목적 선택
    purpose = PurposeType.OFFICE
    objectives = [ObjectiveType.MARKET_ANALYSIS, ObjectiveType.DESIGN_GUIDELINE]
    
    # 분석 단계 자동 제안
    workflow = system.suggest_analysis_steps(purpose, objectives)
    
    print(f"용도: {purpose.value}")
    print(f"목적: {[obj.value for obj in objectives]}")
    print("\n제안된 분석 단계:")
    for step in workflow.steps:
        print(f"- {step.title} ({step.category})")
    
    # 번외 단계 추가
    workflow = system.add_optional_step(workflow, "concept_development")
    
    print("\n번외 단계 추가 후:")
    for step in system.get_final_workflow(workflow):
        print(f"- {step.title} ({step.category})") 