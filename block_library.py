class AnalysisBlock:
    def __init__(self, name, description, analysis_items, output_format, caution):
        self.name = name
        self.description = description
        self.analysis_items = analysis_items
        self.output_format = output_format
        self.caution = caution

daji_block = AnalysisBlock(
    name="대지 분석",
    description="대지의 기본 정보 및 맥락을 분석합니다.",
    analysis_items=[
        "기본정보 요약", "입지 및 도시 맥락", "대지 조건",
        "법적 요건", "환경 및 경관", "교통 및 접근성", "전략적 시사점"
    ],
    output_format="표 + 장문 서술",
    caution="AI 추론 명시 / 설계 제안 금지 / 분석 항목 고정"
)