import pandas as pd
import numpy as np

def process_data(metrics, logs, incidents):
    """Applies Pre-processing, Noise Filtering, and Normalization."""
    print("🔄 Running Data Pipeline...")
    
    # 1. Pre-processing
    metrics = metrics.dropna()
    logs = logs.dropna()
    incidents = incidents.dropna()
    metrics['timestamp'] = pd.to_datetime(metrics['timestamp'])
    logs['timestamp'] = pd.to_datetime(logs['timestamp'])
    incidents['timestamp'] = pd.to_datetime(incidents['timestamp'])
    
    # 2. Noise Filtering (Rolling Average)
    metrics['cpu_usage_filtered'] = metrics['cpu_usage'].rolling(window=3, min_periods=1).mean()
    metrics['memory_usage_filtered'] = metrics['memory_usage'].rolling(window=3, min_periods=1).mean()
    logs = logs[logs['message'].str.len() > 5] 

    # 3. Normalization (Min-Max Scaling)
    min_lat = metrics['network_latency'].min()
    max_lat = metrics['network_latency'].max()
    if max_lat - min_lat != 0:
        metrics['network_latency_normalized'] = (metrics['network_latency'] - min_lat) / (max_lat - min_lat)
    else:
        metrics['network_latency_normalized'] = 0.0
        
    print("✅ Data Pipeline Complete.")
    return metrics, logs, incidents

def anonymize_data(metrics, logs, incidents):
    """Masks sensitive server identifiers for privacy compliance (GDPR/CCPA style)."""
    print(" Applying Privacy & Security Masking...")
    
    # Mask Server IDs in metrics
    metrics['server_id'] = metrics['server_id'].apply(
        lambda x: x.replace('LEGACY', 'SRV-***').replace('MAINFRAME', 'MAIN-***').replace('DB-CLUSTER', 'DB-***')
    )
    
    # Mask Server IDs inside log messages
    logs['message'] = logs['message'].apply(
        lambda x: x.replace('LEGACY-SRV', 'SRV-***').replace('MAINFRAME-A', 'MAIN-***').replace('DB-CLUSTER', 'DB-***')
    )
    
    print("✅ Data Anonymized.")
    return metrics, logs, incidents