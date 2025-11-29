"""
Quick test: SEC data → RAG system
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sec_fetcher import fetch_and_prepare_for_rag
from rag_service import get_rag_service
from langchain_core.documents import Document


def test_sec_to_rag(ticker: str = "AAPL"):
    """Test the complete pipeline"""

    print(f"\n{'=' * 60}")
    print(f"TEST: SEC Edgar → RAG System")
    print(f"{'=' * 60}\n")

    # Step 1: Fetch SEC data
    print(f"📥 Step 1: Fetching SEC data for {ticker}...")
    raw_docs = fetch_and_prepare_for_rag(ticker)

    if not raw_docs:
        print("❌ Failed to fetch SEC data")
        return False

    print(f"✅ Got {len(raw_docs)} sections:")
    for doc in raw_docs:
        section = doc["metadata"]["section_name"]
        length = len(doc["text"])
        print(f"   - {section}: {length} chars")

    # Step 2: Convert to LangChain documents
    print(f"\n📝 Step 2: Converting to LangChain documents...")
    documents = []
    for doc in raw_docs:
        langchain_doc = Document(page_content=doc["text"], metadata=doc["metadata"])
        documents.append(langchain_doc)
        print(f"   ✅ Created doc: {doc['metadata']['section_name']}")

    # Step 3: Load into RAG
    print(f"\n🔮 Step 3: Loading into RAG system...")
    try:
        rag = get_rag_service()
        result = rag.add_financial_documents(documents)

        if result["status"] == "success":
            print(f"✅ Success!")
            print(f"   - Documents added: {result['documents_added']}")
            print(f"   - Chunks created: {result['chunks_created']}")

            # Step 4: Test query
            print(f"\n🔍 Step 4: Testing RAG query...")

            quantitative_data = {
                "margin_of_safety": "15.2%",
                "roic": "45.2%",
                "fcf_yield": "3.8%",
            }

            analysis = rag.analyze_with_rag(
                query=f"What are the main risks for {ticker}?",
                quantitative_data=quantitative_data,
            )

            if analysis["status"] == "success":
                print(f"✅ RAG Analysis successful!")
                print(f"\n{'-' * 60}")
                print(analysis["analysis"][:500] + "...")
                print(f"{'-' * 60}\n")
                print(f"📚 Sources used: {len(analysis['sources'])}")

                return True
            else:
                print(f"❌ Analysis failed: {analysis.get('error')}")
                return False
        else:
            print(f"❌ Failed to add documents: {result.get('error')}")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_sec_to_rag("AAPL")

    if success:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
