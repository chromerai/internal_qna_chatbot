# Setup Guide

Quick setup instructions for the Policy RAG System.

[← Back to README](README.md)

---

## Prerequisites

- Python 3.11+ (project uses: 3.12.12)
- Conda or pip
- Google Gemini API key
- 2GB free disk space

---

## Step 1: Clone Repository
```bash
git clone <repository-url>
```

---

## Step 2: Create Environment

### Using Conda (Recommended)
```bash
conda env create -f python_env.yml
conda activate policy_rag
```

### Using pip + venv
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## Step 3: Get API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app)
2. Click **"Get API Key"**
3. Create a project
4. Copy your API key

---

## Step 4: Configure Environment

Create `.env` file in project root:
```bash
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

Replace `your_api_key_here` with your actual API key.

**Security:** Never commit `.env` to version control!

---

## Step 5: Verify Installation
```bash
python -c "import langchain; import chromadb; print('Dependencies OK')"
```

---

## Step 6: Ingest Documents
```bash
python main.py --ingest
```

Expected output:
```
Initializing RAG Pipeline...
    Ingesting documents from: knowledge_base
Found 3 files
    Processing: policy_v1_2021.txt
    ...
Documents ingested successfully!
```

---

## Step 7: Test the System
```bash
# Single query
python main.py "Can I work from home?"

# Interactive mode
python main.py --interactive
```

---

## Quick Commands
```bash
#help
python main.py --help
# Ask a question
python main.py "your question here"

# Interactive mode
python main.py -i

# Full detailed output
python main.py "your question" --full

# Re-ingest documents
python main.py --ingest
```

---

## Troubleshooting

### API Key Error
```bash
# Verify .env file exists
cat .env

# Check key is loaded
python -c "from config import Config; print('Key:', Config().GEMINI_API_KEY[:10])"
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Vector Store Error
```bash
# Delete and recreate
rm -rf chroma_db
python main.py --ingest
```

### Rate Limit Error

- Wait 1-2 minutes
- Check [API quota](https://aistudio.google.com/app/api-keys)

---

## Configuration (Optional)

Edit `config.yaml` to customize:
```yaml
GEMINI_MODEL: "gemini-1.5-flash"     # or "gemini-1.5-pro"
TEMPERATURE_CONTENT: 0.3          # 0.0 = deterministic, 1.0 = creative
TOP_K: 3                          # Number of documents to retrieve
```

---

## Adding Documents
```bash
# 1. Add .txt file to knowledge_base/
cp <document>.txt knowledge_base/

# 2. Re-ingest
python main.py --ingest
```

**Naming Convention:**
- Policies: `policy_v{version}_{year}.txt`
- Menus: `{day}_cafeteria_menu.txt`
- Generic: `{description}_{date}.txt`

---

## Uninstall
```bash
# Remove environment
conda deactivate
conda env remove -n policy_rag

# Clean up
rm -rf chroma_db output_logs
```

---

## Next Steps

- Read [README.md](README.md) for detailed usage
- Check example outputs
- Customize `config.yaml`
- Add your own documents

---

[← Back to README](README.md)