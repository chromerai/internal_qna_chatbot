# Policy RAG System 🤖

A Retrieval-Augmented Generation (RAG) system for querying company policies and documents using Google's Gemini API with structured output generation.

## 📋 Table of Contents

- [Overview](#overview)
- [Model Choice: Why Gemini?](#model-choice-why-gemini)
- [Features](#features)
- [Quick Setup](#quick-setup)
- [Usage](#usage)
- [Example Outputs](#example-outputs)
- [Limitations](#limitations)
- [Technical Architecture](#technical-architecture)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## 🎯 Overview

This RAG system enables natural language queries over company policy documents, cafeteria menus, and other organizational knowledge. It uses vector similarity search combined with Large Language Model (LLM) generation to provide accurate, source-cited answers.

**Key Capabilities:**
- 📄 Document ingestion with automatic metadata extraction
- 🔍 Semantic search using ChromaDB vector store
- 🎯 Structured output with Pydantic models
- 📚 Source citation and reasoning transparency
- 🔄 Version-aware policy retrieval

## 🚀 Model Choice: Why Gemini?

This project uses **Google Gemini API** (`gemini-2.5-flash`) as the LLM backbone for several strategic reasons:

### 1. **Structured Output Generation** ⭐
Gemini provides native support for JSON schema-based output through `response_json_schema`, enabling precise control over response format:
```python
config = {
    "response_mime_type": "application/json",
    "response_json_schema": PolicyAnswer.model_json_schema(),
    "temperature": 0.3
}
```

This ensures every response conforms to our Pydantic `PolicyAnswer` model with fields like:
- `answer`: The actual response
- `reasoning`: Chain-of-thought explanation
- `cited_sources`: Document references
- `policy_allows_remote`: Boolean policy decisions

### 2. **Cost-Effectiveness for Students** 💰
- Generous free tier with substantial credits for new students
- Significantly more credits for students compared to OpenAI
- Lower per-token pricing for experimentation and development

### 3. **Performance & Quality** ⚡
- Fast response times with `gemini-2.5-flash`
- Strong reasoning capabilities for policy interpretation
- Excellent at following system instructions

### 4. **Ease of Integration** 🛠️
- Simple API with straightforward authentication
- Excellent documentation and examples
- Seamless integration with LangChain

## ✨ Features

- ✅ **Automatic Document Processing**: Extracts metadata (type, version, date) from filenames
- ✅ **Vector Search**: Semantic similarity using ChromaDB + Google Embeddings
- ✅ **Structured Responses**: Guaranteed JSON output format with Pydantic validation
- ✅ **Source Attribution**: Every answer cites specific documents
- ✅ **Version Awareness**: Automatically uses most recent policy versions
- ✅ **CLI Interface**: Interactive and single-query modes
- ✅ **Configurable Output**: Compact or detailed response formats

## 🚀 Quick Setup

See **[SETUP.md](SETUP.md)** for detailed installation instructions.

**TL;DR:**
```bash
# 1. Clone repository
git clone <your-repo-url>
cd policy-rag-system

# 2. Create conda environment
conda env create -f environment.yml
conda activate policy_rag

# 3. Set up API key
echo "GOOGLE_API_KEY=your_api_key_here" > .env

# 4. Ingest documents
python main.py --ingest

# 5. Ask questions!
python main.py "Can I work from home?"
```

## 💬 Usage

### Single Query Mode
```bash
# Ask a question (compact output - default)
python main.py "Can I work from home?"

# Full detailed output
python main.py "What's on the cafeteria menu?" --full
```

### Interactive Mode
```bash
# Start interactive session
python main.py --interactive

# Interactive with full details
python main.py -i --full
```

### Document Management
```bash
# Ingest/re-ingest all documents
python main.py --ingest
```

### Command Reference
```
Options:
  -h, --help            Show help message
  -q, --question TEXT   Question to ask
  -i, --interactive     Interactive mode
  --ingest              Ingest documents
  -f, --full           Show full detailed output
```

## 📸 Example Outputs

### Query 1: Remote Work Policy
**Question:** "Can I work from home?"

**Output (Compact):**
```
----------------------------------------------------------------------
💡 Answer: Yes, according to the latest remote work policy (v2, 2024), 
employees can work remotely up to 3 days per week with manager approval.
📚 Sources: policy_v2_2024.txt
----------------------------------------------------------------------
```

**Output (Full):**
```
======================================================================
   QUESTION:
======================================================================

Can I work from home?

======================================================================
   ANSWER:
======================================================================

Yes, according to the latest remote work policy (v2, 2024), employees 
can work remotely up to 3 days per week with manager approval.

----------------------------------------------------------------------
   DETAILS:
----------------------------------------------------------------------
Reasoning: The query asks about remote work eligibility. I retrieved 
the most recent policy version (v2 from 2024) which supersedes the 
older v1 policy from 2021. The current policy allows remote work with 
specific conditions.
Sources: policy_v2_2024.txt
Policy allows remote: True
======================================================================
```

### Query 2: Cafeteria Menu
**Question:** "What's available in the cafeteria on Friday?"

**Output:**
```
----------------------------------------------------------------------
💡 Answer: The Friday cafeteria menu includes: Veg Biryani, Paneer 
Tikka Masala, Dal Tadka, Salad Bar, and Gulab Jamun for dessert.
📚 Sources: friday_cafeteria_menu.txt
----------------------------------------------------------------------
```

*[Screenshots will be added here after testing]*

## ⚠️ Limitations

### Current Limitations
1. **Document Format**: Only supports `.txt` files (no PDF, DOCX, etc.)
2. **No Deletion Handling**: Deleting documents requires full re-ingestion (`--ingest`)
3. **Single Language**: Optimized for English content only
4. **Fixed Chunk Size**: 500-character chunks may not be optimal for all document types
5. **No Authentication**: CLI-only, no user management or access control
6. **Local Storage**: Vector store stored locally, not suitable for multi-user scenarios

### Performance Considerations
- **Cold Start**: First query after ingestion may be slower
- **API Rate Limits**: Subject to Google Gemini API quotas
- **Vector Search**: Performance degrades with >10,000 documents (requires optimization)

### Known Issues
- Empty responses if no relevant documents found (no fallback behavior)
- Metadata extraction relies on filename patterns (e.g., `policy_v2_2024.txt`)
- ChromaDB persistence directory must be writable

## 🏗️ Technical Architecture

### Component Overview
flowchart TD
    A[main.py<br/>CLI Interface] --> B[rag_engine.py<br/>Orchestration Layer]
    B --> C[ChromaDB<br/>Vector Store]
    B --> D[ingestion_pipeline<br/>Document Processing]
    C --> E[Gemini API<br/>LLM + Embed]
    D --> E
    
    style A fill:#1a73e8,stroke:#000,stroke-width:3px,color:#fff,font-weight:bold
    style B fill:#fbbc04,stroke:#000,stroke-width:3px,color:#000,font-weight:bold
    style C fill:#9334e6,stroke:#000,stroke-width:3px,color:#fff,font-weight:bold
    style D fill:#9334e6,stroke:#000,stroke-width:3px,color:#fff,font-weight:bold
    style E fill:#34a853,stroke:#000,stroke-width:3px,color:#fff,font-weight:bold
    
    linkStyle default stroke:#333,stroke-width:3px
### Data Flow

1. **Ingestion Phase**:
```
   .txt files → Metadata Extraction → Chunking → Embedding → ChromaDB
```

2. **Query Phase**:
```
   User Query → Embedding → Vector Search → Context Retrieval → 
   LLM Generation (with JSON schema) → Pydantic Validation → Response
```

### Key Technologies
- **LangChain**: RAG orchestration framework
- **ChromaDB**: Vector database for semantic search
- **Google Gemini**: LLM for generation + embeddings
- **Pydantic**: Data validation and structured outputs
- **PyYAML**: Configuration management

## ⚙️ Configuration

Key settings in `config.yaml`:
```yaml
paths:
  knowledge_base: "knowledge_base"
  chroma_persist_dir: "./chroma_db"
  collection_name: "techcorp_docs"

active_provider: "gemini"

# Model Configurations
models:
  gemini:
    embedding_model: "gemini-embedding-001"
    llm_model: "gemini-2.5-flash"
    embedding_dimension: 768
    task_type: "retrieval-document"
    temperature_intent: 0
    temperature_content: 0.5
    max_tokens: 1024

retrieval:
  top_k: 5
  similarity_search_k: 10
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- [ ] PDF/DOCX document support
- [ ] Multi-language support
- [ ] Web UI interface
- [ ] Advanced caching mechanisms
- [ ] Document update detection without full re-ingestion
- [ ] Conversation history/memory

## 📄 License

MIT License - feel free to use for educational and commercial purposes.

---

**Questions or Issues?** Open an issue on GitHub or contact the maintainer.

**Built with ❤️ using Google Gemini API**