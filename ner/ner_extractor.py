import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are an enterprise NER system.
Extract:
customer_id, order_id, agent_id, issue_type,
issue_description, severity, sentiment,
department, cause, time_window.
Return ONLY valid JSON.
"""

def extract_entities(email_text):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": email_text}
        ],
        temperature=0
    )
    return response.choices[0].message.content
