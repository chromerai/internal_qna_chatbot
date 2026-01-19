"""
Pydantic Models and Metadata Extraction
Contains all data validation models and document metadata extraction logic
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from langchain_core.documents import Document


# ============================================================================
# ENUMS
# ============================================================================

class DocType(str, Enum):
    """Document Type Enumeration"""
    POLICY = "policy"
    MENU = "menu"
    MEMO = "memo"
    GENERAL = "general"


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PolicyMetaData(BaseModel):
    """Type-safe Metadata for Documents"""
    source: str = Field(description="Filename of the document")
    doc_type: DocType = Field(description="Type of document: policy, menu, memo, general")
    effective_date: str = Field(description="ISO format date (YYYY-MM-DD) when the policy became effective")
    version: int = Field(default=0, description="Version of the document if available otherwise 0")
    year: int = Field(description="Year extracted from effective date")

    @field_validator('effective_date', mode='after')
    @classmethod
    def validate_date(cls, value: str) -> str:
        """Validate ISO FORMAT date"""
        try:
            datetime.fromisoformat(value)
            return value
        except ValueError:
            raise ValueError(f"Must be ISO format date (YYYY-MM-DD), got: {value}")


class PolicyAnswer(BaseModel):
    """
    Structured LLM output with enforced citations
    """
    answer: str = Field(description="Direct answer to the employee's question")
    reasoning: str = Field(description="Brief explanation for choosing this answer")
    cited_sources: Optional[List[str]] = Field(description="Exact filenames of documents used as sources")
    policy_allows_remote: Optional[bool] = Field(
        description="Whether the current policy allows remote work (true/false/null if not applicable)"
    )


class QueryIntent(BaseModel):
    """
    Structured LLM output for classifying query intent for better query understanding
    """
    intent: DocType = Field(description="Type of query: policy, menu, memo, general")
    reasoning: str = Field(description="Brief reasoning for the query classification (1 line)")
    confidence: int = Field(description="Confidence score between 1 and 5", ge=1, le=5)


# ============================================================================
# METADATA EXTRACTION
# ============================================================================

class DocumentMetadata:
    """
    Metadata Extraction from files
    Extracts document type, date, and version information
    """

    def __init__(self, filename: str, content: str):
        """
        Initialize metadata extractor.
        
        Args:
            filename: Name of the document file
            content: Full text content of the document
        """
        self.filename = filename
        self.content = content

        self.docType = self._classify_doc_type()
        self.effective_date = self._extract_date()
        self.version = self._extract_version_info()

    def _classify_doc_type(self) -> str:
        """
        Classify document based on filename and content keywords.
        
        Returns:
            Document type as string
        """
        filename = self.filename.lower()
        content = self.content.lower()

        if 'policy' in filename:
            return DocType.POLICY.value
        elif 'menu' in filename or 'cafeteria' in filename:
            return DocType.MENU.value
        elif 'memo' in filename:
            return DocType.MEMO.value
        else:
            return DocType.GENERAL.value
    
    def _extract_date(self) -> datetime:
        """
        Extract date from filename or content.
        Falls back to file modification date if not found.
        
        Returns:
            datetime object
        """
        # Search from filename - easier
        year_match = re.search(r'_(\d{4})\.txt', self.filename)
        if year_match:
            year = int(year_match.group(1))
            return datetime(year, 1, 1)
        
        # Search from content - more complex
        date_patterns = [
            (r'Effective Date:\s*([A-Za-z]+\s+\d{1,2},\s*\d{4})', "%b %d, %Y"),
            (r'Effective Date:\s*(\d{4}-\d{2}-\d{2})', '%Y-%m-%d'),
        ]

        for pattern, date_format in date_patterns:
            match = re.search(pattern, self.content)
            if match:
                try:
                    date_str = match.group(1)
                    return datetime.strptime(date_str, date_format)
                except ValueError:
                    continue
        
        # Fallback to file modification date
        file_path = Path("knowledge_base", self.filename).resolve()
        doc_date = datetime.fromtimestamp(os.path.getmtime(file_path))
        print(f"Warning: No date in {self.filename}, using file date: {doc_date.strftime('%Y-%m-%d')}")
        return doc_date
    
    def _extract_version_info(self) -> int:
        """
        Extract version number (v1, v2, v3, etc.)
        
        Returns:
            Version number as integer, 0 if not found
        """
        version_match = re.search(r'_v(\d+)_', self.filename)
        if version_match:
            return int(version_match.group(1))
        return 0
    
    def _to_pydantic(self) -> PolicyMetaData:
        """
        Convert to Pydantic model for validation.
        
        Returns:
            PolicyMetaData instance
        """
        return PolicyMetaData(
            source=self.filename,
            doc_type=self.docType,
            effective_date=self.effective_date.isoformat(),
            version=self.version,
            year=self.effective_date.year
        )
    
    def _to_langchain_document(self) -> Document:
        """
        Convert to LangChain Document for vector store.
        
        Returns:
            LangChain Document instance
        """
        return Document(
            page_content=self.content,
            metadata=self._to_pydantic().model_dump()
        )


# ============================================================================
# MAIN (for testing)
# ============================================================================

if __name__ == "__main__":
    # Test metadata extraction
    test_filename = "remote_work_policy_v2_2024.txt"
    test_content = """
    TechCorp Remote Work Policy
    Effective Date: Jan 15, 2024
    
    This policy allows employees to work remotely up to 3 days per week.
    """
    
    extractor = DocumentMetadata(test_filename, test_content)
    
    print("Testing DocumentMetadata:")
    print(f"  Filename: {extractor.filename}")
    print(f"  Doc Type: {extractor.docType}")
    print(f"  Date: {extractor.effective_date}")
    print(f"  Version: {extractor.version}")
    
    print("\nPydantic Model:")
    meta = extractor._to_pydantic()
    print(f"  {meta.model_dump_json(indent=2)}")
    
    print("\n✅ Models validated successfully!")