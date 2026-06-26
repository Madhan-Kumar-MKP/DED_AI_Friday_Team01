import os
import re
import tempfile
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

# ----------------------------
# AI text cleaner (Strips emojis & non-ASCII for FPDF safety)
# ----------------------------
def clean_text(text):
    text = re.sub(r'#+\s*', '', text)
    text = re.sub(r'---+', '', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Strip out any emojis or non-ASCII characters that FPDF can't render
    text = re.sub(r'[^\x00-\x7F]+', '', text) 
    return text

# ----------------------------
# Chart Generator (Plotly)
# ----------------------------
def generate_health_chart(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "System Health Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "green" if score > 70 else "orange" if score > 40 else "red"},
            'steps': [
                {'range': [0, 40], 'color': "lightcoral"},
                {'range': [40, 70], 'color': "khaki"},
                {'range': [70, 100], 'color': "lightgreen"},
            ]
        }
    ))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.write_image(tmp.name)
    return tmp.name

def generate_trend_chart(metrics):
    if metrics is None or metrics.empty:
        return None

    fig = go.Figure()
    x_col = "timestamp"
    y_col = "cpu_usage_filtered" if "cpu_usage_filtered" in metrics.columns else "cpu_usage"
    
    if x_col in metrics.columns and y_col in metrics.columns:
        agg_metrics = metrics.groupby(x_col)[y_col].mean().reset_index()
        fig.add_trace(go.Scatter(
            x=agg_metrics[x_col],
            y=agg_metrics[y_col],
            mode="lines",
            name="CPU Usage Trend",
            line=dict(color="#2980b9", width=2)
        ))
        fig.update_layout(
            title="System Metric Trend",
            xaxis_title="Time",
            yaxis_title="Value",
            margin=dict(t=40, b=40, l=40, r=20)
        )

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.write_image(tmp.name)
    return tmp.name

# ----------------------------
# KPI Risk Model
# ----------------------------
def compute_risk(score):
    if score >= 80:
        return "LOW", (46, 204, 113)
    elif score >= 60:
        return "MEDIUM", (241, 196, 15)
    elif score >= 40:
        return "HIGH", (230, 126, 34)
    else:
        return "CRITICAL", (231, 76, 60)

# ----------------------------
# PDF Generator
# ----------------------------
def generate_pdf_report(metrics, logs, incidents, ai_analysis_text):

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # =========================
    # DATA CALCULATIONS
    # =========================
    total_records = len(metrics) if metrics is not None and not metrics.empty else 0

    critical_logs = logs[logs["log_level"] == "CRITICAL"].shape[0] if logs is not None and not logs.empty else 0
    high_incidents = incidents[incidents["severity"] == "High"].shape[0] if incidents is not None and not incidents.empty else 0

    recent_anomalies = 0
    if metrics is not None and not metrics.empty and "is_anomaly" in metrics.columns:
        metrics["is_anomaly"] = metrics["is_anomaly"].astype(str).str.lower() == "true"
        recent_anomalies = metrics[metrics["is_anomaly"]].shape[0]

    anomaly_pct = (recent_anomalies / total_records) * 100 if total_records else 0
    health_score = max(0, 100 - anomaly_pct * 2)

    risk, risk_color = compute_risk(health_score)

    # Generate Charts
    health_chart = generate_health_chart(health_score)
    trend_chart = generate_trend_chart(metrics)

    # =========================
    # PAGE 1 - DASHBOARD
    # =========================
    pdf.add_page()

    # Header
    pdf.set_fill_color(20, 40, 80)
    pdf.rect(0, 0, 210, 30, "F")
    
    pdf.set_x(10) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 15, "ENTERPRISE SYSTEM HEALTH DASHBOARD", ln=True, align="C")

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 5, "AI Observability & Infrastructure Intelligence Report", ln=True, align="C")

    pdf.ln(10)

    # Health Score Chart
    if health_chart:
        pdf.image(health_chart, x=45, w=120)
        pdf.set_x(10) 

    pdf.ln(10)

    # Risk Badge
    pdf.set_fill_color(*risk_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, f"System Risk Level: {risk}", ln=True, align="C", fill=True)

    pdf.ln(8)

    # KPI GRID
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 11)

    def kpi(x, y, title, value, color):
        pdf.set_fill_color(*color)
        pdf.rect(x, y, 50, 25, "F")
        pdf.set_xy(x, y + 8)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(50, 5, title, align="C")
        pdf.set_xy(x, y + 15)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(50, 5, str(value), align="C")
        pdf.set_font("Helvetica", "B", 11)

    kpi(10, 120, "Critical Logs", critical_logs, (192, 57, 43))
    kpi(70, 120, "High Incidents", high_incidents, (230, 126, 34))
    kpi(130, 120, "Anomalies", recent_anomalies, (52, 152, 219))

    # =========================
    # PAGE 2 - EXEC SUMMARY
    # =========================
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(20, 40, 80)
    pdf.cell(0, 10, "Executive Summary", ln=True)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)

    summary = f"""
System processed {total_records} telemetry records.

Detected:
- {critical_logs} critical logs
- {high_incidents} high severity incidents
- {recent_anomalies} anomalies

Overall system posture is {risk} with health score {health_score:.1f}/100.
"""
    pdf.set_x(10)
    pdf.multi_cell(0, 6, summary)

    # Trend Chart
    if trend_chart:
        pdf.ln(5)
        pdf.set_x(10) 
        pdf.image(trend_chart, w=180)

    # =========================
    # PAGE 3 - AI INSIGHTS
    # =========================
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, "AI Observability Insights", ln=True)

    pdf.set_text_color(60, 60, 60)
    pdf.set_font("Helvetica", "", 10)

    text = clean_text(ai_analysis_text)

    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        pdf.set_x(10) 
        if line.startswith("-"):
            pdf.cell(5)
            # FIX: Replaced "✔" with standard hyphen "-" to prevent FPDF font errors
            pdf.multi_cell(0, 6, f"- {line[1:].strip()}")
        else:
            pdf.multi_cell(0, 6, line)

    # =========================
    # FOOTER
    # =========================
    pdf.set_y(-15)
    pdf.set_x(10) 
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 10, "Generated by AI Observability Platform | Enterprise Report v1.0", align="C")

    # =========================
    # SAVE
    # =========================
    os.makedirs("data", exist_ok=True)
    output = "data/Enterprise_System_Health_Report.pdf"
    pdf.output(output)

    return output