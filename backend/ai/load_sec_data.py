"""
Integration: Load SEC Edgar data into RAG system
"""

from sec_fetcher import fetch_and_prepare_for_rag
from rag_service import get_rag_service
from langchain_core.documents import Document


def load_company_data(ticker: str) -> dict:
    """
    Fetch SEC data and load into RAG system

    Args:
        ticker: Stock ticker

    Returns:
        Status dict
    """
    print(f"📊 Loading data for {ticker}...")

    # Step 1: Fetch SEC documents
    print("  → Fetching SEC Edgar filings...")

    # Use the standalone function that returns formatted docs
    raw_docs = fetch_and_prepare_for_rag(ticker)

    if not raw_docs:
        return {"status": "error", "message": f"No documents found for {ticker}"}

    # Convert to LangChain Document format
    documents = []
    for doc in raw_docs:
        langchain_doc = Document(page_content=doc["text"], metadata=doc["metadata"])
        documents.append(langchain_doc)

    print(f"  ✅ Found {len(documents)} sections")

    # Step 2: Load into RAG
    print("  → Loading into RAG system...")
    rag = get_rag_service()
    result = rag.add_financial_documents(documents)

    if result["status"] == "success":
        print(
            f"  ✅ Added {result['documents_added']} documents, created {result['chunks_created']} chunks"
        )

        # Step 3: Get stats
        stats = rag.get_knowledge_base_stats()
        print(f"  📚 Total documents in knowledge base: {stats['count']}")

        return {
            "status": "success",
            "ticker": ticker,
            "documents_added": result["documents_added"],
            "chunks_created": result["chunks_created"],
            "total_kb_size": stats["count"],
        }
    else:
        return {"status": "error", "message": result.get("error", "Unknown error")}


def analyze_company(ticker: str, quantitative_data: dict = None) -> dict:
    """
    Full analysis: SEC data + quantitative metrics

    Args:
        ticker: Stock ticker
        quantitative_data: Your ValueKit calculations

    Returns:
        Analysis results
    """
    print(f"\n🔍 Analyzing {ticker}...\n")

    # Load company data first
    load_result = load_company_data(ticker)

    if load_result["status"] != "success":
        return load_result

    # Sample quantitative data if not provided
    if not quantitative_data:
        quantitative_data = {
            "dcf": {
                "intrinsic_value": 195.50,
                "current_price": 175.20,
                "upside": "11.6%",
            },
            "roic": "45.2%",
            "margin_of_safety": "11.6%",
        }

    # Perform RAG analysis
    print("\n📈 Running investment analysis...")
    rag = get_rag_service()

    analysis = rag.analyze_with_rag(
        query=f"Based on quantitative metrics and SEC filings, should I invest in {ticker}? Focus on identifying any red flags or moat characteristics.",
        quantitative_data=quantitative_data,
    )

    if analysis["status"] == "success":
        print("\n" + "=" * 60)
        print("INVESTMENT ANALYSIS")
        print("=" * 60)
        print(f"\nCompany: {ticker}")
        print(f"\nQuantitative Metrics:")
        print(f"  - Margin of Safety: {quantitative_data['margin_of_safety']}")
        print(f"  - ROIC: {quantitative_data['roic']}")
        print(f"  - DCF Upside: {quantitative_data['dcf']['upside']}")
        print(f"\n{analysis['analysis']}")
        print("\n" + "=" * 60)

        return {
            "status": "success",
            "ticker": ticker,
            "analysis": analysis["analysis"],
            "sources_used": len(analysis["sources"]),
        }
    else:
        return analysis


if __name__ == "__main__":
    # Example usage
    ticker = "AAPL"

    # Option 1: Just load data
    # load_company_data(ticker)

    # Option 2: Full analysis
    result = analyze_company(ticker)

    print(f"\n✅ Analysis complete!")
