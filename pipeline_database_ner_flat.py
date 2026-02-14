import os
import sys
sys.path.insert(0, 'ner')

from ner_database_direct 
import parse_sql_file, build_flat_ner_output
import json

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 70)
print("DATABASE NER EXTRACTION PIPELINE (FLAT FORMAT)")
print("=" * 70)
print(f"\n📄 Processing: enterprise_intelligence.sql\n")

# Parse the SQL file
data = parse_sql_file("enterprise_intelligence.sql")

print(f"✓ Parsed database tables:")
print(f"  • Customers: {len(data['customers'])} records")
print(f"  • Orders: {len(data['orders'])} records")
print(f"  • Delivery Agents: {len(data['delivery_agents'])} records")
print(f"  • Reviews: {len(data['customer_reviews'])} records")
print(f"  • Incidents: {len(data['incidents'])} records")

# Build flat NER output
records = build_flat_ner_output(data)

# Save to file
output_file = os.path.join(OUTPUT_DIR, "database_ner_flat.json")
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(records, f, indent=2, ensure_ascii=False)

print(f"\n✓ NER Transformation Complete!")
print(f"✓ Output saved to: {output_file}")
print(f"✓ Total records extracted: {len(records)}")

# Display sample
print(f"\n📋 Sample Records:")
print("-" * 70)
for i, record in enumerate(records[:3], 1):
    print(f"\n{i}. Customer {record['customer_id']} | Order {record['order_id']}")
    print(f"   Issue: {record['issue_type']}")
    print(f"   Sentiment: {record['sentiment']}")
    print(f"   Description: {record['issue_description'][:50]}...")

print("\n" + "=" * 70)
