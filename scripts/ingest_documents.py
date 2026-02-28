"""Document ingestion script — loads aerodynamic literature into ChromaDB.

This script is the *data engineering* step that must be run once before
the RAG evaluation pipeline can operate.  It is deterministic and
idempotent (re-running it upserts rather than duplicates).

Usage:
    # 1. Fetch papers first
    uv run python scripts/fetch_papers.py

    # 2. Then ingest into ChromaDB
    uv run python scripts/ingest_documents.py

Expected input layout (populated by fetch_papers.py):
    data/
    └── raw/
        ├── 2301.12345v2.pdf
        ├── manifest.json          ← rich metadata keyed by arxiv_id
        └── ...

Pipeline:
    1. Load manifest.json for rich metadata (title, authors, abstract, …).
    2. Discover PDF / TXT / CSV files under --data-dir.
    3. Extract and clean text (pypdf for PDFs).
    4. Chunk text into overlapping character windows.
    5. Embed each chunk with SentenceTransformers (local, free, no API cost).
    6. Upsert vectors + metadata into ChromaDB (idempotent — safe to re-run).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Ensure project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402 (import after sys.path)
from app.infrastructure.vector_store import vector_store  # noqa: E402


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
MANIFEST_FILENAME = "manifest.json"

CHUNK_SIZE = 512        # characters per chunk
CHUNK_OVERLAP = 64      # overlap between consecutive chunks

# SentenceTransformer model — small, fast, 384-dim vectors, runs fully locally
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Manifest loader
# ---------------------------------------------------------------------------


def load_manifest(data_dir: Path) -> dict[str, dict]:
    """Load the manifest written by fetch_papers.py.

    Returns an empty dict gracefully if no manifest exists yet (e.g. when
    ingesting hand-placed PDFs that were not fetched via the fetch script).
    """
    manifest_path = data_dir / MANIFEST_FILENAME
    if manifest_path.exists():
        try:
            return json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[ingest] WARNING: could not parse manifest: {exc}")
    return {}


def _manifest_entry_for_file(filename: str, manifest: dict[str, dict]) -> dict:
    """Look up manifest metadata by filename. Returns empty dict if not found."""
    for entry in manifest.values():
        if entry.get("filename") == filename:
            return entry
    return {}


# ---------------------------------------------------------------------------
# Step 1: Discover source files
# ---------------------------------------------------------------------------


def discover_files(data_dir: Path, extensions: tuple[str, ...] = (".pdf", ".txt", ".csv")) -> list[Path]:
    """Return all files with the given extensions under ``data_dir``."""
    if not data_dir.exists():
        print(f"[ingest] Data directory not found: {data_dir}")
        print("[ingest] Create the directory and place your source documents there.")
        return []

    files = [f for ext in extensions for f in data_dir.rglob(f"*{ext}")]
    print(f"[ingest] Found {len(files)} source file(s) in {data_dir}")
    return sorted(files)


# ---------------------------------------------------------------------------
# Step 2: Extract text (stubs — implement per format in Phase 3)
# ---------------------------------------------------------------------------


def extract_text_from_file(path: Path) -> str:
    """Dispatch to the correct extractor based on file extension."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _extract_pdf(path)
    elif suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    elif suffix == ".csv":
        return _extract_csv(path)
    else:
        print(f"[ingest] Unsupported file type: {path.name} — skipping")
        return ""


def _extract_pdf(path: Path) -> str:
    """Extract all text from a PDF using pypdf.

    Pages with no extractable text (e.g. scanned images without OCR)
    are silently skipped.  The page number is prepended to each page's
    text so chunk metadata can reference the source page later.
    """
    try:
        import pypdf  # noqa: PLC0415 — lazy import to keep startup fast
    except ImportError:
        print("[ingest] ERROR: pypdf is not installed. Run: uv add pypdf")
        return ""

    pages: list[str] = []
    try:
        reader = pypdf.PdfReader(str(path))
        for i, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = _clean_text(text)
            if text.strip():
                pages.append(f"[Page {i}]\n{text}")
    except Exception as exc:
        print(f"[ingest]   ERROR reading PDF {path.name}: {exc}")
        return ""

    return "\n\n".join(pages)


def _clean_text(text: str) -> str:
    """Normalise whitespace and strip arXiv boilerplate artefacts."""
    # Collapse runs of whitespace / form-feeds into single spaces
    text = re.sub(r"[\x0c\r]", "\n", text)
    text = re.sub(r" {2,}", " ", text)
    # Remove lines that are purely page numbers or separators
    lines = [ln for ln in text.splitlines() if not re.fullmatch(r"\s*\d+\s*", ln)]
    return "\n".join(lines)


def _extract_csv(path: Path) -> str:
    """Concatenate all string-typed cells in a CSV into a single text blob."""
    import csv  # stdlib — always available

    rows: list[str] = []
    try:
        with path.open(encoding="utf-8", errors="ignore", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                # Join all non-empty string fields; skip pure numeric cells
                parts = [
                    v.strip()
                    for v in row.values()
                    if isinstance(v, str) and v.strip() and not v.strip().lstrip("-").replace(".", "").isdigit()
                ]
                if parts:
                    rows.append(" | ".join(parts))
    except Exception as exc:
        print(f"[ingest]   ERROR reading CSV {path.name}: {exc}")
        return ""

    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Step 3: Chunking
# ---------------------------------------------------------------------------


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character-level windows."""
    if not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return [c.strip() for c in chunks if c.strip()]


# ---------------------------------------------------------------------------
# Step 4 + 5: Embed and upsert
# ---------------------------------------------------------------------------


# Module-level cache so the model is loaded once per script run
_embedding_model = None


def _get_embedding_model():
    global _embedding_model  # noqa: PLW0603
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415
        print(f"[ingest] Loading embedding model: {EMBEDDING_MODEL} (first run may download weights)")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def embed_chunks(chunks: list[str]) -> list[list[float]]:
    """Return embedding vectors for each chunk using SentenceTransformers.

    Uses ``all-MiniLM-L6-v2``: 384-dimensional, ~80 MB download, runs
    entirely locally — no API key or internet required at ingest time.
    """
    model = _get_embedding_model()
    embeddings = model.encode(chunks, show_progress_bar=True, batch_size=32)
    return embeddings.tolist()


def ingest_file(path: Path, source_id: str, manifest_entry: dict) -> int:
    """Extract, chunk, embed, and upsert a single file. Returns chunk count.

    Args:
        path:           Path to the source file.
        source_id:      Stable slug used to namespace chunk IDs in ChromaDB.
        manifest_entry: Metadata dict from manifest.json (may be empty for
                        hand-placed files not fetched via fetch_papers.py).
    """
    text = extract_text_from_file(path)
    if not text:
        return 0

    chunks = chunk_text(text)
    if not chunks:
        return 0

    embeddings = embed_chunks(chunks)

    ids = [f"{source_id}::chunk::{i}" for i in range(len(chunks))]

    # Build per-chunk metadata — include all manifest fields so the RAG
    # service can surface paper title/authors alongside retrieved passages.
    base_meta: dict = {
        "source": path.name,
        "source_id": source_id,
        # Rich metadata from the fetch manifest (empty strings if not present)
        "title": manifest_entry.get("title", ""),
        "authors": ", ".join(manifest_entry.get("authors", [])),
        "published": manifest_entry.get("published", ""),
        "arxiv_id": manifest_entry.get("arxiv_id", ""),
        "abstract": manifest_entry.get("abstract", "")[:500],  # cap length
        "categories": ", ".join(manifest_entry.get("categories", [])),
    }
    metadatas = [{**base_meta, "chunk_index": i} for i in range(len(chunks))]

    vector_store.add_documents(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(data_dir: Path) -> None:
    print(f"[ingest] ChromaDB collection : {settings.CHROMA_COLLECTION_NAME}")
    print(f"[ingest] Persist directory  : {settings.CHROMA_PERSIST_DIR}")
    print(f"[ingest] Scanning           : {data_dir}")

    manifest = load_manifest(data_dir)
    print(f"[ingest] Manifest entries   : {len(manifest)}\n")

    files = discover_files(data_dir)
    if not files:
        print("[ingest] No files to ingest.")
        print("[ingest] Tip: run  uv run python scripts/fetch_papers.py  first.")
        return

    total_chunks = 0
    for path in files:
        source_id = path.stem.replace(" ", "_").lower()
        manifest_entry = _manifest_entry_for_file(path.name, manifest)
        label = manifest_entry.get("title") or path.name
        print(f"[ingest] Processing: {label[:80]}")
        n = ingest_file(path, source_id, manifest_entry)
        print(f"[ingest]   → {n} chunks ingested")
        total_chunks += n

    print(f"\n[ingest] Done. {total_chunks} total chunks in collection.")
    print(f"[ingest] Collection size: {vector_store.count()} documents.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest aerodynamic literature into ChromaDB.")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Path to the directory containing source documents (default: {DEFAULT_DATA_DIR})",
    )
    args = parser.parse_args()
    main(data_dir=args.data_dir)
