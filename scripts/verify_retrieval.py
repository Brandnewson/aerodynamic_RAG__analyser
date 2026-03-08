"""Quick verification script — test ChromaDB retrieval quality.

Usage:
    uv run python scripts/verify_retrieval.py

This script:
1. Loads ChromaDB collection without needing FastAPI/SQLite.
2. Runs semantic queries against ingested aerodynamic papers.
3. Prints retrieved chunks + metadata so you can inspect quality.
4. Helps you decide if chunk size, overlap, or embedding model need tuning.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.infrastructure.vector_store import vector_store


EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_embedding_model = None


def _get_embedding_model():
    global _embedding_model  # noqa: PLW0603
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        print(f"[verify] Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _embed_query(query: str) -> list[float]:
    model = _get_embedding_model()
    embedding = model.encode([query], show_progress_bar=False)
    return embedding[0].tolist()


# Test queries — aerodynamic concepts that should retrieve relevant papers
TEST_QUERIES = [
    "ground effect aerodynamics diffuser design",
    "wing downforce vortex interaction",
    "drag reduction bluff body flow separation",
    "CFD turbulence modeling RANS LES",
    "airfoil design lift coefficient",
    "boundary layer separation stall",
]


def verify_retrieval(top_k: int = 5):
    """Run test queries and display results."""
    
    print("\n" + "=" * 80)
    print("CHROMADB RETRIEVAL VERIFICATION")
    print("=" * 80)
    
    # Show collection stats
    count = vector_store.count()
    print(f"\n✓ Collection: {vector_store.collection_name()}")
    print(f"✓ Total chunks: {count}")
    print(f"✓ Retrieving top-{top_k} results per query\n")
    
    # Run each test query
    for i, query in enumerate(TEST_QUERIES, 1):
        print("\n" + "-" * 80)
        print(f"QUERY {i}: {query}")
        print("-" * 80)
        
        # Retrieve from ChromaDB
        results = vector_store.query(
            query_embedding=_embed_query(query),
            top_k=top_k,
        )
        
        # Unpack results
        if results:
            for rank, item in enumerate(results, 1):
                doc = item.get("document", "")
                meta = item.get("metadata") or {}
                distance = float(item.get("distance", 1.0))
                similarity = max(0.0, 1.0 - distance)

                arxiv_id = meta.get("arxiv_id", "unknown")
                title = meta.get("title", "Untitled")
                authors = meta.get("authors", "Unknown")
                chunk_idx = meta.get("chunk_index", 0)

                print(f"\n  [{rank}] {title}")
                print(f"      arXiv: {arxiv_id} | Authors: {authors}")
                print(f"      Chunk: {chunk_idx} | Similarity: {similarity:.3f}")
                print(f"      Text: {doc[:150]}...")
        else:
            print("  ✗ No results returned")


def interactive_query():
    """Allow user to enter custom queries interactively."""
    
    print("\n" + "=" * 80)
    print("INTERACTIVE QUERY MODE")
    print("=" * 80)
    print("\nEnter aerodynamic queries to test retrieval quality.")
    print("(Type 'exit' to quit)\n")
    
    count = vector_store.count()
    print(f"✓ Collection has {count} chunks available.\n")
    
    while True:
        query = input("Query> ").strip()
        
        if query.lower() in ("exit", "quit", "q"):
            print("Exiting.")
            break
        
        if not query:
            print("  (empty query, try again)")
            continue
        
        # Retrieve
        results = vector_store.query(
            query_embedding=_embed_query(query),
            top_k=5,
        )
        
        if results:
            print(f"\n  [Retrieved {len(results)} chunks]\n")

            for rank, item in enumerate(results, 1):
                doc = item.get("document", "")
                meta = item.get("metadata") or {}
                distance = float(item.get("distance", 1.0))
                similarity = max(0.0, 1.0 - distance)
                title = meta.get("title", "Untitled")
                arxiv_id = meta.get("arxiv_id", "?")

                print(f"  [{rank}] ({similarity:.3f}) {title} [{arxiv_id}]")
                print(f"      {doc[:120]}...\n")
        else:
            print("  (no results)")
        
        print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify ChromaDB retrieval quality"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Enter interactive query mode"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of results to retrieve per query (default: 5)"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        interactive_query()
    else:
        verify_retrieval(top_k=args.top_k)