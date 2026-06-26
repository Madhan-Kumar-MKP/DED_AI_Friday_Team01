import pandas as pd
import numpy as np
import os
import random
from datetime import datetime, timedelta

# --- 1. Generate Performance Metrics ---
def generate_metrics(days=30, interval_minutes=15):
    print("Generating Performance Metrics...")
    timestamps = []
    server_ids = []
    cpu_usage = []
    memory_usage = []
    disk_io = []
    network_latency = []
    is_anomaly = []

    start_time = datetime.now() - timedelta(days=days)
    total_points = (days * 24 * 60) // interval_minutes
    servers = ["LEGACY-SRV-01", "LEGACY-SRV-02", "MAINFRAME-A", "DB-CLUSTER-03"]

    for i in range(total_points):
        ts = start_time + timedelta(minutes=i * interval_minutes)
        for srv in servers:
            timestamps.append(ts)
            server_ids.append(srv)
            
            # Normal baseline
            cpu = np.random.normal(45, 10)
            mem = np.random.normal(60, 8)
            disk = np.random.normal(30, 5)
            net = np.random.normal(20, 5)
            anomaly = False

            # Inject Anomalies randomly (approx 5% of data)
            if random.random() < 0.05:
                anomaly_type = random.choice(['cpu_spike', 'mem_leak', 'disk_saturation'])
                if anomaly_type == 'cpu_spike':
                    cpu = np.random.uniform(92, 100)
                elif anomaly_type == 'mem_leak':
                    mem = np.random.uniform(90, 99)
                elif anomaly_type == 'disk_saturation':
                    disk = np.random.uniform(95, 100)
                anomaly = True

            cpu_usage.append(max(0, min(100, cpu)))
            memory_usage.append(max(0, min(100, mem)))
            disk_io.append(max(0, min(100, disk)))
            network_latency.append(max(0, net))
            is_anomaly.append(anomaly)

    df_metrics = pd.DataFrame({
        'timestamp': timestamps,
        'server_id': server_ids,
        'cpu_usage': cpu_usage,
        'memory_usage': memory_usage,
        'disk_io': disk_io,
        'network_latency': network_latency,
        'is_anomaly': is_anomaly
    })
    return df_metrics

# --- 2. Generate System Logs ---
def generate_logs(days=30):
    print("Generating System Logs...")
    log_levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
    messages = {
        'INFO': ['Batch job completed successfully.', 'User login authenticated.', 'Routine backup finished.', 'Cache cleared.'],
        'WARNING': ['High memory threshold approaching.', 'Disk space below 20%.', 'Slow query detected in legacy DB.', 'Connection pool nearing limit.'],
        'ERROR': ['Failed to connect to mainframe.', 'Transaction rollback triggered.', 'API timeout after 30s.', 'File lock contention detected.'],
        'CRITICAL': ['System unresponsive. Manual intervention required.', 'Database cluster failover initiated.', 'Security breach attempt blocked.', 'Core dump generated.']
    }
    
    timestamps = []
    levels = []
    msgs = []
    servers = ["LEGACY-SRV-01", "LEGACY-SRV-02", "MAINFRAME-A", "DB-CLUSTER-03"]
    
    start_time = datetime.now() - timedelta(days=days)
    for _ in range(2000): # Generate 2000 log entries
        ts = start_time + timedelta(seconds=random.randint(0, days*86400))
        level = random.choices(log_levels, weights=[0.6, 0.2, 0.15, 0.05])[0]
        msg = random.choice(messages[level])
        
        timestamps.append(ts)
        levels.append(level)
        msgs.append(f"[{random.choice(servers)}] {msg}")

    df_logs = pd.DataFrame({
        'timestamp': timestamps,
        'log_level': levels,
        'message': msgs
    })
    return df_logs.sort_values('timestamp')

# --- 3. Generate Historical Incidents ---
def generate_incidents():
    print("Generating Historical Incidents...")
    incident_ids = [f"INC-{1000+i}" for i in range(50)]
    timestamps = [datetime.now() - timedelta(days=random.randint(1, 60)) for _ in range(50)]
    severities = random.choices(['Low', 'Medium', 'High', 'Critical'], weights=[0.4, 0.3, 0.2, 0.1], k=50)
    descriptions = [
        "Legacy ERP system froze during payroll processing.",
        "Mainframe batch job failed due to memory overflow.",
        "Network latency spiked causing API timeouts.",
        "Database deadlock detected in legacy CRM.",
        "Automated backup failed due to insufficient disk space."
    ]
    descs = [random.choice(descriptions) for _ in range(50)]
    resolutions = [random.randint(15, 480) for _ in range(50)] # Resolution time in minutes

    df_incidents = pd.DataFrame({
        'incident_id': incident_ids,
        'timestamp': timestamps,
        'severity': severities,
        'description': descs,
        'resolution_time_min': resolutions
    })
    return df_incidents

# --- Main Execution to Save Data ---
def generate_and_save_all():
    os.makedirs("data", exist_ok=True)
    
    df_metrics = generate_metrics()
    df_logs = generate_logs()
    df_incidents = generate_incidents()

    df_metrics.to_csv("data/metrics.csv", index=False)
    df_logs.to_csv("data/logs.csv", index=False)
    df_incidents.to_csv("data/incidents.csv", index=False)
    
    print("✅ Synthetic data saved to 'data/' folder.")

# --- Function to Load Data (Used by Streamlit later) ---
def load_data():
    if not os.path.exists("data/metrics.csv"):
        generate_and_save_all()
        
    metrics = pd.read_csv("data/metrics.csv", parse_dates=['timestamp'])
    logs = pd.read_csv("data/logs.csv", parse_dates=['timestamp'])
    incidents = pd.read_csv("data/incidents.csv", parse_dates=['timestamp'])
    
    return metrics, logs, incidents

if __name__ == "__main__":
    generate_and_save_all()