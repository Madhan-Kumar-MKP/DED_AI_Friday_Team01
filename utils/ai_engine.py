# Agentic AI logic for anomaly detection and summarization
import os
import sys
import httpx
import pandas as pd
from langchain_openai import ChatOpenAI

# --- 1. Initialize HTTP Client & LLM ---
client = httpx.Client(verify=False)

API_KEY = "sk-9jsr_wOuUgqNPt9JvdiMqQ" 

llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key=API_KEY,
    http_client=client,
    temperature=0.3 # Lower temperature for more factual/analytical responses
)

# --- 2. AI Analysis Function ---
def analyze_system_health(metrics_df, logs_df, incidents_df):
    """
    Sends structured data to the LLM to generate a health summary, 
    anomaly detection, and maintenance priorities.
    """
    # 1. Get the latest metrics (last 100 rows to stay within token limits)
    recent_metrics = metrics_df.tail(100).to_csv(index=False)
    
    # 2. Filter for recent critical/error logs
    error_logs = logs_df[logs_df['log_level'].isin(['ERROR', 'CRITICAL'])].tail(50)
    if error_logs.empty:
        recent_logs = "No recent critical or error logs found. System is stable."
    else:
        recent_logs = error_logs.to_csv(index=False)
        
    # 3. Get recent historical incidents for context
    recent_incidents = incidents_df.tail(10).to_csv(index=False)

    # 4. Construct the Prompt
    prompt = f"""
    You are an expert AI IT Application Maintenance Engineer monitoring a legacy system.
    Analyze the following data and provide a structured report covering:
    1. **Overall Health Score** (0-100) with a brief justification.
    2. **Detected Anomalies** (Identify specific metrics that look abnormal, e.g., CPU spikes, memory leaks).
    3. **Log Analysis** (Summarize the critical/error logs and what they indicate).
    4. **Prioritized Maintenance Actions** (Top 3 actionable recommendations based on the current state and past incidents).

    ### RECENT METRICS (CSV) ###
    {recent_metrics}

    ### RECENT ERROR/CRITICAL LOGS (CSV) ###
    {recent_logs}

    ### RECENT INCIDENTS (CSV) ###
    {recent_incidents}

    Provide the response in a clear, professional format with bold headings, suitable for an IT maintenance dashboard.
    """

    # 5. Invoke LLM
    response = llm.invoke(prompt)
    return response.content

# --- 3. Test the AI Engine ---
if __name__ == "__main__":
    # Add parent directory to path so we can import from utils
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_generator import load_data
    
    print("🤖 Testing AI Engine connection and analysis...")    
    try:
        metrics, logs, incidents = load_data()
        result = analyze_system_health(metrics, logs, incidents)
        
        print("\n" + "="*50)
        print("✅ AI ANALYSIS RESULT:")
        print("="*50 + "\n")
        print(result)
    except Exception as e:
        print(f"\n❌ Error connecting to AI: {e}")
        print("Please check your API key and internet connection.")