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
client = httpx.Client(verify=False, timeout=120.0)
API_KEY = "sk-9jsr_wOuUgqNPt9JvdiMqQ" # ️ REPLACE THIS WITH YOUR ACTUAL API KEY

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

# --- 3. Prepare Data for RAG (OPTIMIZED: Only Critical Data) ---
def prepare_rag_documents(metrics, logs, incidents):
    """Converts ONLY critical data into text documents to save time and tokens."""
    docs = []
    
    # 1. ONLY Convert CRITICAL and ERROR logs (Ignore INFO/WARNING to save 80% of time)
    critical_logs = logs[logs['log_level'].isin(['ERROR', 'CRITICAL'])]
    for _, row in critical_logs.iterrows():
        docs.append(f"Log [{row['log_level']}] at {row['timestamp']}: {row['message']}")
        
    # 2. Convert Incidents to text
    for _, row in incidents.iterrows():
        docs.append(f"Incident {row['incident_id']} ({row['severity']}): {row['description']}. Resolution time: {row['resolution_time_min']} mins.")
        
    # 3. ONLY Convert Metric Anomalies to text
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

# --- 5. Query the RAG System using LCEL ---
def query_rag_system(vectorstore, user_question):
    """Retrieves relevant context and generates an answer using LCEL."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    template = """You are an expert AI IT Maintenance Co-Pilot. Use the following context retrieved from the legacy system logs and metrics to answer the user's question.
    If the context doesn't have the exact answer, use your general IT knowledge to provide a helpful troubleshooting step.

    Context:
    {context}

    Question: {question}

    Answer:"""
    
    prompt = ChatPromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    response = rag_chain.invoke(user_question)
    return response