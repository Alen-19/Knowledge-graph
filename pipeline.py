import os
import json
from neo4j import GraphDatabase

# ---------------- CONFIG ----------------
NEO4J_URI = ""
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = ""
OUTPUT_DIR = "outputs"
# ---------------- NEO4J ----------------
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ---------------- PROCESS EMAIL NER RESULTS ----------------
os.makedirs(OUTPUT_DIR, exist_ok=True)

with driver.session() as session:
    # Process email files (email_01.json to email_40.json)
    for i in range(1, 41):
        file = f"email_{i:02d}.json"
        file_path = os.path.join(OUTPUT_DIR, file)
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                ner_data = json.load(f)

            print(f"Processing {file}...")

            # Extract NER results
            customer_id = str(ner_data.get('customer_id')) if ner_data.get('customer_id') else None
            order_id = str(ner_data.get('order_id')) if ner_data.get('order_id') else None
            issue_type = ner_data.get('issue_type')
            agent_id = str(ner_data.get('agent_id')) if ner_data.get('agent_id') else None
            issue_description = ner_data.get('issue_description')

            # ---- Create Customer Node ----
            if customer_id:
                session.run("MERGE (c:Customer {id:$cid})", cid=customer_id)

            # ---- Create Order Node ----
            if order_id:
                session.run("MERGE (o:Order {id:$oid})", oid=order_id)

            # ---- Create Issue Node ----
            if issue_type:
                session.run("MERGE (i:Issue {type:$type, description:$desc})", type=issue_type, desc=issue_description)

            # ---- Create Agent Node (if applicable) ----
            if agent_id:
                session.run("MERGE (a:Agent {id:$aid})", aid=agent_id)

            # ---- Create Relationships ----
            if customer_id and order_id:
                session.run("""
                    MATCH (c:Customer {id:$cid}), (o:Order {id:$oid})
                    MERGE (c)-[:PLACED]->(o)
                """, cid=customer_id, oid=order_id)

            if order_id and issue_type:
                session.run("""
                    MATCH (o:Order {id:$oid}), (i:Issue {type:$type})
                    MERGE (o)-[:HAS_ISSUE]->(i)
                """, oid=order_id, type=issue_type)

            if agent_id and order_id:
                session.run("""
                    MATCH (a:Agent {id:$aid}), (o:Order {id:$oid})
                    MERGE (a)-[:HANDLED]->(o)
                """, aid=agent_id, oid=order_id)

    # Process database NER flat file
    db_ner_file = os.path.join(OUTPUT_DIR, "database_ner_flat.json")
    if os.path.exists(db_ner_file):
        with open(db_ner_file, "r", encoding="utf-8") as f:
            db_ner_data = json.load(f)

        print(f"Processing database_ner_flat.json...")

        # Handle both single record and list of records
        if isinstance(db_ner_data, list):
            records = db_ner_data
        else:
            records = [db_ner_data]

        # Process each database record
        for record in records:
            entity_type = record.get('entity_type')
            entity_value = record.get('entity_value')
            entity_id = record.get('entity_id')

            # ---- Create Entity Node ----
            if entity_type and entity_value:
                session.run(
                    f"MERGE (e:{entity_type} {{value:$val, id:$eid}})",
                    val=entity_value,
                    eid=entity_id
                )

    # ---- PROCESS DOCUMENT NER FILES ----
    print("\n--- Processing Document NER Files ---")
    
    # Get all files in outputs directory
    output_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith("_ner.json")]
    
    for ner_file in output_files:
        file_path = os.path.join(OUTPUT_DIR, ner_file)
        doc_name = ner_file.replace("_ner.json", "")
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Extract JSON from markdown code blocks if present
            if content.strip().startswith("```"):
                # Remove markdown code block markers
                content = content.strip()
                if content.startswith("````json"):
                    content = content[8:]  # Remove ````json
                elif content.startswith("```"):
                    content = content[3:]  # Remove ```
                
                # Remove language identifier if present
                if content.startswith("json\n"):
                    content = content[5:]
                
                # Remove closing ```
                if content.endswith("```"):
                    content = content[:-3]
                
                content = content.strip()
            
            doc_ner_data = json.loads(content)
            
            print(f"Processing {ner_file}...")
            
            # Extract entities from document NER
            order_ids = doc_ner_data.get('ORDER_ID', [])
            customer_ids = doc_ner_data.get('CUSTOMER_ID', [])
            dates = doc_ner_data.get('DATE', [])
            departments = doc_ner_data.get('DEPARTMENT', [])
            issues = doc_ner_data.get('ISSUE', [])
            
            # Create Document node
            session.run(
                "MERGE (d:Document {name:$name})",
                name=doc_name
            )
            
            # Process Customer IDs
            for customer_id in customer_ids:
                if customer_id:
                    session.run("MERGE (c:Customer {id:$cid})", cid=customer_id)
                    # Link document to customer
                    session.run(
                        """
                        MATCH (d:Document {name:$name}), (c:Customer {id:$cid})
                        MERGE (d)-[:MENTIONS_CUSTOMER]->(c)
                        """,
                        name=doc_name, cid=customer_id
                    )
            
            # Process Order IDs
            for order_id in order_ids:
                if order_id:
                    session.run("MERGE (o:Order {id:$oid})", oid=order_id)
                    # Link document to order
                    session.run(
                        """
                        MATCH (d:Document {name:$name}), (o:Order {id:$oid})
                        MERGE (d)-[:MENTIONS_ORDER]->(o)
                        """,
                        name=doc_name, oid=order_id
                    )
            
            # Process Departments
            for dept in departments:
                if dept:
                    session.run("MERGE (dp:Department {name:$dname})", dname=dept)
                    # Link document to department
                    session.run(
                        """
                        MATCH (d:Document {name:$name}), (dp:Department {name:$dname})
                        MERGE (d)-[:MENTIONS_DEPARTMENT]->(dp)
                        """,
                        name=doc_name, dname=dept
                    )
            
            # Process Issues
            for idx, issue in enumerate(issues):
                if issue:
                    issue_id = f"{doc_name}_issue_{idx}"
                    session.run(
                        "MERGE (iss:Issue {id:$iid, description:$desc})",
                        iid=issue_id, desc=issue
                    )
                    # Link document to issue
                    session.run(
                        """
                        MATCH (d:Document {name:$name}), (iss:Issue {id:$iid})
                        MERGE (d)-[:CONTAINS_ISSUE]->(iss)
                        """,
                        name=doc_name, iid=issue_id
                    )
            
            # Link customers to orders mentioned in document
            for customer_id in customer_ids:
                for order_id in order_ids:
                    if customer_id and order_id:
                        session.run(
                            """
                            MATCH (c:Customer {id:$cid}), (o:Order {id:$oid})
                            MERGE (c)-[:PLACED]->(o)
                            """,
                            cid=customer_id, oid=order_id
                        )
        
        except Exception as e:
            print(f"❌ Error processing {ner_file}: {str(e)}")
            continue

driver.close()
print("\n✅ All emails, database NER, and document NER data processed and pushed to Neo4j")
