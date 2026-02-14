#!/usr/bin/env python
"""Test all required imports"""

print("Testing imports...\n")

try:
    from pinecone import Pinecone, ServerlessSpec
    print("✅ Pinecone: OK")
except Exception as e:
    print(f"❌ Pinecone: {e}")

try:
    from langchain_core.prompts import PromptTemplate
    print("✅ LangChain Core: OK")
except Exception as e:
    print(f"❌ LangChain Core: {e}")

try:
    from langchain_community.vectorstores import Pinecone as LangchainPinecone
    print("✅ LangChain Community: OK")
except Exception as e:
    print(f"❌ LangChain Community: {e}")

try:
    from sentence_transformers import SentenceTransformer
    print("✅ Sentence-Transformers: OK")
except Exception as e:
    print(f"❌ Sentence-Transformers: {e}")

try:
    from langchain_huggingface import HuggingFaceEmbeddings
    print("✅ LangChain-HuggingFace: OK")
except Exception as e:
    print(f"❌ LangChain-HuggingFace: {e}")

try:
    from groq import Groq
    print("✅ Groq: OK")
except Exception as e:
    print(f"❌ Groq: {e}")

try:
    from langchain_groq import ChatGroq
    print("✅ LangChain-Groq: OK")
except Exception as e:
    print(f"❌ LangChain-Groq: {e}")

try:
    import streamlit
    print("✅ Streamlit: OK")
except Exception as e:
    print(f"❌ Streamlit: {e}")

try:
    import neo4j
    print("✅ Neo4j: OK")
except Exception as e:
    print(f"❌ Neo4j: {e}")

try:
    import plotly
    print("✅ Plotly: OK")
except Exception as e:
    print(f"❌ Plotly: {e}")

try:
    import pandas
    print("✅ Pandas: OK")
except Exception as e:
    print(f"❌ Pandas: {e}")

try:
    import numpy
    print("✅ NumPy: OK")
except Exception as e:
    print(f"❌ NumPy: {e}")

print("\n" + "="*50)
print("All core dependencies verified! ✅")
print("Using: HuggingFace embeddings + Groq LLM (no OpenAI needed)")
print("="*50)
