from anthropic import Anthropic
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document

from config import RAGConfig
from vector_store import get_vector_store


class RAGService:
    """Main RAG Service for ValueKit Financial Analysis"""

    def __init__(self):
        self.config = RAGConfig()
        self.client = Anthropic(api_key=self.config.ANTHROPIC_API_KEY)
        self.vector_store = get_vector_store()

    def add_financial_documents(
        self, documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Add financial documents to the knowledge base

        Args:
            documents: List of dicts with structure:
                {
                    'text': str,  # Document content
                    'metadata': {  # Optional metadata
                        'company': str,
                        'document_type': str,  # e.g., '10-K', 'earnings_call'
                        'date': str,
                        'ticker': str
                    }
                }

        Returns:
            Dict with status and number of chunks added
        """
        try:
            num_chunks = self.vector_store.add_documents(documents)
            return {
                "status": "success",
                "documents_added": len(documents),
                "chunks_created": num_chunks,
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _format_context(self, documents: List[Document]) -> str:
        """Format retrieved documents into context string"""
        context_parts = []
        for i, doc in enumerate(documents, 1):
            metadata = doc.metadata
            context_parts.append(
                f"Document {i}:\n"
                f"Source: {metadata.get('document_type', 'Unknown')} - {metadata.get('company', 'Unknown')}\n"
                f"Content: {doc.page_content}\n"
            )
        return "\n---\n".join(context_parts)

    def analyze_with_rag(
        self,
        query: str,
        quantitative_data: Optional[Dict[str, Any]] = None,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """
        Perform RAG-enhanced analysis

        Args:
            query: User query (e.g., "Should I invest in AAPL?")
            quantitative_data: Dict with DCF, ROIC, Margin of Safety etc.
            max_tokens: Max response length

        Returns:
            Dict with analysis and sources
        """
        # Step 1: Retrieve relevant documents
        retrieved_docs = self.vector_store.similarity_search_with_score(query)

        # Step 2: Format context
        context = self._format_context([doc for doc, score in retrieved_docs])

        # Step 3: Build prompt with quantitative data as primary
        prompt = self._build_analysis_prompt(query, context, quantitative_data)

        # Step 4: Get Claude's analysis
        try:
            message = self.client.messages.create(
                model=self.config.LLM_MODEL,
                max_tokens=max_tokens,
                temperature=self.config.LLM_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )

            return {
                "status": "success",
                "analysis": message.content[0].text,
                "sources": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata,
                        "relevance_score": float(score),
                    }
                    for doc, score in retrieved_docs
                ],
                "quantitative_metrics": quantitative_data,
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    def _build_analysis_prompt(
        self, query: str, context: str, quantitative_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build the analysis prompt for Claude"""

        prompt = f"""You are a quantitative value investing analyst. Your primary focus is on hard numbers and financial metrics.

QUANTITATIVE METRICS (PRIMARY DECISION FACTORS):
{self._format_quantitative_data(quantitative_data) if quantitative_data else "No quantitative data provided."}

QUALITATIVE CONTEXT (SUPPORTING INFORMATION):
{context}

USER QUERY:
{query}

INSTRUCTIONS:
1. Base your analysis PRIMARILY on the quantitative metrics (DCF, ROIC, Margin of Safety)
2. Use the qualitative context ONLY to:
   - Identify red flags that might invalidate the numbers
   - Provide additional confidence or caution
   - Explain why numbers might be misleading
3. If qualitative information contradicts strong quantitative signals, explain the conflict clearly
4. Always prioritize mathematical analysis over narrative
5. Be precise with numbers and cite specific metrics

Provide your analysis:"""

        return prompt

    def _format_quantitative_data(self, data: Dict[str, Any]) -> str:
        """Format quantitative metrics for the prompt"""
        if not data:
            return "No data available"

        sections = []

        if "dcf" in data:
            sections.append(f"DCF Analysis:\n{self._format_dict(data['dcf'])}")

        if "roic" in data:
            sections.append(f"ROIC: {data['roic']}")

        if "margin_of_safety" in data:
            sections.append(f"Margin of Safety: {data['margin_of_safety']}")

        if "other_metrics" in data:
            sections.append(
                f"Other Metrics:\n{self._format_dict(data['other_metrics'])}"
            )

        return "\n\n".join(sections)

    def _format_dict(self, d: Dict, indent: int = 2) -> str:
        """Format dictionary for readable output"""
        lines = []
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"{' ' * indent}{key}:")
                lines.append(self._format_dict(value, indent + 2))
            else:
                lines.append(f"{' ' * indent}{key}: {value}")
        return "\n".join(lines)

    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        return self.vector_store.get_collection_stats()


# Factory function
def get_rag_service() -> RAGService:
    """Get RAG service instance"""
    return RAGService()
