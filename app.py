import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add project root to sys.path to allow imports from utils
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- Page Config ---
st.set_page_config(page_title="Legacy System Health Monitor", layout="wide", page_icon="🖥️")

# --- Custom CSS for a more "Enterprise" look ---
st.markdown("""
<style>
    .reportview-container .main .block-container { padding-top: 2rem; }
    div[data-testid="stMetricValue"] { font-size: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- Load Data (with error handling) ---
@st.cache_data
def get_data():
    try:
        from utils.data_generator import load_data
        metrics, logs, incidents = load_data()
        return metrics, logs, incidents
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

metrics, logs, incidents = get_data()

# --- Sidebar Navigation ---
st.sidebar.title("️ Legacy Health Monitor")
st.sidebar.markdown("---")
st.sidebar.info("Powered by TCS GenAI Lab\nModel: DeepSeek-V3-0324")
page = st.sidebar.radio("Navigate to:", ["📊 Dashboard", "🤖 AI Insights", "📁 Data Explorer"])

# ==========================================
# PAGE 1: DASHBOARD
# ==========================================
if page == "📊 Dashboard":
    st.title("📊 System Health Dashboard")
    
    if metrics.empty:
        st.warning("⚠️ No data available. Please generate data first.")
        st.stop()
    
    # --- KPI Cards ---
    col1, col2, col3 = st.columns(3)
    
    if 'is_anomaly' in metrics.columns:
        if metrics['is_anomaly'].dtype == 'object':
            metrics['is_anomaly'] = metrics['is_anomaly'].astype(str).str.lower() == 'true'
        recent_anomalies = metrics[metrics['is_anomaly'] == True].shape[0]
    else:
        recent_anomalies = 0
        
    health_score = max(0, 100 - (recent_anomalies * 0.5))
    
    with col1:
        st.metric(label="Overall Health Score", value=f"{health_score:.1f}/100", delta="-2.5%")
    with col2:
        critical_logs = logs[logs['log_level'] == 'CRITICAL'].shape[0] if not logs.empty else 0
        st.metric(label="Critical Alerts", value=critical_logs, delta="+2", delta_color="inverse")
    with col3:
        high_incidents = incidents[incidents['severity'] == 'High'].shape[0] if not incidents.empty else 0
        st.metric(label="High Priority Incidents", value=high_incidents)

    st.markdown("---")

    # --- Charts ---
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.subheader("📈 CPU & Memory Usage Over Time")
        time_series = metrics.groupby('timestamp')[['cpu_usage', 'memory_usage']].mean().reset_index()
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=time_series['timestamp'], y=time_series['cpu_usage'], mode='lines', name='CPU Usage', line=dict(color='red')))
        fig1.add_trace(go.Scatter(x=time_series['timestamp'], y=time_series['memory_usage'], mode='lines', name='Memory Usage', line=dict(color='blue')))
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

# ==========================================
# PAGE 2: AI INSIGHTS
# ==========================================
elif page == "🤖 AI Insights":
    st.title("🤖 AI-Driven System Analysis")
    st.markdown("Click the button below to let our AI Engineer analyze the current system state, detect anomalies, and suggest maintenance priorities.")
    
    if metrics.empty:
        st.warning("⚠️ No data available. Please generate data first.")
        st.stop()
    
    # Session state to hold the AI analysis so we can export it later
    if 'ai_analysis' not in st.session_state:
        st.session_state.ai_analysis = ""

    if st.button(" Run AI Analysis", type="primary", use_container_width=True):
        with st.spinner("🧠 AI is analyzing metrics, logs, and incidents..."):
            try:
                from utils.ai_engine import analyze_system_health
                st.session_state.ai_analysis = analyze_system_health(metrics, logs, incidents)
                st.success("✅ Analysis Complete!")
            except Exception as e:
                st.error(f"❌ Error generating AI insights: {e}")

    # Display the analysis if it exists
    if st.session_state.ai_analysis:
        st.markdown("---")
        st.subheader("📋 AI Report Output")
        st.markdown(st.session_state.ai_analysis)
        
        st.markdown("---")
        st.subheader("📥 Export Report")
        
        # Generate and download PDF
        try:
            from utils.report_generator import generate_pdf_report
            pdf_path = generate_pdf_report(metrics, logs, incidents, st.session_state.ai_analysis)
            
            with open(pdf_path, "rb") as file:
                st.download_button(
                    label=" Download Maintenance Report (PDF)",
                    data=file,
                    file_name="Legacy_System_Health_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        except Exception as e:
            st.error(f"Could not generate PDF: {e}")

# ==========================================
# PAGE 3: DATA EXPLORER
# ==========================================
elif page == "📁 Data Explorer":
    st.title("📁 Data Explorer")
    
    if metrics.empty:
        st.warning("⚠️ No data available.")
        st.stop()
    
    tab1, tab2, tab3 = st.tabs(["Performance Metrics", "System Logs", "Historical Incidents"])
    
    with tab1:
        st.subheader("Performance Metrics (Raw Data)")
        st.write(f"Total Records: {len(metrics)}")
        st.dataframe(metrics.tail(100), use_container_width=True)
    with tab2:
        st.subheader("System Logs (Raw Data)")
        st.write(f"Total Records: {len(logs)}")
        st.dataframe(logs.tail(100), use_container_width=True)
    with tab3:
        st.subheader("Historical Incidents (Raw Data)")
        st.write(f"Total Records: {len(incidents)}")
        st.dataframe(incidents, use_container_width=True)