from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from pinecone import Pinecone
from groq import Groq
import config
import json
import os
import glob
from typing import List, Dict, Any

class LangChainRAGPipeline:
    """RAG (Retrieval Augmented Generation) pipeline using LangChain"""
    
    def __init__(self):
        """Initialize RAG pipeline"""
        self.pinecone_client = Pinecone(api_key=config.PINECONE_API_KEY)
        self.index = self.pinecone_client.Index(config.PINECONE_INDEX_NAME)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.HUGGINGFACE_MODEL
        )
        self.llm = ChatGroq(
            groq_api_key=config.GROQ_API_KEY,
            model_name=config.GROQ_MODEL,
            temperature=0.7
        )
        self.groq_client = Groq(api_key=config.GROQ_API_KEY)
        self.vectorstore = None
        self._initialize_vectorstore()
    
    def _initialize_vectorstore(self):
        """Initialize LangChain vectorstore from Pinecone"""
        try:
            self.vectorstore = PineconeVectorStore.from_existing_index(
                index_name=config.PINECONE_INDEX_NAME,
                embedding=self.embeddings,
                text_key="issue_description"
            )
            print("✅ LangChain vectorstore initialized")
        except Exception as e:
            print(f"⚠️  Warning: Vectorstore initialization issue: {e}")
            try:
                self.vectorstore = PineconeVectorStore(
                    index=self.index,
                    embedding=self.embeddings,
                    text_key="issue_description"
                )
                print("✅ LangChain vectorstore initialized (fallback)")
            except Exception as e2:
                print(f"⚠️  Vectorstore fallback failed: {e2}")

    def _load_local_context(self) -> str:
        """Load all local data (emails, documents, SQL NER) for comprehensive RAG context"""
        context_parts = []

        # 1. Load email NER outputs
        # Also build a mapping from email filename to customer_id for raw email labeling
        self._email_customer_map = {}
        try:
            email_files = sorted(glob.glob(os.path.join(config.OUTPUT_DIR, "email_*.json")))
            for ef in email_files:
                with open(ef, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                email_name = os.path.basename(ef).replace('.json', '')
                # Build a human-readable label from customer_id, date, and issue_type
                cid = data.get('customer_id') or 'Unknown'
                date_val = data.get('date') or ''
                issue = data.get('issue_type') or ''
                label_parts = [f"Customer {cid}"]
                if date_val and str(date_val) not in ('None', 'null', ''):
                    label_parts.append(f"Date: {date_val}")
                if issue and str(issue) not in ('None', 'null', ''):
                    label_parts.append(f"Issue: {issue}")
                label = ' | '.join(label_parts)
                parts = [f"[{label}]"]
                # Store mapping for raw email files
                self._email_customer_map[email_name] = label
                for key in ['customer_id', 'order_id', 'issue_type', 'issue_description',
                            'sentiment', 'severity', 'department', 'cause', 'agent_id', 'date', 'time_window']:
                    val = data.get(key)
                    if val and str(val) not in ('None', '', 'null'):
                        parts.append(f"  {key}: {val}")
                context_parts.append('\n'.join(parts))
        except Exception as e:
            print(f"⚠️  Error loading email data: {e}")

        # 2. Load raw email text files
        try:
            email_txt_files = sorted(glob.glob(os.path.join(config.EMAIL_DIR, "*.txt")))
            for tf in email_txt_files:
                with open(tf, 'r', encoding='utf-8') as f:
                    text = f.read().strip()
                if text:
                    email_base = os.path.basename(tf).replace('.txt', '')
                    # Use the human-readable label from parsed NER data if available
                    label = self._email_customer_map.get(email_base, f"Email from {email_base}")
                    context_parts.append(f"[Raw: {label}]\n{text}")
        except Exception as e:
            print(f"⚠️  Error loading raw emails: {e}")

        # 3. Load document NER outputs
        try:
            doc_ner_files = [f for f in os.listdir(config.OUTPUT_DIR)
                            if f.endswith('_ner.json') and not f.startswith('email_') and f != 'database_ner_flat.json']
            for df in doc_ner_files:
                with open(os.path.join(config.OUTPUT_DIR, df), 'r', encoding='utf-8') as f:
                    content = f.read()
                # Strip markdown code blocks if present
                if content.strip().startswith('```'):
                    content = content.strip().lstrip('`').lstrip('json\n').rstrip('`').strip()
                try:
                    doc_data = json.loads(content)
                    doc_name = df.replace('_ner.json', '')
                    parts = [f"[Document: {doc_name}]"]
                    for key, values in doc_data.items():
                        if isinstance(values, list) and values:
                            parts.append(f"  {key}: {', '.join(str(v) for v in values[:10])}")
                        elif values:
                            parts.append(f"  {key}: {values}")
                    context_parts.append('\n'.join(parts))
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            print(f"⚠️  Error loading document NER: {e}")

        # 4. Load database NER flat file (SQL data)
        try:
            db_file = os.path.join(config.OUTPUT_DIR, 'database_ner_flat.json')
            if os.path.exists(db_file):
                with open(db_file, 'r', encoding='utf-8') as f:
                    db_data = json.load(f)
                if isinstance(db_data, list):
                    parts = ["[Database/SQL Entities]"]
                    for record in db_data[:50]:
                        etype = record.get('entity_type', '')
                        evalue = record.get('entity_value', '')
                        eid = record.get('entity_id', '')
                        parts.append(f"  {etype}: {evalue} (id: {eid})")
                    context_parts.append('\n'.join(parts))
        except Exception as e:
            print(f"⚠️  Error loading database NER: {e}")

        return '\n\n'.join(context_parts)

    
    def create_qa_chain(self):
        """Create a QA chain for enterprise knowledge"""
        
        prompt_template = """You are an enterprise intelligence assistant. Answer questions based on the provided context.

IMPORTANT: When referencing data sources, NEVER cite internal file names or email numbers (e.g. "email 01", "email_15").
Instead, always identify records by their Customer ID (e.g. "Customer C102"), date, order ID, or issue type.

Context: {context}

Question: {question}

Provide a comprehensive answer using the context. If the context doesn't contain relevant information, 
say "Information not available in knowledge base" and suggest what data might help."""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 3})
        
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | self.llm
            | StrOutputParser()
        )
        
        return chain, retriever
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """Answer a question using RAG pipeline"""
        try:
            qa_chain, retriever = self.create_qa_chain()
            answer = qa_chain.invoke(question)
            
            # Get source documents
            source_docs = retriever.invoke(question)
            
            return {
                "answer": answer,
                "source_documents": [
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                    } for doc in source_docs
                ],
                "success": True
            }
        
        except Exception as e:
            print(f"❌ Error answering question: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "source_documents": [],
                "success": False
            }
    
    def summarize_entities(self, entities: List[Dict]) -> str:
        """Summarize a list of entities"""
        try:
            entity_text = "\n".join([
                f"- {e.get('entity_type', 'Unknown')}: {e.get('value', '')} ({e.get('id', '')})"
                for e in entities[:10]
            ])
            
            prompt = f"""
            Summarize the following extracted entities:
            {entity_text}
            
            Provide a brief 2-3 sentence summary of what these entities represent.
            """
            
            message = self.groq_client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            return message.choices[0].message.content
        
        except Exception as e:
            print(f"❌ Error summarizing entities: {e}")
            return "Summary unavailable"
    
    def extract_insights(self, data: Dict) -> Dict[str, str]:
        """Extract insights from data using LLM"""
        try:
            insights = {}
            
            # Issue analysis
            if "issue_type" in data:
                prompt = f"What are the key insights about {data['issue_type']} issues? Provide 2-3 bullet points."
                message = self.groq_client.chat.completions.create(
                    model=config.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5
                )
                insights["issue_insights"] = message.choices[0].message.content
            
            # Sentiment analysis
            if "sentiment" in data:
                prompt = f"Analyze the sentiment '{data['sentiment']}' in customer feedback. What does this mean for business?"
                message = self.groq_client.chat.completions.create(
                    model=config.GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5
                )
                insights["sentiment_insights"] = message.choices[0].message.content
            
            return insights
        
        except Exception as e:
            print(f"❌ Error extracting insights: {e}")
            return {}
    
    def semantic_search_with_rag(self, query: str, top_k: int = 5) -> Dict:
        """Perform semantic search across Pinecone + local data and answer with RAG"""
        try:
            sources = []
            pinecone_context = ""

            # 1. Vector search from Pinecone (if available)
            if self.vectorstore:
                try:
                    docs = self.vectorstore.similarity_search(query, k=top_k)
                    if docs:
                        pinecone_context = "\n".join([doc.page_content for doc in docs])
                        sources = [
                            {"content": doc.page_content[:200], "metadata": doc.metadata}
                            for doc in docs
                        ]
                except Exception as ve:
                    print(f"⚠️  Vector search warning: {ve}")

            # 2. Load all local data (emails, documents, SQL)
            local_context = self._load_local_context()

            # 3. Combine both contexts (truncate to fit LLM context window)
            combined_context = ""
            if pinecone_context:
                combined_context += f"--- Pinecone Search Results ---\n{pinecone_context}\n\n"
            if local_context:
                # Trim to ~12000 chars to stay within token limits
                combined_context += f"--- Enterprise Data (Emails, Documents, Database) ---\n{local_context[:12000]}"

            if not combined_context.strip():
                return {
                    "query": query,
                    "answer": "No data found. Please ensure emails, documents, and database data have been processed.",
                    "sources": [],
                    "success": False
                }

            prompt = f"""You are an enterprise intelligence assistant for an email and document analysis system.
You have access to parsed emails, document NER extractions, and database entity data.
Answer the user's question accurately based ONLY on the provided data. 
If you list items, use numbered lists. Be specific with names, IDs, dates, and details.

IMPORTANT: When referencing data sources, NEVER cite internal file names or email numbers (e.g. "email 01", "email_15").
Instead, always identify records by their Customer ID (e.g. "Customer C102"), date, order ID, or issue type.
This makes the response meaningful to business users who have no knowledge of internal file naming.

Enterprise Data:
{combined_context}

Question: {query}

Answer:"""

            message = self.groq_client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            return {
                "query": query,
                "answer": message.choices[0].message.content,
                "sources": sources,
                "success": True
            }

        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return {
                "query": query,
                "answer": f"Error: {str(e)}",
                "sources": [],
                "success": False
            }
    
    def generate_recommendations(self, issue_type: str, sentiment: str) -> str:
        """Generate recommendations based on issue and sentiment"""
        try:
            prompt = f"""
            Based on the following:
            - Issue Type: {issue_type}
            - Customer Sentiment: {sentiment}
            
            Provide 3 actionable recommendations to improve customer experience and resolve this issue.
            """
            
            message = self.groq_client.chat.completions.create(
                model=config.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            return message.choices[0].message.content
        
        except Exception as e:
            print(f"❌ Error generating recommendations: {e}")
            return "Recommendations unavailable"


# Test function
if __name__ == "__main__":
    config.validate_config()
    
    rag = LangChainRAGPipeline()
    print("✅ LangChain RAG Pipeline initialized!")
    
    # Test semantic search
    # result = rag.semantic_search_with_rag("What are the common delivery issues?")
    # print(f"\nSearch Result:\n{json.dumps(result, indent=2)}")
