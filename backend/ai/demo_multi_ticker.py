"""
Multi-Ticker Test Suite for SEC RAG System
Tests verschiedene Sectors und Company Sizes
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sec_fetcher import fetch_and_prepare_for_rag
from rag_service import get_rag_service
from langchain_core.documents import Document
import time


TEST_COMPANIES = {
    "Tech Giants": ["AAPL", "MSFT", "GOOGL"],
    "Finance": ["JPM", "BAC"],
    "Retail": ["WMT", "COST"],
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

        # Clear old data for this ticker
        print(f"   Clearing old data...")

        add_result = rag.add_financial_documents(documents)

        if add_result["status"] == "success":
            result["chunks_created"] = add_result["chunks_created"]
            print(f"✅ Created {add_result['chunks_created']} chunks")

            # Step 4: Quick test query
            print(f"\n🔍 Step 4: Testing RAG query...")

            test_query = f"What are the main business segments of {ticker}?"
            analysis = rag.analyze_with_rag(
                query=test_query, quantitative_data={"test": "data"}
            )

            if analysis["status"] == "success":
                result["status"] = "success"
                print(f"✅ RAG query successful!")
                print(f"   Sources used: {len(analysis['sources'])}")
                print(f"\n   Preview: {analysis['analysis'][:200]}...")
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


def run_all_tests():
    """Run tests for all companies"""

    print("\n" + "=" * 70)
    print("🚀 MULTI-TICKER TEST SUITE")
    print("=" * 70)
    print(
        f"\nTesting {sum(len(tickers) for tickers in TEST_COMPANIES.values())} companies"
    )
    print(f"Sectors: {', '.join(TEST_COMPANIES.keys())}\n")

    all_results = []

    for sector, tickers in TEST_COMPANIES.items():
        print(f"\n{'#' * 70}")
        print(f"# SECTOR: {sector}")
        print(f"{'#' * 70}")

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
    print("📊 TEST SUMMARY")
    print("=" * 70 + "\n")

    success = [r for r in all_results if r["status"] == "success"]
    failed = [r for r in all_results if r["status"] in ["failed", "error"]]
    partial = [r for r in all_results if r["status"] == "partial"]

    print(f"✅ Success: {len(success)}/{len(all_results)}")
    print(f"⚠️  Partial: {len(partial)}/{len(all_results)}")
    print(f"❌ Failed:  {len(failed)}/{len(all_results)}\n")

    if success:
        print("Successful tickers:")
        for r in success:
            print(
                f"  ✅ {r['ticker']:6s} ({r['sector']:15s}) - {r['sections_found']} sections, {r['chunks_created']} chunks"
            )

    if partial:
        print("\nPartial success:")
        for r in partial:
            print(
                f"  ⚠️  {r['ticker']:6s} ({r['sector']:15s}) - {r.get('error', 'Unknown')}"
            )

    if failed:
        print("\nFailed tickers:")
        for r in failed:
            print(
                f"  ❌ {r['ticker']:6s} ({r['sector']:15s}) - {r.get('error', 'Unknown')}"
            )

    # Save results
    print(f"\n💾 Saving results to test_results.txt...")
    with open("test_results.txt", "w") as f:
        f.write("SEC RAG SYSTEM - MULTI-TICKER TEST RESULTS\n")
        f.write("=" * 70 + "\n\n")

        for r in all_results:
            f.write(f"{r['ticker']} ({r['sector']}): {r['status']}\n")
            if r["error"]:
                f.write(f"  Error: {r['error']}\n")
            else:
                f.write(
                    f"  Sections: {r['sections_found']}, Chunks: {r['chunks_created']}\n"
                )
            f.write("\n")

    print(f"\n{'=' * 70}")
    print(f"✅ TEST SUITE COMPLETE!")
    print(f"{'=' * 70}\n")

    return all_results


if __name__ == "__main__":
    results = run_all_tests()
