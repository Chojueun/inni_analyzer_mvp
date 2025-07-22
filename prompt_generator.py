import dspy

class DajiAnalysis(dspy.Module):
    def __init__(self):
        super().__init__()
        self.predict = dspy.Predict("대지 관련 정보를 입력받아 분석 보고서를 작성하세요.")

    def forward(self, input_text):
        return self.predict(input_text)