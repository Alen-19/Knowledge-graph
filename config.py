import os
from dotenv import load_dotenv

load_dotenv()

# ============= API KEYS =============
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# ============= EMBEDDING CONFIG =============
# Using Hugging Face (FREE) instead of OpenAI
HUGGINGFACE_MODEL = "sentence-transformers/all-MiniLM-L6-v2"  # Free, fast, good quality
EMBEDDING_DIMENSION = 384  # Dimension for the HF model

# ============= NEO4J CONFIG =============
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://2c6d793b.databases.neo4j.io:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# ============= PINECONE CONFIG =============
PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "enterprise-knowledge-graph")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")
PINECONE_DIMENSION = EMBEDDING_DIMENSION  # 384 for HuggingFace sentence-transformers model

# ============= PATHS =============
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "outputs")
DATA_DIR = os.getenv("DATA_DIR", "data")
EMAIL_DIR = os.path.join(DATA_DIR, "emails")

# ============= LLM CONFIG =============
GROQ_MODEL = "openai/gpt-oss-120b"

# ============= STREAMLIT CONFIG =============
STREAMLIT_PAGE_TITLE = "Enterprise Intelligence Dashboard"
STREAMLIT_PAGE_ICON = "📊"
STREAMLIT_LAYOUT = "wide"

# ============= KPI THRESHOLDS =============
KPI_THRESHOLDS = {
    "positive_sentiment": 0.6,
    "negative_sentiment": 0.3,
    "issue_critical": ["Critical", "High"],
    "resolution_time_hours": 24
}

# ============= VALIDATION =============
def validate_config():
    """Validate that all required API keys are set"""
    required_keys = [
        GROQ_API_KEY,
        NEO4J_PASSWORD,
        PINECONE_API_KEY
    ]
    missing = [i for i, key in enumerate(required_keys) if not key]
    if missing:
        print("⚠️  Warning: Some API keys are missing. Update .env file.")
    return True

if __name__ == "__main__":
    validate_config()
    print("✅ Config loaded successfully!")
