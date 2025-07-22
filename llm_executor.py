import dspy
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

dspy.settings.configure(openai_model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))

def run_daji_analysis(text):
    from prompt_generator import DajiAnalysis
    daji_module = DajiAnalysis()
    result = daji_module.forward(text)
    return result