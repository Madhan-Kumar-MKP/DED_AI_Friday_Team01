import os

print("🚀 Setting up Legacy Health Monitor Project...")

# 1. Define folders to create
folders = [
    "data",
    "utils"
]

# 2. Define files to create and their initial content
files = {
    "utils/__init__.py": "# Makes utils a Python package\n",
    "utils/data_generator.py": "# Logic to generate synthetic legacy logs/metrics\n",
    "utils/ai_engine.py": "# Agentic AI logic for anomaly detection and summarization\n",
    "app.py": "# Main Streamlit Dashboard\nimport streamlit as st\nst.title('Loading...')\n",
    "requirements.txt": """streamlit
langchain
langchain-openai
httpx
pandas
numpy
plotly
fpdf2
"""
}

# 3. Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"📁 Created folder: {folder}")

# 4. Create files
for file_path, content in files.items():
    # Create parent directories if they don't exist (just in case)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📄 Created file: {file_path}")

print("\n✅ Project structure created successfully!")
print("👉 Next step: Open your PyCharm terminal and run: pip install -r requirements.txt")