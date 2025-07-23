import dspy

class PDFSummarizer(dspy.Signature):
    def __init__(self):
        super().__init__()
        self.input_variables = ['text']
        self.output_variables = ['summary']

summarizer = dspy.Predict(PDFSummarizer)

def summarize_pdf(text):
    result = summarizer(text=text)
    return result.summary
