"""
RAG Engine with Conflict Resolution and Noise Filtering
Main query engine with intelligent document retrieval and filtering
"""

from pathlib import Path
from typing import List
from google import genai
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma

from config import Config
from logger import setup_logger
from models import QueryIntent, PolicyAnswer
from ingestion_pipeline import IngestionPipeline


class RagEngine:
    """
    RAG engine with conflict resolution and noise filtering.
    - LangChain vector store (for embeddings only)
    - Pydantic validation
    - Native Gemini API with schema support
    """

    def __init__(self, config: Config):
        """
        Initialize RAG Engine.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = setup_logger(name="RagEngine", log_level="INFO")
        
        self.client = genai.Client(api_key=self.config.GEMINI_API_KEY)
        self.logger.info(f"Initialized Gemini client with model: {self.config.GEMINI_MODEL}")
        
        self.pipeline = IngestionPipeline(config)
        self.vectorstore = None
        
        self.logger.info("RAG Engine initialized successfully")
    
    def load_vectorstore(self):
        """Load existing vector store from disk."""
        try:
            self.vectorstore = self.pipeline.load_existing_vectorstore()
            self.logger.info("Vector store loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load vector store: {e}")
            raise
    
    def ingest_documents(self):
        """Ingest documents and create vector store."""
        try:
            self.vectorstore = self.pipeline.ingest_documents()
            self.logger.info("Documents ingested successfully")
        except Exception as e:
            self.logger.error(f"Failed to ingest documents: {e}")
            raise
    
    def _retrieve_documents(self, query: str, k: int = 10) -> List[Document]:
        """
        Retrieve relevant documents using vector similarity.
        
        Args:
            query: User query
            k: Number of documents to retrieve
            
        Returns:
            List of retrieved documents
        """
        if not self.vectorstore:
            error_msg = "Documents not ingested. Call load_vectorstore() or ingest_documents() first."
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        try:
            results = self.vectorstore.similarity_search(query, k=k)
            print(f"    Retrieved {len(results)} documents")
            self.logger.debug(f"Retrieved {len(results)} documents for query: {query}")
            return results
        except Exception as e:
            self.logger.error(f"Document retrieval failed: {e}")
            raise
    
    def _classify_query_intent(self, query: str) -> QueryIntent:
        """
        Use Gemini to classify query intent and determine which doc types are needed.
        
        Args:
            query: User query
            
        Returns:
            QueryIntent object with intent classification
        """
        prompt = f"""Classify this employee query into ONE category based on what type of document would answer it:

- "policy" - Questions about rules, permissions, procedures, what's allowed/not allowed, work requirements, benefits, HR matters, remote work, time off, company guidelines
- "menu" - Questions about food, cafeteria, meals, dining, lunch, dinner, breakfast
- "memo" - Questions about announcements, updates, communications, notices
- "general" - Unclear or could need multiple document types

Query: {query}

Respond with ONLY the category name (policy, menu, memo, or general). Nothing else."""

        try:
            response = self.client.models.generate_content(
                model=self.config.GEMINI_MODEL,
                contents=prompt,
                config={
                    "temperature": self.config.TEMPERATURE_INTENT,
                    "response_mime_type": "application/json",
                    "response_json_schema": QueryIntent.model_json_schema()
                }
            )
            
            result = QueryIntent.model_validate_json(response.text)
            
            print(f"    Query intent: {result.intent}")
            self.logger.debug(f"Query intent classified as: {result.intent} (confidence: {result.confidence})")
            return result
            
        except Exception as e:
            self.logger.warning(f"Intent classification failed: {e}, defaulting to 'general'")
            print(f"    Intent classification failed: {e}, defaulting to 'general'")
            from models import DocType
            return QueryIntent(intent=DocType.GENERAL, reasoning="Failed to classify", confidence=1)
    
    def _filter_documents_by_metadata(self, documents: List[Document], query: str) -> List[Document]:
        """
        Filter documents based on query intent and metadata.
        Returns only the most relevant and up-to-date documents.
        
        Args:
            documents: Retrieved documents
            query: User query
            
        Returns:
            Filtered documents
        """
        
        result = self._classify_query_intent(query)
        intent = result.intent.value
        
        print(f"    Documents before filtering: {len(documents)}")
        self.logger.info(f"Filtering documents for intent: {intent}")
        
        if intent == 'menu':
            filtered_docs = [d for d in documents if d.metadata.get('doc_type') == 'menu']
            print(f"Keeping only MENU documents: {len(filtered_docs)}")
            self.logger.debug(f"Filtered to {len(filtered_docs)} MENU documents")
            return filtered_docs
        
        elif intent == 'memo':
            filtered_docs = [d for d in documents if d.metadata.get('doc_type') == 'memo']
            print(f"Keeping only MEMO documents: {len(filtered_docs)}")
            self.logger.debug(f"Filtered to {len(filtered_docs)} MEMO documents")
            return filtered_docs
        
        elif intent == 'policy':
            policy_docs = [d for d in documents if d.metadata.get('doc_type') == 'policy']
            print(f"    Found {len(policy_docs)} policy documents")
            self.logger.debug(f"Found {len(policy_docs)} policy documents")
            return self._filter_latest_policy(policy_docs)
        
        else:
            print(f"    General query - filtering all document types")
            self.logger.debug("General query - applying policy filtering")
            return self._filter_latest_policy(documents)

    def _filter_latest_policy(self, documents: List[Document]) -> List[Document]:
        """
        Keep only the latest version of policy documents.
        Non-policy documents pass through unchanged.
        
        Args:
            documents: Documents to filter
            
        Returns:
            Filtered documents with only latest policy
        """
        if not documents:
            return []
        
        policy_docs = [d for d in documents if d.metadata.get('doc_type') == 'policy']
        other_docs = [d for d in documents if d.metadata.get('doc_type') != 'policy']
        
        if len(policy_docs) <= 1:
            return documents
        
        print(f"        Multiple policies detected: {len(policy_docs)}")
        self.logger.debug(f"Multiple policies detected: {len(policy_docs)}")
        
        latest_policy = None
        latest_year = 0
        latest_version = 0
        
        for doc in policy_docs:
            year = doc.metadata.get('year', 0)
            version = doc.metadata.get('version', 0)
            source = doc.metadata.get('source', 'unknown')
            
            print(f"      - {source}: year={year}, version={version}")
            
            if (year > latest_year) or (year == latest_year and version > latest_version):
                latest_policy = doc
                latest_year = year
                latest_version = version
        
        if latest_policy:
            print(f"Keeping latest: {latest_policy.metadata.get('source')} "
                  f"(year: {latest_year}, v{latest_version})")
            self.logger.info(
                f"Selected latest policy: {latest_policy.metadata.get('source')} "
                f"(year: {latest_year}, v{latest_version})"
            )
            return [latest_policy] + other_docs
        
        return documents
    
    def retrieve_relevant_context(self, query: str, k: int = 5) -> List[Document]:
        """
        Main retrieval method:
        1. Retrieve top-k documents by similarity
        2. Filter by document metadata (conflict resolution)
        3. Return only relevant and up-to-date documents
        
        Args:
            query: User query
            k: Number of documents to retrieve initially
            
        Returns:
            Filtered documents
        """
        print("     RETRIEVAL PHASE")
        print("-" * 70)
        self.logger.info(f"Starting retrieval for query: {query}")
        
        documents = self._retrieve_documents(query, k=self.config.SIMILARITY_SEARCH_K)
        
        filtered_docs = self._filter_documents_by_metadata(documents, query)
        
        print(f"    Final documents: {len(filtered_docs)}")
        print("-" * 70 + "\n")
        self.logger.info(f"Retrieval complete. Final documents: {len(filtered_docs)}")
        
        return filtered_docs
        
    def _build_context(self, documents: List[Document]) -> str:
        """
        Build context string from filtered documents.
        Each document is already complete (no chunking).
        
        Args:
            documents: Filtered documents
            
        Returns:
            Context string for LLM
        """
        context_parts = []
        
        for doc in documents:
            meta = doc.metadata
            
            context_parts.append(
                f"=== Document: {meta.get('source', 'unknown')} ===\n"
                f"Type: {meta.get('doc_type', 'unknown')}\n"
                f"Year: {meta.get('year', 'N/A')}\n"
                f"Version: v{meta.get('version', 'N/A')}\n"
                f"Effective Date: {meta.get('effective_date', 'N/A')}\n\n"
                f"Content:\n{doc.page_content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _generate_answer(self, question: str, context: str) -> PolicyAnswer:
        """
        Generate answer using Gemini API.
        
        Args:
            question: User question
            context: Retrieved context
            
        Returns:
            PolicyAnswer with structured response
        """
        prompt = f"""You are a helpful HR assistant for TechCorp Inc.

Answer the employee's question using ONLY the provided documents.

1. ONLY answer if the documents contain relevant information to the question.
2. ALWAYS prioritize the MOST RECENT policy when there are conflicts
3. If an older policy contradicts a newer policy, the NEWER policy wins
4. If the documents DO NOT contain information to answer the question, respond with:
   "answer": "I don't have information about that in the company documents. I can only help with TechCorp policies, menus, and memos.", "cited_sources": []
5. DO NOT make up information or use knowledge outside the provided documents
6. Be direct and concise

Documents:
{context}

EMPLOYEE QUESTION: {question}

ANSWER (with citations):"""
        
        print("     Generating answer with Gemini...\n")
        self.logger.info("Generating answer with LLM")
        
        try:
            response = self.client.models.generate_content(
                model=self.config.GEMINI_MODEL,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": PolicyAnswer.model_json_schema(),
                    "temperature": self.config.TEMPERATURE_CONTENT
                }
            )
            
            answer = PolicyAnswer.model_validate_json(response.text)
            self.logger.info("Answer generated successfully")
            return answer
        
        except Exception as e:
            self.logger.error(f"Failed to generate answer: {e}")
            raise
    
    def query(self, question: str) -> PolicyAnswer:
        """
        Main query method.
        
        Args:
            question: User's question
        
        Returns:
            PolicyAnswer with structured response
        """
        print("=" * 70)
        print(f"QUERY: {question}")
        print("=" * 70 + "\n")
        self.logger.info(f"Processing query: {question}")
        
        relevant_docs = self.retrieve_relevant_context(question, k=self.config.RETRIEVAL_TOP_K)
        
        if not relevant_docs:
            self.logger.warning("No relevant documents found")
            return PolicyAnswer(
                answer="No relevant documents found to answer your question.",
                reasoning="No documents matched the query",
                cited_sources=[],
                policy_allows_remote=None
            )
        
        context = self._build_context(relevant_docs)
        
        answer = self._generate_answer(question, context)

        print("\n   Generated answer")
        return answer


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    try:
        config = Config()
        
        rag = RagEngine(config)
        
        try:
            rag.load_vectorstore()
        except FileNotFoundError:
            print("Vector store not found. Ingesting documents...")
            rag.ingest_documents()
        
        test_question = "Can I work from home?"
        answer = rag.query(test_question)
        
        print("\n" + "=" * 70)
        print("   ANSWER:")
        print("=" * 70)
        print(f"\n{answer.answer}\n")
        print(f"    Reasoning: {answer.reasoning}")
        print(f"    Sources: {answer.cited_sources}")
        print(f"    Policy allows remote: {answer.policy_allows_remote}")
        print("=" * 70)
        
    except Exception as e:
        print(f"    Error: {e}")