import json
import os
import subprocess
import sys
from typing import List, Dict, Any

# Uninstall deprecated pinecone plugins before importing pinecone (fixes DeprecatedPluginError)
for _pkg in ["pinecone-plugin-inference", "pinecone-plugin-assistant"]:
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", _pkg],
                   capture_output=True)

from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import config

class PineconeHandler:
    """Handle Pinecone vector database operations"""
    
    def __init__(self):
        """Initialize Pinecone client and create/connect to index"""
        self.pc = Pinecone(api_key=config.PINECONE_API_KEY)
        print(f"📦 Loading HuggingFace model: {config.HUGGINGFACE_MODEL}")
        self.embedding_model = SentenceTransformer(config.HUGGINGFACE_MODEL)
        self.index_name = config.PINECONE_INDEX_NAME
        self.dimension = config.PINECONE_DIMENSION
        self.index = None
        self._initialize_index()
    
    def _initialize_index(self):
        """Initialize or connect to Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                print(f"📍 Creating Pinecone index: {self.index_name} (dim={self.dimension})")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
            else:
                # Verify dimension matches HuggingFace (384) — if old index used OpenAI (1536), recreate
                idx_info = self.pc.describe_index(self.index_name)
                existing_dim = idx_info.dimension
                if existing_dim != self.dimension:
                    print(f"⚠️  Index dimension mismatch: existing={existing_dim}, expected={self.dimension}")
                    print(f"🔄 Deleting old index and recreating with correct dimension...")
                    self.pc.delete_index(self.index_name)
                    import time; time.sleep(5)
                    self.pc.create_index(
                        name=self.index_name,
                        dimension=self.dimension,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud="aws",
                            region="us-east-1"
                        )
                    )
                    print(f"✅ Recreated index with dimension {self.dimension}")
                else:
                    print(f"✅ Connected to existing index: {self.index_name}")
            
            self.index = self.pc.Index(self.index_name)
            print(f"✅ Pinecone index ready. Stats: {self.index.describe_index_stats()}")
        
        except Exception as e:
            print(f"❌ Error initializing Pinecone: {e}")
            raise
    
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using HuggingFace sentence-transformers (FREE)"""
        try:
            embedding = self.embedding_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return None
    
    def store_entity(self, entity_id: str, entity_data: Dict[str, Any], entity_type: str):
        """Store entity embedding in Pinecone"""
        try:
            # Create searchable text from entity data
            text_content = f"""
            Type: {entity_type}
            ID: {entity_data.get('id', 'N/A')}
            Value: {entity_data.get('value', 'N/A')}
            Description: {entity_data.get('description', '')}
            Metadata: {json.dumps(entity_data)}
            """
            
            embedding = self.get_embedding(text_content)
            if not embedding:
                return False
            
            # Store in Pinecone with metadata
            metadata = {
                "entity_type": entity_type,
                "source": entity_data.get('source', 'unknown'),
                "timestamp": entity_data.get('timestamp', 'N/A'),
                **{k: str(v) for k, v in entity_data.items() if k not in ['embedding']}
            }
            
            self.index.upsert(vectors=[
                (entity_id, embedding, metadata)
            ])
            
            print(f"✅ Stored {entity_type}: {entity_id}")
            return True
        
        except Exception as e:
            print(f"❌ Error storing entity: {e}")
            return False
    
    def store_document(self, doc_id: str, doc_text: str, doc_metadata: Dict[str, Any]):
        """Store document embedding in Pinecone"""
        try:
            embedding = self.get_embedding(doc_text[:2000])  # Limit text length
            if not embedding:
                return False
            
            metadata = {
                "doc_type": "document",
                **{k: str(v) for k, v in doc_metadata.items()}
            }
            
            self.index.upsert(vectors=[
                (doc_id, embedding, metadata)
            ])
            
            print(f"✅ Stored document: {doc_id}")
            return True
        
        except Exception as e:
            print(f"❌ Error storing document: {e}")
            return False
    
    def semantic_search(self, query: str, top_k: int = 5, filters: Dict = None) -> List[Dict]:
        """Perform semantic search on stored embeddings"""
        try:
            query_embedding = self.get_embedding(query)
            if not query_embedding:
                return []
            
            # Search with optional filters
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter=filters
            )
            
            search_results = []
            for match in results.matches:
                search_results.append({
                    "id": match.id,
                    "score": float(match.score),
                    "metadata": match.metadata
                })
            
            return search_results
        
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return []
    
    def semantic_search_by_type(self, query: str, entity_type: str, top_k: int = 5) -> List[Dict]:
        """Search within specific entity type"""
        filters = {
            "entity_type": {"$eq": entity_type}
        }
        return self.semantic_search(query, top_k, filters)
    
    def batch_store_entities(self, entities: List[Dict], entity_type: str):
        """Store multiple entities at once"""
        success_count = 0
        for i, entity in enumerate(entities):
            entity_id = f"{entity_type}_{entity.get('id', i)}"
            if self.store_entity(entity_id, entity, entity_type):
                success_count += 1
        
        print(f"✅ Batch stored {success_count}/{len(entities)} {entity_type}s")
        return success_count
    
    def load_and_store_ner_outputs(self):
        """Load NER JSON outputs and store in Pinecone"""
        try:
            outputs_dir = config.OUTPUT_DIR
            
            # Load email JSON files
            email_count = 0
            for file in os.listdir(outputs_dir):
                if file.startswith("email_") and file.endswith(".json"):
                    try:
                        with open(os.path.join(outputs_dir, file), 'r') as f:
                            email_data = json.load(f)
                        
                        doc_id = f"email_{file.split('_')[1].split('.')[0]}"
                        description = email_data.get('issue_description', '')
                        
                        metadata = {
                            "source": "email",
                            "customer_id": email_data.get('customer_id', ''),
                            "order_id": email_data.get('order_id', ''),
                            "agent_id": str(email_data.get('agent_id', '') or ''),
                            "issue_type": email_data.get('issue_type', ''),
                            "issue_description": email_data.get('issue_description', ''),
                            "sentiment": email_data.get('sentiment', ''),
                            "severity": str(email_data.get('severity', '') or ''),
                            "department": email_data.get('department', ''),
                            "cause": email_data.get('cause', ''),
                            "time_window": str(email_data.get('time_window', '') or '')
                        }
                        
                        self.store_document(doc_id, description, metadata)
                        email_count += 1
                    except Exception as e:
                        print(f"⚠️  Error processing {file}: {e}")
            
            # Load database NER flat file
            db_ner_file = os.path.join(outputs_dir, "database_ner_flat.json")
            if os.path.exists(db_ner_file):
                with open(db_ner_file, 'r') as f:
                    db_data = json.load(f)
                
                if isinstance(db_data, list):
                    for record in db_data[:100]:  # Limit to first 100
                        entity_id = f"db_entity_{record.get('entity_id', '')}"
                        self.store_entity(entity_id, record, record.get('entity_type', 'Unknown'))
            
            print(f"\n✅ Successfully loaded and stored NER outputs in Pinecone!")
            print(f"   - Email documents: {email_count}")
        
        except Exception as e:
            print(f"❌ Error loading NER outputs: {e}")
    
    def get_index_stats(self) -> Dict:
        """Get index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "namespaces": stats.namespaces,
                "dimension": self.dimension
            }
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}


# Test function
if __name__ == "__main__":
    config.validate_config()
    
    handler = PineconeHandler()
    print("\n📊 Pinecone Handler initialized successfully!")
    
    # Uncomment to load NER outputs
    # handler.load_and_store_ner_outputs()
