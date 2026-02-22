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
department, cause, date, time_window.

IMPORTANT date rules:
- Look for the "Date:" header in the email to determine when it was sent.
- Resolve ALL relative date references ("today", "yesterday", "this week",
  "last week", "earlier today", "last month", etc.) relative to the email's
  Date header, NOT relative to the current date.
  For example, if the email Date is 2026-01-28 and the email says "today",
  then date = "2026-01-28". If it says "yesterday", date = "2026-01-27".
- Return "date" as an ISO date string (YYYY-MM-DD).
- If no date can be determined, set date to the email's Date header value.
- "time_window" should describe the time-of-day or duration (e.g. "8:15 PM",
  "peak hours 7-9 PM", "25 minutes"), NOT relative day references.

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
