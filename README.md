# 🤖 AI Knowledge Graph Builder for Enterprise Intelligence

An AI-powered platform that automatically extracts entities and relationships from enterprise data (emails, databases, documents) and builds dynamic knowledge graphs for intelligent business insights.

## 🎯 Project Objectives

✅ **Automated Data Ingestion** - Process multiple data sources (emails, SQL databases, documents)
✅ **Entity & Relationship Extraction** - LLM-based Named Entity Recognition (NER)
✅ **Knowledge Graph Construction** - Build and store in Neo4j
✅ **Semantic Search** - Find similar entities and patterns using Pinecone embeddings
✅ **RAG Pipeline** - Retrieve relevant context and generate intelligent answers
✅ **Interactive Dashboard** - Visualize, search, and analyze knowledge graphs
✅ **KPI Tracking** - Monitor data quality, customer satisfaction, agent performance

---

## 🏗️ Architecture

```
┌─────────────────┐
│  Data Sources   │
│ Emails, SQL, Docs
└────────┬────────┘
         │
    ┌────▼─────────┐
    │ NER Pipeline │ (Existing)
    └────┬─────────┘
         │
    ┌────▼──────────────┐
    │  Data Processing  │
    │  JSON Outputs     │
    └────┬──────────────┘
         │
    ┌────▼─────────────────────────┐
    │   Pinecone Embeddings        │ (NEW)
    │   Vector Database Storage    │
    └────┬─────────────────────────┘
         │
    ┌────┴──────────────┬──────────────────┬──────────────┐
    │                   │                  │              │
┌───▼──────┐  ┌────────▼──────┐  ┌──────▼──────┐  ┌────▼────────┐
│ Neo4j    │  │  LangChain    │  │ KPI Metrics │  │ Streamlit   │
│ Graphs   │  │  RAG Pipeline │  │ Calculator  │  │ Dashboard   │
└──────────┘  └───────────────┘  └─────────────┘  └─────────────┘
```

---

## 📦 New Modules Created

| Module | Purpose | Key Functions |
|--------|---------|---|
| **config.py** | Central configuration & API keys | `validate_config()` |
| **pinecone_handler.py** | Vector DB management | `semantic_search()`, `store_entity()`, `load_and_store_ner_outputs()` |
| **langchain_rag.py** | RAG pipeline orchestration | `answer_question()`, `semantic_search_with_rag()`, `generate_recommendations()` |
| **kpi_metrics.py** | KPI calculation engine | `calculate_all_kpis()`, comprehensive metrics |
| **dashboard.py** | Streamlit interactive UI | 5 tabs with full features |

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example to actual .env
copy .env.example .env

# Edit .env with your API keys
notepad .env
```

**Required API Keys:**
- `GROQ_API_KEY` - From https://groq.com
- `OPENAI_API_KEY` - From https://openai.com
- `PINECONE_API_KEY` - From https://pinecone.io (free tier)
- `NEO4J_PASSWORD` - Your existing Neo4j instance

### 3. Start the Dashboard
```bash
# Windows Batch
start.bat

# Or PowerShell
powershell -ExecutionPolicy Bypass -File start.ps1

# Or directly
streamlit run dashboard.py
```

---

## 📊 Dashboard Features

### 📈 Tab 1: Analytics & KPIs
- **Real-time KPI Cards**: Data quality, customer satisfaction, issue counts
- **Issue Distribution Charts**: Visual breakdown of issue types
- **Sentiment Analysis**: Customer feedback sentiment trends
- **Agent Performance**: Individual agent metrics and rankings
- **Customer Metrics**: Customer satisfaction and engagement stats
- **Export Options**: Save reports as JSON/CSV

### 🔍 Tab 2: Semantic Search
- Natural language search across all enterprise data
- Filter by entity type (Issues, Customers, Agents, Documents)
- Adjustable result count
- View detailed metadata and source information

### 💬 Tab 3: Q&A Chatbot
- Ask questions about your enterprise data
- RAG-powered intelligent answers with source citations
- Chat history tracking
- Context-aware responses using Pinecone + LLM

### 🕸️ Tab 4: Graph Visualization
- Interactive Neo4j knowledge graph visualization
- Explore entity relationships
- Navigate connected data
- Customize visualization

### 📋 Tab 5: System Status
- Component initialization status
- Configuration details
- Available file browser
- System diagnostics

---

## 📊 KPI Metrics Included

### Data Quality (5 KPIs)
- Total files processed
- Data validity rate
- Records count
- Missing fields tracking
- Data completeness percentage

### Issue Analytics (6 KPIs)
- Total unique issues
- Issue type distribution
- Top 5 issue types
- Critical issue count
- Critical rate percentage

### Sentiment Analysis (8 KPIs)
- Positive/Negative/Neutral counts & rates
- Sentiment distribution breakdown
- Customer satisfaction score

### Agent Performance (5 KPIs)
- Total agents count
- Issues per agent
- Satisfaction score per agent
- Top agents ranking
- Average workload

### Customer Metrics (5 KPIs)
- Unique customers count
- Orders per customer
- High satisfaction rate
- Customer lifetime metrics

### Graph Metrics (3 KPIs)
- Neo4j node counts
- Relationship statistics
- Graph coverage metrics

**Total: 32+ KPIs tracked**

---

## 🔑 API Integrations

| API | Purpose | Model/Tier |
|-----|---------|-----------|
| **Groq** | LLM for entity extraction & generation | openai/gpt-oss-120b (120B params) |
| **OpenAI** | Embeddings & semantic search | text-embedding-3-small |
| **Pinecone** | Vector database | Free tier (suitable for testing) |
| **Neo4j** | Knowledge graph storage | Cloud instance |

---

## 📁 Project Structure

```
d:\Data Ingestion Infosys\
│
├── 🚀 STARTUP FILES
│   ├── start.bat                 # Windows batch starter
│   ├── start.ps1                 # PowerShell starter
│   ├── SETUP_GUIDE.md            # Detailed setup instructions
│   └── README.md                 # This file
│
├── ⚙️ CONFIGURATION
│   ├── config.py                 # Central configuration
│   ├── .env.example              # API key template
│   └── .env                      # YOUR API keys (create this)
│
├── 📦 CORE MODULES (NEW)
│   ├── pinecone_handler.py      # Vector database management
│   ├── langchain_rag.py         # RAG pipeline
│   ├── kpi_metrics.py           # KPI calculations
│   ├── dashboard.py             # Streamlit dashboard
│   └── requirements.txt          # Python dependencies
│
├── 📚 EXISTING MODULES
│   ├── pipeline.py              # Neo4j sync pipeline
│   ├── pipeline_ner_email.py    # Email NER extraction
│   ├── pipeline_database_ner_flat.py  # DB NER extraction
│   └── ner/                     # NER modules
│       ├── ner_extractor.py
│       ├── ner_database_direct.py
│       └── ner_database_extractor.py
│
├── 📊 DATA
│   ├── data/emails/             # Email input files
│   ├── outputs/                 # NER JSON outputs
│   └── enterprise_intelligence_sqlite.sql  # Database schema
│
└── 🗄️ DATABASE
    └── Neo4j cloud instance (existing)
```

---

## 🎓 How It Works

### Data Flow

```
1. EMAIL INPUT
   └─> ner_extractor.py (Groq LLM)
       └─> JSON output
           └─> Pinecone embeddings
               └─> Dashboard search
```

```
2. DATABASE INPUT
   └─> ner_database_direct.py (Regex parsing)
       └─> Flat NER JSON
           └─> Pinecone embeddings
               └─> Dashboard search
```

```
3. RAG PIPELINE
   User Question
   └─> Pinecone semantic search
       └─> LangChain retrieval
           └─> Groq LLM generation
               └─> Answer with sources
```

```
4. KPI CALCULATION
   JSON outputs
   └─> kpi_metrics.py analysis
       └─> Dashboard visualization
           └─> Export (JSON/CSV)
```

---

## 🔧 Troubleshooting

### Issue: "API Key Error"
**Solution:**
- Check `.env` file exists
- Verify key format (no extra quotes)
- Ensure keys are active/not expired

### Issue: "Pinecone Index Not Found"
**Solution:**
- First run auto-creates index
- Check API key validity
- Verify region: `us-west1-gcp`

### Issue: "Streamlit Won't Start"
**Solution:**
```bash
pip install --upgrade streamlit
streamlit cache clear
streamlit run dashboard.py
```

### Issue: "Neo4j Connection Failed"
**Solution:**
- Verify instance is running
- Check connection string
- Verify Neo4j password in .env

---

## 📈 Next Steps

1. **Get API Keys** (5 minutes)
   - Groq: https://groq.com
   - OpenAI: https://openai.com
   - Pinecone: https://pinecone.io

2. **Setup Environment** (2 minutes)
   - Copy `.env.example` → `.env`
   - Add API keys
   - Run `start.bat` or `start.ps1`

3. **Load Your Data** (5 minutes)
   - Place emails in `data/emails/`
   - Run existing NER pipelines
   - Click "Load NER Outputs" in dashboard

4. **Explore Dashboard** (15 minutes)
   - Try semantic search
   - Ask Q&A questions
   - View KPI analytics
   - Visualize graph

5. **Customize** (ongoing)
   - Add business-specific KPIs
   - Enhance visualizations
   - Integrate more data sources

---

## 💡 Use Cases

✅ **Customer Support Analysis** - Identify common issues, agent performance
✅ **Sentiment Tracking** - Monitor customer satisfaction trends
✅ **Knowledge Discovery** - Find hidden relationships in enterprise data
✅ **Intelligent Search** - Semantic search across all documents
✅ **Decision Support** - Ask questions, get context-aware answers
✅ **Performance Monitoring** - Track KPIs and business metrics
✅ **Risk Detection** - Identify critical issues and patterns

---

## 📚 Documentation

- **SETUP_GUIDE.md** - Detailed installation & configuration
- **config.py** - View configuration options
- **Module docstrings** - Read inline documentation
- **Streamlit docs** - https://docs.streamlit.io
- **LangChain docs** - https://python.langchain.com
- **Pinecone docs** - https://docs.pinecone.io

---

## 🤝 Contributing

To enhance this project:

1. **Add Custom KPIs** - Edit `kpi_metrics.py`
2. **Improve RAG** - Enhance `langchain_rag.py`
3. **Customize Dashboard** - Modify `dashboard.py`
4. **Add Data Sources** - Create new ingestion modules
5. **Optimize Performance** - Profile and improve

---

## 📝 License & Credits

**Made for:** Infosys Internship Program
**Created with:** Streamlit, LangChain, Pinecone, Neo4j, Groq
**Purpose:** Enterprise Intelligence & Knowledge Graph Building

---

## ✅ Checklist

- [ ] Install Python 3.8+
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create `.env` file with API keys
- [ ] Run: `streamlit run dashboard.py`
- [ ] Load NER outputs to Pinecone
- [ ] Calculate KPIs
- [ ] Try semantic search
- [ ] Ask Q&A questions
- [ ] View graph visualization
- [ ] Export KPI reports

---

## 🚀 Ready to Go!

You now have a complete AI-powered enterprise intelligence platform with:
- ✅ Vector embeddings (Pinecone)
- ✅ RAG capabilities (LangChain)
- ✅ Interactive dashboard (Streamlit)
- ✅ KPI tracking (32+ metrics)
- ✅ Semantic search
- ✅ Knowledge graphs (Neo4j)

**Start the dashboard and begin exploring your enterprise data!**

```bash
streamlit run dashboard.py
```

---

**Questions?** Check SETUP_GUIDE.md or review the inline code documentation.

**Good luck with your Infosys internship!** 🎓
