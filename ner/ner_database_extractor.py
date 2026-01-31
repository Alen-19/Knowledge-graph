import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DATABASE_SYSTEM_PROMPT = """
You are an enterprise database NER system.
Extract entities from database tables and records:

For CUSTOMERS table extract:
- customer_id, name, email, location

For ORDERS table extract:
- order_id, customer_id, agent_id, order_status, order_time, delivery_time, delivery_status

For DELIVERY_AGENTS table extract:
- agent_id, agent_name, vehicle_type, base_location

For CUSTOMER_REVIEWS table extract:
- review_id, order_id, review_text, sentiment, review_rating

For INCIDENTS table extract:
- incident_id, customer_id, order_id, issue_type, issue_severity, reported_at

Additional extractions:
- entity_type (PERSON, LOCATION, ORGANIZATION, DATE, STATUS, CONTACT)
- relationships (which customer has which order, which agent delivered which order)
- business_metrics (delivery_performance, customer_sentiment, incident_count)

Return ONLY valid JSON with the structure:
{
    "table_name": "...",
    "records": [
        {
            "entity_type": "...",
            "entities": {...},
            "relationships": {...},
            "metrics": {...}
        }
    ],
    "summary": {
        "total_records": number,
        "entity_count": number,
        "key_findings": [...]
    }
}
"""

def extract_database_entities(database_content):
    """Extract NER entities from database SQL content"""
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": DATABASE_SYSTEM_PROMPT},
            {"role": "user", "content": database_content}
        ],
        temperature=0
    )
    return response.choices[0].message.content


def extract_from_file(file_path):
    """Read database file and extract entities"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return extract_database_entities(content)
