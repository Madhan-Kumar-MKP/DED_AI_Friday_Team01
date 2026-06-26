import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="Legacy System Health Monitor", layout="wide", page_icon="🖥️")

# --- 1. Load RAW Data (Cached for performance) ---
@st.cache_data
def get_raw_data():
    from utils.data_generator import load_data
    return load_data()

# --- 2. Sidebar Settings ---
st.sidebar.title("🖥️ Legacy Health Monitor")
st.sidebar.markdown("---")
st.sidebar.info("Powered by TCS GenAI Lab\nModel: DeepSeek-V3-0324")

st.sidebar.markdown("### ⚙️ System Settings")
live_mode = st.sidebar.checkbox("Enable Live Monitoring (Auto-refresh)", value=False)
privacy_mode = st.sidebar.checkbox("🔒 Enable Privacy Mode (Anonymize Data)", value=False)

if privacy_mode:
    st.sidebar.warning("🔒 Sensitive server IDs are masked.")

page = st.sidebar.radio("Navigate to:", ["📊 Dashboard", "🤖 AI Insights & Co-Pilot", "📁 Data Explorer"])

# --- 3. Process Data (Runs fresh, no caching bugs) ---
try:
    raw_metrics, raw_logs, raw_incidents = get_raw_data()
    from utils.data_pipeline import process_data, anonymize_data
    
    # Apply Preprocessing, Noise Filtering, Normalization
    metrics, logs, incidents = process_data(raw_metrics, raw_logs, raw_incidents)
    
    # Apply Privacy Masking if enabled
    if privacy_mode:
        metrics, logs, incidents = anonymize_data(metrics, logs, incidents)
except Exception as e:
    st.error(f"❌ Critical Pipeline Error: {e}")
    st.stop()

# ==========================================
# PAGE 1: DASHBOARD
# ==========================================
if page == "📊 Dashboard":
    st.title("📊 System Health Dashboard")
    
    if metrics.empty:
        st.warning("⚠️ No data available.")
        st.stop()
    
    # KPI Calculation
    if 'is_anomaly' in metrics.columns:
        if metrics['is_anomaly'].dtype == 'object':
            metrics['is_anomaly'] = metrics['is_anomaly'].astype(str).str.lower() == 'true'
        recent_anomalies = metrics[metrics['is_anomaly'] == True].shape[0]
    else:
        recent_anomalies = 0
        
    total_records = len(metrics)
    anomaly_pct = (recent_anomalies / total_records) * 100 if total_records > 0 else 0
    health_score = max(0, 100 - (anomaly_pct * 2)) # Realistic percentage-based score
    
    critical_logs = logs[logs['log_level'] == 'CRITICAL'].shape[0] if not logs.empty else 0
    high_incidents = incidents[incidents['severity'] == 'High'].shape[0] if not incidents.empty else 0

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Overall Health Score", value=f"{health_score:.1f}/100", delta="-2.5%")
    with col2:
        st.metric(label="Critical Alerts", value=critical_logs, delta="+2", delta_color="inverse")
    with col3:
        st.metric(label="High Priority Incidents", value=high_incidents)

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.subheader("📈 CPU & Memory Usage (Noise Filtered)")
        st.caption("✨ Showing smoothed data after noise filtering pipeline")
        time_series = metrics.groupby('timestamp')[['cpu_usage_filtered', 'memory_usage_filtered']].mean().reset_index()
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=time_series['timestamp'], y=time_series['cpu_usage_filtered'], mode='lines', name='CPU (Filtered)', line=dict(color='red')))
        fig1.add_trace(go.Scatter(x=time_series['timestamp'], y=time_series['memory_usage_filtered'], mode='lines', name='Memory (Filtered)', line=dict(color='blue')))
        fig1.update_layout(xaxis_title="Time", yaxis_title="Percentage (%)", hovermode='x unified')
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col2:
        st.subheader("📊 Log Severity Distribution")
        if not logs.empty and 'log_level' in logs.columns:
            log_counts = logs['log_level'].value_counts().reset_index()
            log_counts.columns = ['Level', 'Count']
            fig2 = px.pie(log_counts, values='Count', names='Level', 
                          color_discrete_map={'INFO':'#2ecc71', 'WARNING':'#f1c40f', 'ERROR':'#e67e22', 'CRITICAL':'#e74c3c'})
            st.plotly_chart(fig2, use_container_width=True)

    # Live Refresh Logic
    if live_mode:
        countdown_placeholder = st.sidebar.empty()
        for i in range(10, 0, -1):
            countdown_placeholder.info(f"⏳ Next data refresh in {i}s...")
            time.sleep(1)
        st.rerun()

# ==========================================
# PAGE 2: AI INSIGHTS & CO-PILOT
# ==========================================
elif page == "🤖 AI Insights & Co-Pilot":
    st.title("🤖 AI-Driven System Analysis & Co-Pilot")
    
    if metrics.empty:
        st.warning("⚠️ No data available.")
        st.stop()
    
    if 'ai_analysis' not in st.session_state:
        st.session_state.ai_analysis = ""
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # --- 1. Generate Main Report Button ---
    if st.button("🚀 Run AI System Analysis", type="primary", use_container_width=True):
        with st.spinner("🧠 AI is analyzing metrics, logs, and incidents..."):
            try:
                from utils.ai_engine import analyze_system_health
                st.session_state.ai_analysis = analyze_system_health(metrics, logs, incidents)
                st.success("✅ Analysis Complete!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

    # --- 2. Display Report if Available ---
    if st.session_state.ai_analysis:
        st.markdown("---")
        # Display the AI text directly without an extra subheader to keep it clean
        st.markdown(st.session_state.ai_analysis) 
        
        # Export PDF
        st.markdown("---")
        if st.button("📄 Generate PDF Report", use_container_width=True):
            with st.spinner("Generating PDF..."):
                try:
                    from utils.report_generator import generate_pdf_report
                    pdf_path = generate_pdf_report(metrics, logs, incidents, st.session_state.ai_analysis)
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_file,
                            file_name="Legacy_System_Health_Report.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                except Exception as e:
                    st.error(f"PDF Error: {e}")

    # --- 3. INTERACTIVE AI CHAT CO-PILOT ---
    st.markdown("---")
    st.subheader("💬 Interactive AI Co-Pilot")
    st.caption("Ask questions about your infrastructure. Examples: *'Why did MAINFRAME-A spike?'* or *'What caused the API timeouts?'*")
    
    # Display chat history
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Chat input
    if prompt := st.chat_input("Ask about system health, logs, or anomalies..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("🔍 Investigating system data..."):
                try:
                    from utils.ai_engine import chat_with_data
                    response = chat_with_data(prompt, metrics, logs, incidents, st.session_state.ai_analysis)
                    st.markdown(response)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"Chat error: {e}")

# ==========================================
# PAGE 3: DATA EXPLORER
# ==========================================
elif page == "📁 Data Explorer":
    st.title("📁 Data Explorer")
    
    if privacy_mode:
        st.info("🔒 Privacy Mode is ACTIVE. Sensitive server identifiers are masked.")
    
    if metrics.empty:
        st.warning("⚠️ No data available.")
        st.stop()
    
    tab1, tab2, tab3 = st.tabs(["Performance Metrics", "System Logs", "Historical Incidents"])
    
    with tab1:
        st.subheader("Performance Metrics (Normalized & Filtered)")
        st.dataframe(metrics.tail(100), use_container_width=True)
    with tab2:
        st.subheader("System Logs")
        st.dataframe(logs.tail(100), use_container_width=True)
    with tab3:
        st.subheader("Historical Incidents")
        st.dataframe(incidents, use_container_width=True)