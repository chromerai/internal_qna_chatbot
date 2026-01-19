"""
Configuration Module for RAG System
Loads settings from config.yaml and API keys from .env file
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """
    Central configuration for RAG system.
    Loads from config.yaml and environment variables.
    """
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration by loading from YAML file.
        
        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = config_path
        self._load_config()
        self._load_env()
    
    def _load_config(self):
        """Load configuration from YAML file."""
        config_file = Path(self.config_path)
        
        if not config_file.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                "Please create config.yaml in the project root."
            )
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Paths
        paths = config_data.get('paths', {})
        self.KNOWLEDGE_BASE_PATH = paths.get('knowledge_base', 'knowledge_base')
        self.CHROMA_PERSIST_DIR = paths.get('chroma_persist_dir', './chroma_db')
        self.COLLECTION_NAME = paths.get('collection_name', 'techcorp_docs')
        
        # Models
        models = config_data.get('models', {})
        self.EMBEDDING_MODEL = models.get('embedding_model', 'gemini-embedding-001')
        self.GEMINI_MODEL = models.get('gemini_model', 'gemini-2.5-flash')
        self.EMBEDDING_DIMENSION = models.get('embedding_dimension', 768) 
        self.TEMPERATURE_INTENT = models.get('temperature_intent', 0.0)
        self.TEMPERATURE_CONTENT = models.get('temperature_content', 0.5)
        self.MAX_TOKENS = models.get('max_tokens', 1024)
        
        self.ACTIVE_PROVIDER = config_data.get('active_provider', 'gemini')
        # Retrieval
        retrieval = config_data.get('retrieval', {})
        self.RETRIEVAL_TOP_K = retrieval.get('top_k', 5)
        self.SIMILARITY_SEARCH_K = retrieval.get('similarity_search_k', 10)
    
    def _load_env(self):
        """Load environment variables from .env file."""
        load_dotenv()
        self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        
        if not self.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY not found in environment. "
                "Please create a .env file with: GEMINI_API_KEY=your_key"
            )
    
    def validate(self):
        """Validate configuration settings."""
        # Check knowledge base exists
        kb_path = Path(self.KNOWLEDGE_BASE_PATH)
        if not kb_path.exists():
            raise FileNotFoundError(
                f"Knowledge base not found: {self.KNOWLEDGE_BASE_PATH}"
            )
        
        return True
    
    def display(self):
        """Display current configuration."""
        print("=" * 70)
        print("⚙️  RAG System Configuration")
        print("=" * 70)
        print(f"\n📁 Paths:")
        print(f"   Knowledge Base: {self.KNOWLEDGE_BASE_PATH}")
        print(f"   Chroma DB:      {self.CHROMA_PERSIST_DIR}")
        print(f"   Collection:     {self.COLLECTION_NAME}")
        print(f"\n🤖 Models:")
        print(f"   Embedding:      {self.EMBEDDING_MODEL}")
        print(f"   LLM:            {self.GEMINI_MODEL}")
        print(f"   Temp (Intent):  {self.TEMPERATURE_INTENT}")
        print(f"   Temp (Answer):  {self.TEMPERATURE_CONTENT}")
        print(f"\n🔍 Retrieval:")
        print(f"   Top K:          {self.RETRIEVAL_TOP_K}")
        print(f"   Search K:       {self.SIMILARITY_SEARCH_K}")
        print("=" * 70 + "\n")


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    try:
        config = Config()
        config.display()
        config.validate()
        print("     Configuration valid\n")
        
    except Exception as e:
        print(f"    Configuration error: {e}")