"""
Quick Multi-Ticker Test - 4 Companies only
Fast validation across different sectors
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sec_fetcher import fetch_and_prepare_for_rag
from rag_service import get_rag_service
from langchain_core.documents import Document
import time


# Quick test: 1 ticker per sector
TEST_COMPANIES = {
    "Tech": ["MSFT"],
    "Finance": ["JPM"],
    "Retail": ["WMT"],
    "Semiconductor": ["NVDA"],
}


def test_single_ticker(ticker: str, sector: str) -> dict:
    """Test SEC fetch + RAG for one ticker"""

    print(f"\n{'=' * 70}")
    print(f"🧪 TESTING: {ticker} ({sector})")
    print(f"{'=' * 70}\n")

    result = {
        "ticker": ticker,
        "sector": sector,
        "status": "unknown",
        "sections_found": 0,
        "chunks_created": 0,
        "error": None,
    }

    try:
        # Step 1: Fetch SEC data
        print(f"📥 Step 1: Fetching SEC data...")
        start_time = time.time()

        raw_docs = fetch_and_prepare_for_rag(ticker)

        fetch_time = time.time() - start_time

        if not raw_docs:
            result["status"] = "failed"
            result["error"] = "No documents found"
            print(f"❌ FAILED: No documents found")
            return result

        result["sections_found"] = len(raw_docs)
        print(f"✅ Found {len(raw_docs)} sections in {fetch_time:.1f}s")

        # Show section sizes
        for doc in raw_docs:
            section = doc["metadata"]["section_name"]
            length = len(doc["text"])
            print(f"   - {section}: {length:,} chars")

        # Step 2: Convert to LangChain
        print(f"\n📝 Step 2: Converting to LangChain documents...")
        documents = []
        for doc in raw_docs:
            langchain_doc = Document(page_content=doc["text"], metadata=doc["metadata"])
            documents.append(langchain_doc)

        # Step 3: Load into RAG
        print(f"\n🔮 Step 3: Loading into RAG system...")
        rag = get_rag_service()

        add_result = rag.add_financial_documents(documents)

        if add_result["status"] == "success":
            result["chunks_created"] = add_result["chunks_created"]
            print(f"✅ Created {add_result['chunks_created']} chunks")

            # Step 4: Quick test query
            print(f"\n🔍 Step 4: Testing RAG query...")

            test_query = (
                f"What are the key competitive advantages and risks for {ticker}?"
            )
            analysis = rag.analyze_with_rag(
                query=test_query,
                quantitative_data={"roic": "20%", "margin_of_safety": "10%"},
            )

            if analysis["status"] == "success":
                result["status"] = "success"
                print(f"✅ RAG query successful!")
                print(f"   Sources used: {len(analysis['sources'])}")
                print(f"\n   Analysis preview:")
                print(f"   {analysis['analysis'][:300]}...")
            else:
                result["status"] = "partial"
                result["error"] = "RAG query failed"
                print(f"⚠️  RAG loaded but query failed")
        else:
            result["status"] = "failed"
            result["error"] = f"Failed to add to RAG: {add_result.get('error')}"
            print(f"❌ Failed to add documents to RAG")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()

    return result


def run_quick_tests():
    """Run quick tests - 4 companies only"""

    print("\n" + "=" * 70)
    print("🚀 QUICK MULTI-TICKER TEST (4 companies)")
    print("=" * 70)
    print(f"\nTesting: {', '.join([t[0] for t in TEST_COMPANIES.values()])}")
    print(f"Sectors: {', '.join(TEST_COMPANIES.keys())}\n")

    all_results = []

    for sector, tickers in TEST_COMPANIES.items():
        for ticker in tickers:
            result = test_single_ticker(ticker, sector)
            all_results.append(result)

            # Wait between tickers to avoid rate limits
            if result["status"] == "success":
                print(f"\n⏳ Waiting 10s to avoid rate limits...")
                time.sleep(10)
            else:
                print(f"\n⏳ Waiting 5s before next ticker...")
                time.sleep(5)

    # Summary
    print("\n" + "=" * 70)
    print("📊 QUICK TEST SUMMARY")
    print("=" * 70 + "\n")

    success = [r for r in all_results if r["status"] == "success"]
    failed = [r for r in all_results if r["status"] in ["failed", "error"]]
    partial = [r for r in all_results if r["status"] == "partial"]

    print(f"✅ Success: {len(success)}/4")
    print(f"⚠️  Partial: {len(partial)}/4")
    print(f"❌ Failed:  {len(failed)}/4\n")

    if success:
        print("✅ Successful tickers:")
        for r in success:
            print(
                f"   {r['ticker']:6s} ({r['sector']:15s}) - {r['sections_found']} sections, {r['chunks_created']} chunks"
            )

    if partial:
        print("\n⚠️  Partial success:")
        for r in partial:
            print(
                f"   {r['ticker']:6s} ({r['sector']:15s}) - {r.get('error', 'Unknown')}"
            )

    if failed:
        print("\n❌ Failed tickers:")
        for r in failed:
            print(
                f"   {r['ticker']:6s} ({r['sector']:15s}) - {r.get('error', 'Unknown')}"
            )

    # Insights
    print("\n" + "=" * 70)
    print("💡 KEY INSIGHTS")
    print("=" * 70 + "\n")

    if len(success) == 4:
        print("🎉 Perfect! System works across all sectors!")
        print("   → Ready for UI integration")
        print("   → Can proceed with moat analysis refinement")
    elif len(success) >= 3:
        print("✅ Good! System works for most sectors")
        print(f"   → Check failed tickers: {[r['ticker'] for r in failed + partial]}")
        print("   → Might need sector-specific handling")
    elif len(success) >= 2:
        print("⚠️  Partial success - needs investigation")
        print("   → System works but not reliably")
        print("   → Debug failed cases before proceeding")
    else:
        print("❌ Major issues detected")
        print("   → Need to fix core problems first")

    print(f"\n{'=' * 70}")
    print(f"✅ QUICK TEST COMPLETE!")
    print(f"{'=' * 70}\n")

    return all_results


if __name__ == "__main__":
    results = run_quick_tests()
