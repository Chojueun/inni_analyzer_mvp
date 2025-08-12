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

from typing import Dict, List
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
    SPORTS = "체육/스포츠"
    CONTRACT_BIDDING = "계약·입찰"
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
    CONCEPT_RESEARCH = "컨셉리서치"
    RISK_ANALYSIS = "리스크분석"
    DOCUMENT_ANALYSIS = "과업지시서 및 문서 분석"
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

    # ─── 실행과 관련된 핵심 로직 (과거 코드 통합) ─────────────────────────────
    
    def get_available_objectives(self, purpose: PurposeType) -> List[ObjectiveType]:
        """용도에 따른 사용 가능한 목적 반환"""
        return self.purpose_objective_mapping.get(purpose, [ObjectiveType.OTHER])
    
    def suggest_analysis_steps(self, purpose: PurposeType, objectives: List[ObjectiveType]) -> AnalysisWorkflow:
        """분석 단계 자동 제안 (과거 코드 방식)"""
        steps = self.required_steps.copy()
        
        for objective in objectives:
            if objective in self.recommended_steps:
                steps.extend(self.recommended_steps[objective])
        
        # 중복 제거
        unique_steps = []
        seen_ids = set()
        for step in steps:
            if step.id not in seen_ids:
                unique_steps.append(step)
                seen_ids.add(step.id)
        
        # 순서 정렬
        unique_steps.sort(key=lambda x: x.order)
        
        return AnalysisWorkflow(
            purpose=purpose,
            objective=objectives[0] if objectives else ObjectiveType.OTHER,
            steps=unique_steps
        )

    def add_optional_step(self, workflow: AnalysisWorkflow, step_id: str) -> AnalysisWorkflow:
        """번외 단계 추가 (과거 코드 방식)"""
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
        """순서 변경 (과거 코드 방식)"""
        all_steps = workflow.steps + workflow.custom_steps
        
        ordered_steps = []
        for step_id in new_order:
            step = next((s for s in all_steps if s.id == step_id), None)
            if step:
                ordered_steps.append(step)
        
        required_steps = [step for step in ordered_steps if step.is_required]
        other_steps = [step for step in ordered_steps if not step.is_required]
        
        workflow.steps = required_steps
        workflow.custom_steps = other_steps
        
        return workflow

    def get_final_workflow(self, workflow: AnalysisWorkflow) -> List[AnalysisStep]:
        """최종 실행 단계 목록 (과거 코드 방식)"""
        all_steps = workflow.steps + workflow.custom_steps
        all_steps.sort(key=lambda x: x.order)
        return all_steps

    # ─── 실행 상태 관리 (새로 추가) ─────────────────────────────
    
    def get_current_step(self, workflow: AnalysisWorkflow, current_index: int) -> AnalysisStep:
        """현재 실행할 단계 반환"""
        all_steps = self.get_final_workflow(workflow)
        if 0 <= current_index < len(all_steps):
            return all_steps[current_index]
        return None

    def get_step_progress(self, workflow: AnalysisWorkflow, completed_steps: List[str]) -> Dict:
        """단계별 진행 상황 반환"""
        all_steps = self.get_final_workflow(workflow)
        progress = {
            "total": len(all_steps),
            "completed": len(completed_steps),
            "current_index": len(completed_steps),
            "progress_percentage": (len(completed_steps) / len(all_steps)) * 100 if all_steps else 0,
            "steps_status": []
        }
        
        for i, step in enumerate(all_steps):
            status = "completed" if step.title in completed_steps else "pending"
            if i == len(completed_steps):
                status = "current"
            
            progress["steps_status"].append({
                "index": i,
                "step": step,
                "status": status
            })
        
        return progress

    def can_execute_step(self, workflow: AnalysisWorkflow, step_id: str, completed_steps: List[str]) -> bool:
        """단계 실행 가능 여부 확인"""
        step = next((s for s in self.get_final_workflow(workflow) if s.id == step_id), None)
        if not step:
            return False
        
        # 의존성 확인
        for dependency in step.dependencies:
            if dependency not in completed_steps:
                return False
        
        return True

    def get_next_executable_step(self, workflow: AnalysisWorkflow, completed_steps: List[str]) -> AnalysisStep:
        """다음 실행 가능한 단계 반환"""
        all_steps = self.get_final_workflow(workflow)
        
        for step in all_steps:
            if step.title not in completed_steps and self.can_execute_step(workflow, step.id, completed_steps):
                return step
        
        return None

    # ─── 기존 메서드들 (유지) ─────────────────────────────
    
    def _load_purpose_objective_mapping(self) -> Dict[PurposeType, List[ObjectiveType]]:
        """용도별 목적 매핑 로드"""
        return {
            PurposeType.OFFICE: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.CONCEPT_RESEARCH,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.RESIDENTIAL: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.CONCEPT_RESEARCH,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.COMMERCIAL: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.BRANDING,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.CONCEPT_RESEARCH,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.CULTURAL: [
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.BRANDING,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.CONCEPT_RESEARCH,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.EDUCATIONAL: [
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.LEGAL_REVIEW,
                ObjectiveType.CONCEPT_RESEARCH,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.MEDICAL: [
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.LEGAL_REVIEW,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.CONCEPT_RESEARCH,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.INDUSTRIAL: [
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.LEGAL_REVIEW,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.CONCEPT_RESEARCH,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.MIXED_USE: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.SPORTS: [
                ObjectiveType.MARKET_ANALYSIS,
                ObjectiveType.DESIGN_GUIDELINE,
                ObjectiveType.MASS_STRATEGY,
                ObjectiveType.SPACE_PLANNING,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.CONCEPT_RESEARCH,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.DOCUMENT_ANALYSIS
            ],
            PurposeType.CONTRACT_BIDDING: [
                ObjectiveType.LEGAL_REVIEW,
                ObjectiveType.RISK_ANALYSIS,
                ObjectiveType.COST_ANALYSIS,
                ObjectiveType.OPERATION_STRATEGY,
                ObjectiveType.DOCUMENT_ANALYSIS
            ]
        }

    def _load_required_steps(self) -> List[AnalysisStep]:
        """필수 단계 로드"""
        return [
            AnalysisStep(
                id="doc_collector",
                title="문서 구조 및 요구사항 매트릭스화",
                description="입찰/계약 문서 전체 구조와 핵심정보, 시설별 상세 요구사항, 주요 섹션별 목적을 표로 정리",
                is_required=True,
                order=1,
                category="문서분석"
            ),
            AnalysisStep(
                id="context_analyzer",
                title="프로젝트 컨텍스트 및 배경 분석",
                description="프로젝트의 배경, 목적, 제약사항, 이해관계자, 지역적 특성 등을 종합 분석",
                is_required=True,
                order=2,
                category="컨텍스트분석"
            )
        ]

    def _load_recommended_steps(self) -> Dict[ObjectiveType, List[AnalysisStep]]:
        """권장 단계 로드"""
        return {
            ObjectiveType.MARKET_ANALYSIS: [
                AnalysisStep(
                    id="market_analyzer",
                    title="시장 분석 및 경쟁사 조사",
                    description="시장 현황, 경쟁사 분석, 시장 트렌드, 수요 예측 등을 종합 분석",
                    is_recommended=True,
                    order=3,
                    category="시장분석"
                )
            ],
            ObjectiveType.DESIGN_GUIDELINE: [
                AnalysisStep(
                    id="design_guideline",
                    title="디자인 가이드라인 및 기준 분석",
                    description="디자인 원칙, 건축 기준, 규제 요구사항, 디자인 트렌드를 분석",
                    is_recommended=True,
                    order=4,
                    category="디자인분석"
                )
            ],
            ObjectiveType.MASS_STRATEGY: [
                AnalysisStep(
                    id="mass_strategy",
                    title="Mass 전략 및 공간 구성 분석",
                    description="건물 형태, 공간 구성, 동선 계획, 기능 배치 전략을 분석",
                    is_recommended=True,
                    order=5,
                    category="공간분석"
                )
            ],
            ObjectiveType.COST_ANALYSIS: [
                AnalysisStep(
                    id="cost_analyzer",
                    title="원가 분석 및 경제성 검토",
                    description="건설 원가, 운영 비용, 수익성 분석, 투자 대비 효과를 분석",
                    is_recommended=True,
                    order=6,
                    category="경제분석"
                )
            ],
            ObjectiveType.OPERATION_STRATEGY: [
                AnalysisStep(
                    id="operation_strategy",
                    title="운영 전략 및 관리 방안",
                    description="시설 운영 방안, 관리 체계, 서비스 전략, 효율성 개선 방안을 분석",
                    is_recommended=True,
                    order=7,
                    category="운영분석"
                )
            ],
            ObjectiveType.BRANDING: [
                AnalysisStep(
                    id="branding_strategy",
                    title="브랜딩 전략 및 아이덴티티",
                    description="브랜드 아이덴티티, 마케팅 전략, 사용자 경험, 차별화 요소를 분석",
                    is_recommended=True,
                    order=8,
                    category="브랜딩분석"
                )
            ],
            ObjectiveType.LEGAL_REVIEW: [
                AnalysisStep(
                    id="legal_reviewer",
                    title="법적 검토 및 규제 분석",
                    description="관련 법규, 규제 요구사항, 계약 조건, 법적 리스크를 분석",
                    is_recommended=True,
                    order=9,
                    category="법적분석"
                )
            ],
            ObjectiveType.SPACE_PLANNING: [
                AnalysisStep(
                    id="space_planner",
                    title="공간 계획 및 기능 배치",
                    description="공간 구성, 기능별 배치, 동선 계획, 확장성 고려사항을 분석",
                    is_recommended=True,
                    order=10,
                    category="공간계획"
                )
            ],
            ObjectiveType.CONCEPT_RESEARCH: [
                AnalysisStep(
                    id="concept_researcher",
                    title="컨셉 리서치 및 참고 사례",
                    description="유사 프로젝트 사례, 컨셉 트렌드, 참고 자료, 벤치마킹 요소를 분석",
                    is_recommended=True,
                    order=11,
                    category="컨셉분석"
                )
            ],
            ObjectiveType.RISK_ANALYSIS: [
                AnalysisStep(
                    id="risk_analyzer",
                    title="리스크 분석 및 대응 방안",
                    description="프로젝트 리스크, 위험 요소, 대응 전략, 예방 조치를 분석",
                    is_recommended=True,
                    order=12,
                    category="리스크분석"
                )
            ],
            ObjectiveType.DOCUMENT_ANALYSIS: [
                AnalysisStep(
                    id="document_analyzer",
                    title="과업지시서 및 문서 분석",
                    description="과업지시서, 계약서, 기술사양서, 관련 문서의 상세 분석",
                    is_recommended=True,
                    order=13,
                    category="문서분석"
                )
            ]
        }

    def _load_optional_steps(self) -> List[AnalysisStep]:
        """옵션 단계 로드"""
        return [
            AnalysisStep(
                id="concept_development",
                title="컨셉 개발 및 아이디어 구체화",
                description="프로젝트 컨셉 개발, 아이디어 구체화, 창의적 솔루션 제안",
                is_optional=True,
                order=14,
                category="컨셉개발"
            ),
            AnalysisStep(
                id="sustainability_analysis",
                title="지속가능성 및 친환경 분석",
                description="친환경 요소, 에너지 효율성, 지속가능성 전략 분석",
                is_optional=True,
                order=15,
                category="지속가능성"
            ),
            AnalysisStep(
                id="technology_integration",
                title="기술 통합 및 스마트 솔루션",
                description="스마트 기술, IoT, 자동화, 디지털 솔루션 통합 방안",
                is_optional=True,
                order=16,
                category="기술통합"
            )
        ]

    # ─── 유틸리티 메서드들 ─────────────────────────────
    
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