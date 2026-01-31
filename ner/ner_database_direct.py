import os
import json
import sqlite3
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def parse_sql_file(sql_file):
    """Parse SQL file to extract data in structured format"""
    import re
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract INSERT statements and build a structured data dict
    data = {
        'customers': [],
        'orders': [],
        'delivery_agents': [],
        'customer_reviews': [],
        'incidents': []
    }
    
    # Parse customers
    customer_pattern = r"INSERT INTO `customers`[^;]*VALUES\s*(.+?);"
    customer_match = re.search(customer_pattern, content, re.DOTALL)
    if customer_match:
        values_str = customer_match.group(1)
        tuples = re.findall(r"\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", values_str)
        for match in tuples:
            data['customers'].append({
                'customer_id': match[0],
                'name': match[1],
                'email': match[2],
                'location': match[3]
            })
    
    # Parse delivery agents
    agent_pattern = r"INSERT INTO `delivery_agents`[^;]*VALUES\s*(.+?);"
    agent_match = re.search(agent_pattern, content, re.DOTALL)
    if agent_match:
        values_str = agent_match.group(1)
        tuples = re.findall(r"\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", values_str)
        for match in tuples:
            data['delivery_agents'].append({
                'agent_id': match[0],
                'name': match[1],
                'vehicle_type': match[2],
                'base_location': match[3]
            })
    
    # Parse orders (more complex due to NULL values)
    order_pattern = r"INSERT INTO `orders`[^;]*VALUES\s*(.+?);"
    order_match = re.search(order_pattern, content, re.DOTALL)
    if order_match:
        values_str = order_match.group(1)
        tuples = re.findall(r"\('([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*(NULL|'[^']*')\)", values_str)
        for match in tuples:
            delivery_time = None if match[5] == 'NULL' else match[5].strip("'")
            data['orders'].append({
                'order_id': match[0],
                'customer_id': match[1],
                'agent_id': match[2],
                'order_status': match[3],
                'order_time': match[4],
                'delivery_time': delivery_time
            })
    
    # Parse customer reviews
    review_pattern = r"INSERT INTO `customer_reviews`[^;]*VALUES\s*(.+?);"
    review_match = re.search(review_pattern, content, re.DOTALL)
    if review_match:
        values_str = review_match.group(1)
        tuples = re.findall(r"\((\d+),\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", values_str)
        for match in tuples:
            data['customer_reviews'].append({
                'review_id': match[0],
                'order_id': match[1],
                'review_text': match[2],
                'sentiment': match[3]
            })
    
    # Parse incidents
    incident_pattern = r"INSERT INTO `incidents`[^;]*VALUES\s*(.+?);"
    incident_match = re.search(incident_pattern, content, re.DOTALL)
    if incident_match:
        values_str = incident_match.group(1)
        tuples = re.findall(r"\((\d+),\s*'([^']+)',\s*'([^']+)',\s*'([^']+)',\s*'([^']+)'\)", values_str)
        for match in tuples:
            data['incidents'].append({
                'incident_id': match[0],
                'customer_id': match[1],
                'order_id': match[2],
                'issue_type': match[3],
                'reported_at': match[4]
            })
    
    return data

def build_flat_ner_output(data):
    """Build the flat NER output format from parsed database"""
    records = []
    
    # Create a lookup maps
    orders_map = {o['order_id']: o for o in data['orders']}
    reviews_map = {r['order_id']: r for r in data['customer_reviews']}
    
    # Process incidents
    for incident in data['incidents']:
        order_id = incident['order_id']
        order = orders_map.get(order_id, {})
        review = reviews_map.get(order_id, {})
        
        record = {
            "customer_id": incident['customer_id'],
            "order_id": order_id,
            "agent_id": order.get('agent_id'),
            "issue_type": incident.get('issue_type'),
            "issue_description": review.get('review_text', ''),
            "severity": None,
            "sentiment": review.get('sentiment'),
            "department": "Operations",
            "cause": incident.get('issue_type'),
            "time_window": None
        }
        records.append(record)
    
    # Add reviews without incidents
    for order_id, review in reviews_map.items():
        if not any(r['order_id'] == order_id for r in records):
            order = orders_map.get(order_id, {})
            record = {
                "customer_id": order.get('customer_id'),
                "order_id": order_id,
                "agent_id": order.get('agent_id'),
                "issue_type": None,
                "issue_description": review.get('review_text', ''),
                "severity": None,
                "sentiment": review.get('sentiment'),
                "department": "Operations",
                "cause": None,
                "time_window": None
            }
            records.append(record)
    
    return records

if __name__ == "__main__":
    print("Processing database file: enterprise_intelligence.sql...")
    print("=" * 60)
    
    # Parse the SQL file
    data = parse_sql_file("enterprise_intelligence.sql")
    
    # Build flat NER output
    records = build_flat_ner_output(data)
    
    # Save to file
    output_file = os.path.join(OUTPUT_DIR, "database_ner_flat.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Successfully extracted and transformed database NER")
    print(f"✓ Output saved to {output_file}")
    print(f"✓ Total records: {len(records)}")
    print("\nSample records:")
    for i, record in enumerate(records[:3]):
        print(f"  {i+1}. Order {record['order_id']}: {record['sentiment']} - {record['issue_type']}")
