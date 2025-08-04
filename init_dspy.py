# init_dspy.py
import dspy
import os
from dotenv import load_dotenv

load_dotenv()
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")

if not getattr(dspy.settings, "lm", None):
    lm = dspy.LM(
        "claude-sonnet-4-20250514",
        provider="anthropic",
        api_key=anthropic_api_key,
        max_tokens=2000
    )
    dspy.configure(lm=lm, track_usage=True)
