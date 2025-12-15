# ValueKit RAG System

RAG (Retrieval-Augmented Generation) System für quantitative Value-Investing Analysen.

## Tech Stack

- **LangChain**: RAG Framework
- **ChromaDB**: Vector Database (local persistence)
- **Claude Sonnet 4.5**: LLM für Analysen
- **Voyage AI**: Financial-specialized Embeddings

## Setup

### 1. Dependencies installieren

```bash
cd backend
pip install langchain langchain-anthropic chromadb voyageai anthropic python-dotenv --break-system-packages
```

### 2. API Keys in secrets.toml

```toml
[anthropic]
api_key = "sk-ant-xxxxx"

[voyage]
api_key = "pa-xxxxx"
```

### 3. File Struktur

```
backend/ai/
├── config.py           # Konfiguration
├── vector_store.py     # ChromaDB + Voyage Embeddings
├── rag_service.py      # Main RAG Service
├── test_rag.py         # Test Suite
└── data/
    └── chroma_db/      # Vector DB (auto-created)
```

## Usage

### Test System

```bash
cd backend/ai
python test_rag.py
```

### In deinem Code verwenden

```python
from rag_service import get_rag_service

# Initialize
rag = get_rag_service()

# Add financial documents
docs = [
    {
        "text": "Apple Q4 earnings...",
        "metadata": {
            "company": "Apple Inc.",
            "ticker": "AAPL",
            "document_type": "earnings_report"
        }
    }
]
rag.add_financial_documents(docs)

# Perform analysis with quantitative data
result = rag.analyze_with_rag(
    query="Should I invest in AAPL?",
    quantitative_data={
        "dcf": {"intrinsic_value": 195.50, "current_price": 175.20},
        "roic": "45.2%",
        "margin_of_safety": "11.6%"
    }
)

print(result["analysis"])
```

## Key Features

### Quantitative-First Approach

- DCF, ROIC, Margin of Safety sind PRIMARY decision factors
- Qualitative info aus RAG ist SUPPORTING, nicht dominant

### Financial-Specialized

- Voyage Finance-2 Embeddings optimiert für Financial Documents
- Chunking preserves numerical context
- Claude's precision for quantitative reasoning

### Use Cases für WIPRO

1. **Risk Factor Analysis**: "Was sind die Risiken bei Company X?"
2. **Qualitative Validation**: "Bestätigen earnings calls die DCF assumptions?"
3. **Competitive Analysis**: "Wie steht X vs Competitors?"
4. **Management Quality**: "Track record vom Management?"

## Kosten

- **Claude Sonnet 4.5**: ~$50-100 für ganzes WIPRO
- **Voyage AI**: ~$5-10 für Embeddings
- **Total**: ~$60-120 (weit unter $300 Budget)

## Next Steps

1. ✅ Setup testen mit `python test_rag.py`
2. Integration mit ValueKit API
3. Real financial data sources anbinden (10-K, earnings calls)
4. UI für RAG-enhanced analysis
5. Evaluation: Mit vs ohne RAG vergleichen

## Troubleshooting

**Import Errors**: Check ob alle packages installiert sind
**API Errors**: Verify secrets.toml keys
**ChromaDB Errors**: Delete `data/chroma_db/` und neu initialisieren
