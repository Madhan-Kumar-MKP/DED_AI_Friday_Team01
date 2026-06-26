import os
import sys
import httpx
import pandas as pd
from langchain_openai import ChatOpenAI

# --- 1. Initialize HTTP Client & LLM (Added 120s Timeout) ---
# The timeout prevents the app from hanging indefinitely if the API is slow
client = httpx.Client(verify=False, timeout=120.0)

API_KEY = "sk-9jsr_wOuUgqNPt9JvdiMqQ" 

llm = ChatOpenAI(
    base_url="https://genailab.tcs.in",
    model="azure_ai/genailab-maas-DeepSeek-V3-0324",
    api_key=API_KEY,
    http_client=client,
    temperature=0.3
)

# --- 2. AI Analysis Function (OPTIMIZED FOR SPEED) ---
def analyze_system_health(metrics_df, logs_df, incidents_df):
    """
    Sends a highly compressed summary of data to the LLM for fast analysis.
    """
    # 1. Metrics: Only send anomalies and aggregate stats to save tokens
    if 'is_anomaly' in metrics_df.columns:
        if metrics_df['is_anomaly'].dtype == 'object':
            metrics_df['is_anomaly'] = metrics_df['is_anomaly'].astype(str).str.lower() == 'true'
        
        # Only take the top 15 anomalies instead of 100 raw rows
        anomalies = metrics_df[metrics_df['is_anomaly'] == True].tail(15)
        metrics_summary = anomalies.to_csv(index=False) if not anomalies.empty else "No anomalies detected."
        
        # Add quick aggregate stats
        stats = f"Total Records: {len(metrics_df)}, Avg CPU: {metrics_df['cpu_usage'].mean():.1f}%, Max Memory: {metrics_df['memory_usage'].max():.1f}%"
    else:
        metrics_summary = "No anomaly data available."
        stats = "No metrics available."

    # 2. Logs: Only send the most recent critical/error logs (Top 15)
    error_logs = logs_df[logs_df['log_level'].isin(['ERROR', 'CRITICAL'])].tail(15)
    logs_summary = error_logs.to_csv(index=False) if not error_logs.empty else "No recent critical or error logs."
        
    # 3. Incidents: Only send the last 5
    recent_incidents = incidents_df.tail(5).to_csv(index=False)

    # 4. Construct the Prompt (Much smaller and focused)
    prompt = f"""
    You are an expert AI IT Application Maintenance Engineer.
    Analyze the following compressed data from a legacy system and provide a structured report:
    1. Overall Health Score (0-100) with brief justification.
    2. Detected Anomalies (Identify specific metrics).
    3. Log Analysis (Summarize critical/error logs).
    4. Top 3 Prioritized Maintenance Actions.

    ### SYSTEM STATS ###
    {stats}

    ### RECENT ANOMALIES (CSV) ###
    {metrics_summary}

    ### RECENT ERROR/CRITICAL LOGS (CSV) ###
    {logs_summary}

    ### RECENT INCIDENTS (CSV) ###
    {recent_incidents}

    Provide the response in a clear, professional format with bold headings.
    """

    # 5. Invoke LLM
    response = llm.invoke(prompt)
    return response.content

# --- 3. Test the AI Engine ---
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_generator import load_data
    
    print("🤖 Testing AI Engine...")
    try:
        metrics, logs, incidents = load_data()
        result = analyze_system_health(metrics, logs, incidents)
        print("\n✅ AI ANALYSIS RESULT:\n")
        print(result)
    except Exception as e:
        print(f"\n❌ Error: {e}")