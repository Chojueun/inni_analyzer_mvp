#summary_generator.py

import dspy
from dspy import Signature, InputField, OutputField

# DSPy 설정은 agent_executor.py에서 처리하므로 여기서는 제거
# try:
#     import openai
#     dspy.settings.configure(lm=openai.OpenAI())
# except:
#     pass

class SiteAnalysisFields(Signature):
    text: str = InputField(desc="PDF에서 추출한 전체 텍스트")
    site_area: str = OutputField(desc="대지면적")
    site_address: str = OutputField(desc="대지 주소")
    site_slope: str = OutputField(desc="대지 경사, 고도, 방위")
    zoning: str = OutputField(desc="용도지역, 지구단위계획 등")
    restrictions: str = OutputField(desc="고도제한, 일조권, 환경, 소음, 특이 규제")
    traffic: str = OutputField(desc="주변 도로, 교통, 진출입")
    precedent_comparison: str = OutputField(desc="유사 연수원·교육시설과 비교 포인트")
    risk_factors: str = OutputField(desc="대지·법규 관련 주요 리스크")

class PDFSummary(Signature):
    text: str = InputField(desc="PDF에서 추출한 전체 텍스트")
    summary: str = OutputField(desc="PDF 내용의 핵심 요약")

site_parser = dspy.Predict(SiteAnalysisFields)
summary_predictor = dspy.Predict(PDFSummary)

def summarize_pdf(pdf_text: str) -> str:
    """PDF 텍스트를 요약하는 함수"""
    try:
        result = summary_predictor(text=pdf_text)
        return getattr(result, "summary", "요약을 생성할 수 없습니다.")
    except Exception as e:
        return f"요약 생성 중 오류 발생: {str(e)}"

def extract_site_analysis_fields(pdf_text: str) -> dict:
    """PDF에서 대지 및 법규 관련 필드를 추출하는 함수"""
    try:
        result = site_parser(text=pdf_text)
        return {
            "site_area": getattr(result, "site_area", "대지면적 정보 없음"),
            "site_address": getattr(result, "site_address", "대지 주소 정보 없음"),
            "site_slope": getattr(result, "site_slope", "대지 경사 정보 없음"),
            "zoning": getattr(result, "zoning", "용도지역 정보 없음"),
            "restrictions": getattr(result, "restrictions", "건축 규제 정보 없음"),
            "traffic": getattr(result, "traffic", "교통 정보 없음"),
            "precedent_comparison": getattr(result, "precedent_comparison", "유사 사례 비교 정보 없음"),
            "risk_factors": getattr(result, "risk_factors", "리스크 요인 정보 없음")
        }
    except Exception as e:
        # 오류 발생 시 기본값 반환
        return {
            "site_area": f"추출 오류: {str(e)}",
            "site_address": "대지 주소 정보 없음",
            "site_slope": "대지 경사 정보 없음",
            "zoning": "용도지역 정보 없음",
            "restrictions": "건축 규제 정보 없음",
            "traffic": "교통 정보 없음",
            "precedent_comparison": "유사 사례 비교 정보 없음",
            "risk_factors": "리스크 요인 정보 없음"
        }
