import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import json
import networkx as nx
from pyvis.network import Network
import config
from pinecone_handler import PineconeHandler
from langchain_rag import LangChainRAGPipeline
from kpi_metrics import KPICalculator
from neo4j import GraphDatabase
import os

# Page config
st.set_page_config(
    page_title=config.STREAMLIT_PAGE_TITLE,
    page_icon=config.STREAMLIT_PAGE_ICON,
    layout=config.STREAMLIT_LAYOUT
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .header-title {
        color: #1f77b4;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subheader-title {
        color: #ff7f0e;
        font-size: 1.5em;
        margin-top: 20px;
    }
    /* Hide Deploy button and menu */
    [data-testid="stToolbar"] {
        display: none;
    }
    /* WhatsApp-style chat container */
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 60vh;
        overflow-y: auto;
        padding: 16px 8px;
        border-radius: 12px;
        background: #0e1117;
        border: 1px solid #1e2530;
        margin-bottom: 8px;
        scroll-behavior: smooth;
    }
    .chat-container .stChatMessage {
        max-width: 85%;
    }
    /* Auto-scroll JS anchor */
    #chat-anchor {
        height: 0;
        overflow: hidden;
    }
    </style>
""", unsafe_allow_html=True)

# ============= SESSION STATE INITIALIZATION =============
if "pinecone_handler" not in st.session_state:
    st.session_state.pinecone_handler = None
if "rag_pipeline" not in st.session_state:
    st.session_state.rag_pipeline = None
if "kpi_calc" not in st.session_state:
    st.session_state.kpi_calc = None
if "kpis" not in st.session_state:
    st.session_state.kpis = None

# ============= INITIALIZE COMPONENTS =============
@st.cache_resource
def initialize_handlers():
    """Initialize all handlers"""
    try:
        ph = PineconeHandler()
        rag = LangChainRAGPipeline()
        kpi = KPICalculator()
        return ph, rag, kpi
    except Exception as e:
        st.error(f"❌ Initialization Error: {e}")
        return None, None, None

# ============= SIDEBAR =============
with st.sidebar:
    st.markdown("## 📊 Enterprise Intelligence Dashboard")
    st.markdown("---")
    
    # Initialize buttons
    if st.button("🔄 Initialize System"):
        with st.spinner("Initializing components..."):
            ph, rag, kpi = initialize_handlers()
            st.session_state.pinecone_handler = ph
            st.session_state.rag_pipeline = rag
            st.session_state.kpi_calc = kpi
            st.success("✅ System Initialized!")
    
    if st.button("📥 Load NER Outputs to Pinecone"):
        if st.session_state.pinecone_handler:
            with st.spinner("Loading NER outputs..."):
                st.session_state.pinecone_handler.load_and_store_ner_outputs()
                st.success("✅ NER outputs loaded to Pinecone!")
        else:
            st.error("⚠️  Please initialize system first")
    
    st.markdown("---")
    
    # KPI refresh button
    if st.button("📊 Calculate KPIs"):
        if st.session_state.kpi_calc:
            with st.spinner("Calculating KPIs..."):
                st.session_state.kpis = st.session_state.kpi_calc.calculate_all_kpis()
                st.success("✅ KPIs Calculated!")
        else:
            st.error("⚠️  Please initialize system first")
    
    st.markdown("---")
    st.markdown("**System Status:**")
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.pinecone_handler:
            st.success("✅ Pinecone")
        else:
            st.warning("⚠️  Pinecone")
    with col2:
        if st.session_state.rag_pipeline:
            st.success("✅ RAG")
        else:
            st.warning("⚠️  RAG")

# ============= MAIN CONTENT =============
st.markdown('<p class="header-title">📊 AI Knowledge Graph Builder</p>', unsafe_allow_html=True)
st.markdown("*Building Dynamic Knowledge Graphs from Enterprise Data*")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Analytics & KPIs",
    "💬 Q&A Chatbot",
    "🕸️ Graph Visualization",
    "📋 System Status"
])

# ============= TAB 1: ANALYTICS & KPIs =============
with tab1:
    st.markdown('<p class="subheader-title">📊 Key Performance Indicators (KPIs)</p>', unsafe_allow_html=True)
    
    if st.button("🔄 Refresh KPIs", key="refresh_kpis_tab1"):
        if st.session_state.kpi_calc:
            with st.spinner("Calculating KPIs..."):
                st.session_state.kpis = st.session_state.kpi_calc.calculate_all_kpis()
                st.success("✅ KPIs Updated!")
    
    if st.session_state.kpis:
        kpis = st.session_state.kpis
        
        # KPI Summary Cards
        st.markdown("### 🎯 KPI Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            data_quality = kpis.get("data_quality", {}).get("data_completeness", "N/A")
            st.metric("Data Quality", data_quality)
        
        with col2:
            satisfaction = kpis.get("sentiment_analysis", {}).get("customer_satisfaction_score", "N/A")
            st.metric("Customer Satisfaction", satisfaction)
        
        with col3:
            total_issues = kpis.get("issue_analytics", {}).get("total_issues", 0)
            st.metric("Total Issues", total_issues)
        
        with col4:
            critical = kpis.get("issue_analytics", {}).get("critical_issues", 0)
            st.metric("Critical Issues", critical)
        
        st.markdown("---")
        
        # Issue Analytics
        st.markdown("### 📌 Issue Analytics")
        col1, col2 = st.columns(2)
        
        with col1:
            issue_analytics = kpis.get("issue_analytics", {})
            if issue_analytics.get("issue_distribution"):
                fig = go.Figure(data=[
                    go.Bar(x=list(issue_analytics["issue_distribution"].keys()),
                           y=list(issue_analytics["issue_distribution"].values()),
                           marker_color='indianred')
                ])
                fig.update_layout(title="Issue Type Distribution", xaxis_title="Issue Type", yaxis_title="Count")
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            sentiment_data = kpis.get("sentiment_analysis", {})
            if sentiment_data.get("sentiment_distribution"):
                fig = go.Figure(data=[
                    go.Pie(labels=list(sentiment_data["sentiment_distribution"].keys()),
                           values=list(sentiment_data["sentiment_distribution"].values()))
                ])
                fig.update_layout(title="Customer Sentiment Distribution")
                st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Sentiment by Issue Type
        st.markdown("### 🎭 Sentiment by Issue Type")
        sentiment_data = kpis.get("sentiment_analysis", {})
        sentiment_by_issue = sentiment_data.get("sentiment_by_issue", {})
        if sentiment_by_issue:
            # Build a dataframe: rows = issue types, columns = sentiment categories
            rows = []
            for issue, breakdown in sentiment_by_issue.items():
                for sentiment, count in breakdown.items():
                    rows.append({"Issue Type": issue, "Sentiment": sentiment, "Count": count})
            sbi_df = pd.DataFrame(rows)
            
            # Sort issue types by total count descending
            issue_order = sbi_df.groupby("Issue Type")["Count"].sum().sort_values(ascending=False).index.tolist()
            
            color_map = {"Positive": "#2ecc71", "Neutral": "#f39c12", "Negative": "#e74c3c"}
            fig = px.bar(
                sbi_df, x="Issue Type", y="Count", color="Sentiment",
                barmode="group", title="Sentiment Breakdown by Issue Type",
                color_discrete_map=color_map,
                category_orders={"Issue Type": issue_order, "Sentiment": ["Positive", "Neutral", "Negative"]}
            )
            fig.update_layout(xaxis_tickangle=-30)
            st.plotly_chart(fig, use_container_width=True)
        
        # Agent Performance Table (keep the table, remove the chart)
        st.markdown("### 👥 Agent Performance")
        agent_perf = kpis.get("agent_performance", {})
        if agent_perf.get("top_agents"):
            agent_df = pd.DataFrame(agent_perf["top_agents"])
            st.dataframe(agent_df, use_container_width=True)
        
        st.markdown("---")
        
        # Customer Metrics
        st.markdown("### 👤 Customer Metrics")
        col1, col2, col3 = st.columns(3)
        customer_metrics = kpis.get("customer_metrics", {})
        
        with col1:
            st.metric("Unique Customers", customer_metrics.get("unique_customers", 0))
        with col2:
            st.metric("High Satisfaction", customer_metrics.get("high_satisfaction_rate", "N/A"))
        with col3:
            st.metric("Avg Orders/Customer", customer_metrics.get("avg_orders_per_customer", "N/A"))
        
        st.markdown("---")
        
        # Detailed KPI Table
        st.markdown("### 📋 Detailed KPI Report")
        kpi_df = st.session_state.kpi_calc.export_kpis_to_dataframe()
        st.dataframe(kpi_df, use_container_width=True)
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📥 Export as JSON"):
                filepath = st.session_state.kpi_calc.export_kpis_to_json()
                st.success(f"✅ Exported to {filepath}")
        with col2:
            csv = kpi_df.to_csv(index=False)
            st.download_button("📥 Download CSV", csv, "kpi_report.csv")
    
    else:
        st.info("ℹ️  Click 'Calculate KPIs' in the sidebar to generate metrics")

# ============= TAB 2: Q&A CHATBOT =============
with tab2:
    st.markdown('<p class="subheader-title">💬 Intelligent Q&A Assistant</p>', unsafe_allow_html=True)
    
    if not st.session_state.rag_pipeline:
        st.error("⚠️  RAG pipeline not initialized. Click 'Initialize System' in sidebar.")
    else:
        # Initialize chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []
        
        # Clear chat button in a small column at top
        col_header, col_clear = st.columns([5, 1])
        with col_header:
            st.caption("💡 Ask questions about your enterprise data. The AI will search the knowledge base and generate answers.")
        with col_clear:
            if st.button("🗑️ Clear", key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()
        
        # Display chat history in a scrollable WhatsApp-style container
        chat_container = st.container(height=500)
        with chat_container:
            for msg in st.session_state.chat_history:
                with st.chat_message(msg["role"], avatar="🧑‍💼" if msg["role"] == "user" else "🤖"):
                    st.markdown(msg["content"])
                    if msg.get("sources"):
                        with st.expander("📚 Sources"):
                            for source in msg["sources"]:
                                st.markdown(f"- {source.get('content', 'N/A')}")
        
        # Chat input pinned at bottom
        if question := st.chat_input("Ask about your email data..."):
            # Add user message to history
            st.session_state.chat_history.append({"role": "user", "content": question})
            
            # Generate response
            with st.spinner("Thinking..."):
                try:
                    result = st.session_state.rag_pipeline.semantic_search_with_rag(question)
                    
                    if result.get("success"):
                        answer = result.get("answer", "No answer generated")
                        sources = result.get("sources", [])
                    else:
                        answer = result.get("answer", result.get("error", "Something went wrong. Please try again."))
                        sources = []
                    
                    # Add assistant message to history
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources
                    })
                
                except Exception as e:
                    error_msg = f"Sorry, an error occurred: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
            
            st.rerun()

# ============= TAB 3: GRAPH VISUALIZATION =============
with tab3:
    st.markdown('<p class="subheader-title">🕸️ Knowledge Graph Visualization</p>', unsafe_allow_html=True)
    
    st.info("💡 This visualization shows the Neo4j knowledge graph with entities and their relationships.")
    
    # Color palette for entity types
    ENTITY_COLORS = {
        "Person": "#e74c3c",
        "Organization": "#3498db",
        "Issue": "#e67e22",
        "Customer": "#2ecc71",
        "Agent": "#9b59b6",
        "Product": "#1abc9c",
        "Location": "#f39c12",
        "Date": "#95a5a6",
        "Email": "#34495e",
        "Department": "#d35400",
        "Technology": "#16a085",
        "Service": "#8e44ad",
        "Metric": "#c0392b",
        "Process": "#2980b9",
        "Tool": "#27ae60",
    }
    DEFAULT_COLOR = "#7f8c8d"
    
    # Fetch real data from Neo4j
    try:
        if config.NEO4J_PASSWORD is None:
            st.warning("⚠️  Neo4j password not configured. Graph visualization unavailable.")
        else:
            driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
            )
            
            with driver.session() as session:
                # Fetch all nodes
                nodes_result = session.run("MATCH (n) RETURN elementId(n) as id, labels(n)[0] as label, coalesce(n.name, n.id, n.type, n.description, '') as name LIMIT 500")
                nodes_data = nodes_result.data()
                
                # Fetch all relationships
                rels_result = session.run("MATCH (a)-[r]->(b) RETURN elementId(a) as source, elementId(b) as target, type(r) as rel_type LIMIT 1000")
                rels_data = rels_result.data()
            
            driver.close()
            
            st.success(f"✅ Loaded {len(nodes_data)} nodes and {len(rels_data)} relationships from Neo4j")
            
            # Build node map with clean names
            node_map = {}
            label_set = set()
            for node in nodes_data:
                node_id = node['id']
                label = node['label'] or 'Unknown'
                name = (node['name'] or '').strip()
                if not name:
                    name = f"{label}_{len(node_map)}"
                # Truncate long names for display
                display_name = name[:30] + "..." if len(name) > 30 else name
                node_map[node_id] = {"name": name, "display": display_name, "label": label}
                label_set.add(label)
            
            # --- Filters ---
            st.markdown("### 🎛️ Filters")
            filter_col1, filter_col2 = st.columns([3, 1])
            with filter_col1:
                selected_labels = st.multiselect(
                    "Show entity types:",
                    sorted(label_set),
                    default=sorted(label_set)
                )
            with filter_col2:
                max_nodes = st.slider("Max nodes:", 10, min(200, len(nodes_data)), min(80, len(nodes_data)))
            
            # Filter nodes
            filtered_ids = set()
            count = 0
            for nid, info in node_map.items():
                if info["label"] in selected_labels:
                    filtered_ids.add(nid)
                    count += 1
                    if count >= max_nodes:
                        break
            
            # Filter edges to only include filtered nodes
            filtered_rels = [r for r in rels_data if r['source'] in filtered_ids and r['target'] in filtered_ids]
            
            st.info(f"📊 Showing {len(filtered_ids)} nodes and {len(filtered_rels)} relationships")
            
            # --- Legend ---
            active_labels = sorted(set(node_map[nid]["label"] for nid in filtered_ids))
            legend_html = "<div style='display:flex;flex-wrap:wrap;gap:12px;margin-bottom:16px;'>"
            for lbl in active_labels:
                color = ENTITY_COLORS.get(lbl, DEFAULT_COLOR)
                legend_html += f"<span style='display:inline-flex;align-items:center;gap:4px;'><span style='width:14px;height:14px;border-radius:50%;background:{color};display:inline-block;'></span> <b>{lbl}</b></span>"
            legend_html += "</div>"
            st.markdown(legend_html, unsafe_allow_html=True)
            
            # --- Build PyVis Network ---
            try:
                net = Network(
                    height="700px",
                    width="100%",
                    directed=True,
                    notebook=False,
                    bgcolor="#0e1117",
                    font_color="white",
                )
                
                # Add nodes with colors and readable labels
                for nid in filtered_ids:
                    info = node_map[nid]
                    color = ENTITY_COLORS.get(info["label"], DEFAULT_COLOR)
                    net.add_node(
                        nid,
                        label=info["display"],
                        title=f"<b>{info['label']}</b><br>{info['name']}",
                        color=color,
                        size=25,
                        font={"size": 12, "color": "white", "strokeWidth": 2, "strokeColor": "#000"},
                    )
                
                # Add edges with relationship labels
                for rel in filtered_rels:
                    net.add_edge(
                        rel['source'],
                        rel['target'],
                        title=rel['rel_type'],
                        label=rel['rel_type'],
                        color={"color": "#555", "highlight": "#ff0"},
                        font={"size": 9, "color": "#aaa", "strokeWidth": 0},
                        arrows="to",
                        width=1.5,
                        smooth={"type": "curvedCW", "roundness": 0.15},
                    )
                
                # Physics settings for better layout
                net.set_options("""
                {
                  "physics": {
                    "enabled": true,
                    "solver": "forceAtlas2Based",
                    "forceAtlas2Based": {
                      "gravitationalConstant": -80,
                      "centralGravity": 0.01,
                      "springLength": 150,
                      "springConstant": 0.05,
                      "damping": 0.4,
                      "avoidOverlap": 0.8
                    },
                    "stabilization": {
                      "enabled": true,
                      "iterations": 200
                    }
                  },
                  "interaction": {
                    "hover": true,
                    "tooltipDelay": 100,
                    "zoomView": true,
                    "dragView": true,
                    "navigationButtons": true
                  },
                  "edges": {
                    "smooth": {
                      "type": "curvedCW",
                      "roundness": 0.15
                    }
                  }
                }
                """)
                
                net.write_html("graph.html")
                
                if os.path.exists("graph.html"):
                    with open("graph.html", "r", encoding="utf-8") as f:
                        html_string = f.read()
                    st.components.v1.html(html_string, height=750, scrolling=True)
                else:
                    st.warning("⚠️  Graph file could not be created")
            except Exception as vis_error:
                st.warning(f"⚠️  Interactive graph unavailable: {vis_error}")
                st.info("Showing fallback static visualization...")
                
                # Fallback: Plotly
                try:
                    G = nx.DiGraph()
                    for nid in filtered_ids:
                        info = node_map[nid]
                        G.add_node(nid, label=info["label"], name=info["display"])
                    for rel in filtered_rels:
                        G.add_edge(rel['source'], rel['target'], rel_type=rel['rel_type'])
                    
                    pos = nx.spring_layout(G, k=3, iterations=80, seed=42)
                    
                    # Edge traces
                    edge_x, edge_y = [], []
                    for edge in G.edges():
                        x0, y0 = pos[edge[0]]
                        x1, y1 = pos[edge[1]]
                        edge_x += [x0, x1, None]
                        edge_y += [y0, y1, None]
                    
                    edge_trace = go.Scatter(
                        x=edge_x, y=edge_y,
                        mode='lines',
                        line=dict(width=0.8, color='rgba(150,150,150,0.4)'),
                        hoverinfo='none'
                    )
                    
                    # Node traces grouped by label for legend
                    traces = [edge_trace]
                    for lbl in active_labels:
                        nx_list, ny_list, nt_list = [], [], []
                        for nid in filtered_ids:
                            info = node_map[nid]
                            if info["label"] == lbl and nid in pos:
                                x, y = pos[nid]
                                nx_list.append(x)
                                ny_list.append(y)
                                nt_list.append(info["display"])
                        
                        color = ENTITY_COLORS.get(lbl, DEFAULT_COLOR)
                        traces.append(go.Scatter(
                            x=nx_list, y=ny_list,
                            mode='markers+text',
                            name=lbl,
                            text=nt_list,
                            textposition="top center",
                            textfont=dict(size=9, color="white"),
                            hoverinfo='text',
                            marker=dict(size=16, color=color, line=dict(width=1, color='white'))
                        ))
                    
                    fig = go.Figure(data=traces)
                    fig.update_layout(
                        showlegend=True,
                        legend=dict(font=dict(color="white")),
                        hovermode='closest',
                        height=700,
                        template='plotly_dark',
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        margin=dict(l=0, r=0, t=0, b=0),
                    )
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as fallback_error:
                    st.error(f"Fallback visualization also failed: {fallback_error}")
    
    except Exception as e:
        st.warning(f"⚠️  Could not load Neo4j graph: {e}")
        st.info("ℹ️  Ensure Neo4j connection is properly configured and password is set")

# ============= TAB 4: SYSTEM STATUS =============
with tab4:
    st.markdown('<p class="subheader-title">📋 System Status & Configuration</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Initialized Components")
        status = {
            "Pinecone Handler": st.session_state.pinecone_handler is not None,
            "RAG Pipeline": st.session_state.rag_pipeline is not None,
            "KPI Calculator": st.session_state.kpi_calc is not None,
            "KPIs Calculated": st.session_state.kpis is not None
        }
        
        for component, status_val in status.items():
            icon = "✅" if status_val else "❌"
            st.write(f"{icon} {component}")
    
    with col2:
        st.markdown("### 🔧 Configuration")
        st.write(f"**Output Directory:** `{config.OUTPUT_DIR}`")
        st.write(f"**Data Directory:** `{config.DATA_DIR}`")
        st.write(f"**Pinecone Index:** `{config.PINECONE_INDEX_NAME}`")
        st.write(f"**LLM Model:** `{config.GROQ_MODEL}`")
    
    st.markdown("---")
    
    # File browser
    st.markdown("### 📁 Available Files")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Output Files:**")
        if os.path.exists(config.OUTPUT_DIR):
            files = os.listdir(config.OUTPUT_DIR)
            json_files = [f for f in files if f.endswith('.json')]
            st.write(f"Total JSON files: {len(json_files)}")
            
            # Show sample files
            for file in json_files[:5]:
                st.write(f"- {file}")
            if len(json_files) > 5:
                st.write(f"... and {len(json_files) - 5} more")
    
    with col2:
        st.markdown("**Email Data:**")
        if os.path.exists(config.EMAIL_DIR):
            emails = [f for f in os.listdir(config.EMAIL_DIR) if f.endswith('.txt')]
            st.write(f"Total email files: {len(emails)}")
            
            if len(emails) > 0:
                st.write(f"Sample: {emails[0]}")

# ============= FOOTER =============
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: gray; font-size: 0.8em;">
    🤖 AI Knowledge Graph Builder for Enterprise Intelligence | Built with Streamlit + LangChain + Pinecone<br>
    Made for Infosys Internship Program
    </div>
""", unsafe_allow_html=True)
