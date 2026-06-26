# ==========================================
# MONKEY PATCH TO FIX CORPORATE SSL ERRORS
# ==========================================
import requests
import urllib3

# Suppress the "Unverified HTTPS request" warnings to keep the console clean
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. Monkey patch requests.get to bypass SSL verification
_original_requests_get = requests.get
def _patched_requests_get(*args, **kwargs):
    kwargs['verify'] = False
    return _original_requests_get(*args, **kwargs)
requests.get = _patched_requests_get

# 2. Monkey patch requests.Session.request as well for broader coverage
_original_session_request = requests.Session.request
def _patched_session_request(self, method, url, **kwargs):
    kwargs['verify'] = False
    return _original_session_request(self, method, url, **kwargs)
requests.Session.request = _patched_session_request
# ==========================================

# NOW import the rest of your libraries
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import time
# ... (rest of your existing imports and code)

import os
import httpx
import pandas as pd

# --- MODERN LANGCHAIN IMPORTS (LCEL) ---
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- 1. Setup HTTP Client & API Key ---
client = httpx.Client(verify=False)
API_KEY = "sk-9jsr_wOuUgqNPt9JvdiMqQ" # ⚠️ REPLACE THIS WITH YOUR ACTUAL API KEY

# --- 2. Initialize LLM and Embeddings ---
llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key=API_KEY,
    http_client=client,
    temperature=0.3
)

embeddings = OpenAIEmbeddings(
    base_url="https://genailab.tcs.in",
    model="azure/genailab-maas-text-embedding-3-large",
    api_key=API_KEY,
    http_client=client
)

# --- 3. Prepare Data for RAG (Convert CSV to Text Chunks) ---
def prepare_rag_documents(metrics, logs, incidents):
    """Converts structured data into text documents for the Vector DB."""
    docs = []
    
    # 1. Convert Logs to text
    for _, row in logs.iterrows():
        docs.append(f"Log [{row['log_level']}] at {row['timestamp']}: {row['message']}")
        
    # 2. Convert Incidents to text
    for _, row in incidents.iterrows():
        docs.append(f"Incident {row['incident_id']} ({row['severity']}): {row['description']}. Resolution time: {row['resolution_time_min']} mins.")
        
    # 3. Convert Metric Anomalies to text (Only anomalies to save tokens)
    if 'is_anomaly' in metrics.columns:
        if metrics['is_anomaly'].dtype == 'object':
            metrics['is_anomaly'] = metrics['is_anomaly'].astype(str).str.lower() == 'true'
        anomaly_metrics = metrics[metrics['is_anomaly'] == True]
        
        for _, row in anomaly_metrics.iterrows():
            docs.append(f"Anomaly at {row['timestamp']} on {row['server_id']}: CPU={row['cpu_usage']}%, Mem={row['memory_usage']}%, Disk={row['disk_io']}%, Latency={row['network_latency']}ms")

    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_text("\n".join(docs))
    
    return chunks

# --- 4. Initialize Vector Store (ChromaDB) ---
def initialize_rag(metrics, logs, incidents):
    """Creates and returns the ChromaDB vector store."""
    chunks = prepare_rag_documents(metrics, logs, incidents)
    
    # Create vector store from texts
    vectorstore = Chroma.from_texts(
        texts=chunks, 
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    return vectorstore

# --- 5. Query the RAG System using LCEL (Modern LangChain) ---
def query_rag_system(vectorstore, user_question):
    """Retrieves relevant context and generates an answer using LCEL."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Custom Prompt for IT Maintenance
    template = """You are an expert AI IT Maintenance Co-Pilot. Use the following context retrieved from the legacy system logs and metrics to answer the user's question.
    If the context doesn't have the exact answer, use your general IT knowledge to provide a helpful troubleshooting step, but mention that the specific data wasn't found in the logs.

    Context:
    {context}

    Question: {question}

    Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Helper function to format retrieved documents into a single string
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    # Create RAG Chain using LCEL (LangChain Expression Language)
    # This is the modern, official way to build chains in LangChain!
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    response = rag_chain.invoke(user_question)
    return response