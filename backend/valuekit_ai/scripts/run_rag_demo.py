"""
Test script for ValueKit RAG system
Run this to verify everything works
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
import sys
import traceback

print("🔍 Starting test script...")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
print("-" * 50)

# Test imports first
print("\n📦 Testing imports...")
try:
    print("  - Importing anthropic...")
    import anthropic

    print("    ✅ anthropic imported")
except ImportError as e:
    print(f"    ❌ Failed to import anthropic: {e}")
    sys.exit(1)

try:
    print("  - Importing voyageai...")
    import voyageai

    print("    ✅ voyageai imported")
except ImportError as e:
    print(f"    ❌ Failed to import voyageai: {e}")
    sys.exit(1)

try:
    print("  - Importing chromadb...")
    import chromadb

    print("    ✅ chromadb imported")
except ImportError as e:
    print(f"    ❌ Failed to import chromadb: {e}")
    sys.exit(1)

try:
    print("  - Importing langchain...")
    from langchain_core.documents import Document
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    print("    ✅ langchain imported")
except ImportError as e:
    print(f"    ❌ Failed to import langchain: {e}")
    print(
        "    Run: pip install langchain-core langchain-text-splitters --break-system-packages"
    )
    sys.exit(1)

print("\n✅ All imports successful!\n")

# Test config and API keys
print("🔑 Checking API keys...")
try:
    from backend.valuekit_ai.config.config import RAGConfig

    RAGConfig.validate()
    print("✅ API keys found and validated\n")
except Exception as e:
    print(f"❌ API key validation failed: {e}\n")
    sys.exit(1)

# Now import our modules
try:
    print("📦 Importing RAG service...")
    from backend.valuekit_ai.rag.rag_service import get_rag_service

    print("✅ RAG service imported\n")
except Exception as e:
    print(f"❌ Failed to import RAG service: {e}")
    traceback.print_exc()
    sys.exit(1)


def test_basic_setup():
    """Test 1: Basic initialization"""
    print("=" * 50)
    print("TEST 1: Basic Setup")
    print("=" * 50)

    try:
        print("  - Creating RAG service instance...")
        rag = get_rag_service()
        print("  ✅ RAG Service initialized successfully")

        print("  - Getting vector store stats...")
        stats = rag.get_knowledge_base_stats()
        print(f"  ✅ Vector store stats: {stats}")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("\n  Full traceback:")
        traceback.print_exc()
        return False

    return True


def test_add_documents():
    """Test 2: Add sample financial documents"""
    print("\n" + "=" * 50)
    print("TEST 2: Adding Documents")
    print("=" * 50)

    try:
        print("  - Getting RAG service...")
        rag = get_rag_service()

        # Sample financial documents
        sample_docs = [
            {
                "text": """Apple Inc. Q4 2024 Results:
                Revenue: $89.5B (up 6% YoY)
                iPhone revenue: $46.2B
                Services revenue: $22.3B (record high)
                Gross margin: 46.2%
                Operating cash flow: $27.5B
                
                Management noted strong demand for iPhone 15 Pro models and 
                continued growth in Services segment. R&D spending increased 
                to $7.8B as company invests in AI capabilities.""",
                "metadata": {
                    "company": "Apple Inc.",
                    "ticker": "AAPL",
                    "document_type": "earnings_report",
                    "date": "2024-11-01",
                },
            },
            {
                "text": """Apple Inc. 10-K Filing - Risk Factors:
                
                The company faces intense competition in smartphone market,
                particularly from Chinese manufacturers. Supply chain 
                dependencies on Asian manufacturers present operational risks.
                
                Regulatory scrutiny on App Store practices continues in EU 
                and US, potentially impacting Services revenue. China market 
                exposure (~19% of revenue) presents geopolitical risk.
                
                Company maintains strong balance sheet with $162B in cash
                and marketable securities, offset by $111B in debt.""",
                "metadata": {
                    "company": "Apple Inc.",
                    "ticker": "AAPL",
                    "document_type": "10-K",
                    "date": "2024-10-27",
                },
            },
        ]

        print(f"  - Adding {len(sample_docs)} documents...")
        result = rag.add_financial_documents(sample_docs)
        print(f"  ✅ Documents added: {result}")

        print("  - Getting updated stats...")
        stats = rag.get_knowledge_base_stats()
        print(f"  ✅ Updated stats: {stats}")

    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("\n  Full traceback:")
        traceback.print_exc()
        return False

    return True


def test_rag_analysis():
    """Test 3: Perform RAG analysis with quantitative data"""
    print("\n" + "=" * 50)
    print("TEST 3: RAG Analysis")
    print("=" * 50)

    try:
        print("  - Getting RAG service...")
        rag = get_rag_service()

        # Sample quantitative data (wie du sie aus ValueKit hast)
        quantitative_data = {
            "dcf": {
                "intrinsic_value": 195.50,
                "current_price": 175.20,
                "upside": "11.6%",
            },
            "roic": "45.2%",
            "margin_of_safety": "11.6%",
            "other_metrics": {
                "pe_ratio": 28.5,
                "debt_to_equity": 1.8,
                "fcf_yield": "3.2%",
            },
        }

        query = "Should I invest in Apple (AAPL) based on value investing principles?"

        print(f"  - Running analysis for query: '{query}'")
        print("  - This may take 10-30 seconds (Claude API call)...")

        result = rag.analyze_with_rag(query=query, quantitative_data=quantitative_data)

        if result["status"] == "success":
            print("\n  ✅ ANALYSIS RESULT:")
            print("  " + "-" * 48)
            # Print analysis with indentation
            for line in result["analysis"].split("\n"):
                print(f"  {line}")
            print("  " + "-" * 48)
            print(f"\n  📊 Quantitative Metrics Used:")
            print(
                f"    - DCF Intrinsic Value: ${quantitative_data['dcf']['intrinsic_value']}"
            )
            print(f"    - Margin of Safety: {quantitative_data['margin_of_safety']}")
            print(f"    - ROIC: {quantitative_data['roic']}")
            print(f"\n  📚 Sources Used: {len(result['sources'])} documents")
            for i, source in enumerate(result["sources"], 1):
                print(f"\n    Source {i}:")
                print(f"      Type: {source['metadata'].get('document_type')}")
                print(f"      Relevance: {source['relevance_score']:.3f}")
        else:
            print(f"  ❌ Analysis failed: {result['error']}")
            return False

    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("\n  Full traceback:")
        traceback.print_exc()
        return False

    return True


def run_all_tests():
    """Run all tests"""
    print("\n" + "🚀 " * 20)
    print("VALUEKIT RAG SYSTEM TEST SUITE")
    print("🚀 " * 20 + "\n")

    tests = [
        ("Basic Setup", test_basic_setup),
        ("Add Documents", test_add_documents),
        ("RAG Analysis", test_rag_analysis),
    ]

    results = []
    for name, test_func in tests:
        success = test_func()
        results.append((name, success))

    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    for name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{name}: {status}")

    all_passed = all(success for _, success in results)
    if all_passed:
        print("\n🎉 All tests passed! RAG system is ready.")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")

    return all_passed


if __name__ == "__main__":
    run_all_tests()
