"""
Document Ingestion Pipeline
Handles document loading, metadata extraction, and vector store creation
"""

from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

from config import Config
from logger import setup_logger
from models import DocumentMetadata


class IngestionPipeline:
    """
    Pipeline for ingesting documents into vector store.
    Handles metadata extraction and Chroma DB creation.
    """
    
    def __init__(self, config: Config):
        """
        Initialize ingestion pipeline.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = setup_logger(name="IngestionPipeline", log_level="INFO")
        self.kb_path = Path(config.KNOWLEDGE_BASE_PATH)
        self.vectorstore = None
        
        self._initialize_embeddings()
        
        self.logger.info(f"Ingestion pipeline initialized for provider: {config.ACTIVE_PROVIDER}")
    
    def _initialize_embeddings(self):
        """Initialize embedding model based on active provider."""
        try:
            if self.config.ACTIVE_PROVIDER == 'gemini':
                self.embedding = GoogleGenerativeAIEmbeddings(
                    model=self.config.EMBEDDING_MODEL,
                    google_api_key=self.config.GEMINI_API_KEY,
                    output_dimensionality=self.config.EMBEDDING_DIMENSION,
                    task_type="retrieval-document"
                )
                self.logger.info(f"Initialized Gemini embeddings: {self.config.EMBEDDING_MODEL}")
            
            # elif self.config.ACTIVE_PROVIDER == 'openai':
            #     from langchain_openai import OpenAIEmbeddings
            #     self.embedding = OpenAIEmbeddings(
            #         model=self.config.EMBEDDING_MODEL,
            #         openai_api_key=self.config.API_KEY,
            #         dimensions=self.config.EMBEDDING_DIMENSION
            #     )
            #     self.logger.info(f"Initialized OpenAI embeddings: {self.config.EMBEDDING_MODEL}")
            
            # elif self.config.ACTIVE_PROVIDER == 'ollama':
            #     from langchain_ollama import OllamaEmbeddings
            #     self.embedding = OllamaEmbeddings(
            #         model=self.config.EMBEDDING_MODEL,
            #         base_url=self.config.BASE_URL
            #     )
            #     self.logger.info(f"Initialized Ollama embeddings: {self.config.EMBEDDING_MODEL}")
            
            else:
                raise ValueError(f"Unsupported provider: {self.config.ACTIVE_PROVIDER}")
        
        except Exception as e:
            self.logger.error(f"Failed to initialize embeddings: {e}")
            raise
    
    def ingest_documents(self) -> Chroma:
        """
        Main ingestion method:
        1. Load all .txt files from knowledge base
        2. Extract metadata from each document
        3. Create vector store and persist to disk
        
        Returns:
            Chroma vector store instance
        """
        print("Initializing RAG Pipeline...")
        self.logger.info("Starting document ingestion")
        
        print(f"    Ingesting documents from: {self.kb_path}")

        vectorstore_path = Path(self.config.CHROMA_PERSIST_DIR)
        if vectorstore_path.exists():
            self.logger.info("Removing existing vector store...")
            import shutil
            shutil.rmtree(vectorstore_path)
            self.logger.info("Existing vector store removed.")
        
        if not self.kb_path.exists():
            error_msg = f"Knowledge base not found: {self.kb_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        txt_files = list(self.kb_path.glob("*.txt"))
        
        if not txt_files:
            error_msg = f"No .txt files in {self.kb_path}"
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        print(f"Found {len(txt_files)} files\n")
        self.logger.info(f"Found {len(txt_files)} .txt files")
        
        all_documents = []
        
        for filepath in txt_files:
            try:
                print(f"    Processing: {filepath.name}")
                self.logger.debug(f"Processing file: {filepath.name}")
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata_extractor = DocumentMetadata(filepath.name, content)
                langchain_doc = metadata_extractor._to_langchain_document()
                
                meta = metadata_extractor._to_pydantic()
                print(f"      Type: {meta.doc_type}")
                print(f"      Date: {meta.year}")
                print(f"      Version: {meta.version}")
            
                all_documents.append(langchain_doc)
                self.logger.info(f"Successfully processed: {filepath.name}")
                print()
            
            except Exception as e:
                self.logger.error(f"Failed to process {filepath.name}: {e}")
                print(f"    Error processing {filepath.name}: {e}\n")
                continue
        
        if not all_documents:
            error_msg = "No documents were successfully processed"
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Create vector store
        print("     Creating vector store...")
        self.logger.info("Creating Chroma vector store...")
        
        try:
            self.vectorstore = Chroma.from_documents(
                documents=all_documents,
                embedding=self.embedding,
                collection_name=self.config.COLLECTION_NAME,
                persist_directory=self.config.CHROMA_PERSIST_DIR
            )
            
            print(f"    Indexed {len(all_documents)} documents from {len(txt_files)} files\n")
            self.logger.info(
                f"  Vector store created successfully. "
                f"  Documents: {len(all_documents)}, Files: {len(txt_files)}"
            )
            
            return self.vectorstore
        
        except Exception as e:
            self.logger.error(f"Failed to create vector store: {e}")
            raise
    
    def load_existing_vectorstore(self) -> Chroma:
        """
        Load existing vector store from disk.
        
        Returns:
            Chroma vector store instance
        """
        persist_dir = Path(self.config.CHROMA_PERSIST_DIR)
        
        if not persist_dir.exists():
            error_msg = (
                f"Chroma DB not found at {self.config.CHROMA_PERSIST_DIR}. "
                "Please run ingest_documents() first."
            )
            self.logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            self.vectorstore = Chroma(
                persist_directory=self.config.CHROMA_PERSIST_DIR,
                embedding_function=self.embedding,
                collection_name=self.config.COLLECTION_NAME
            )
            
            print(f"    Loaded existing vector store from {self.config.CHROMA_PERSIST_DIR}")
            self.logger.info(f"Loaded vector store from {self.config.CHROMA_PERSIST_DIR}")
            
            return self.vectorstore
        
        except Exception as e:
            self.logger.error(f"Failed to load vector store: {e}")
            raise


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    try:
        config = Config()
        
        pipeline = IngestionPipeline(config)
        
        vectorstore = pipeline.ingest_documents()
        
        print("     Ingestion complete!")
        
    except Exception as e:
        print(f"    Ingestion failed: {e}")