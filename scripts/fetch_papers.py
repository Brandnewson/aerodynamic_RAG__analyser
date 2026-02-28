"""Fetch aerodynamic literature from arXiv and populate data/raw/.

This is the *data acquisition* step.  Run it once (or periodically) to
build/refresh the corpus that the ingestion script will embed into ChromaDB.

Usage:
    uv run python scripts/fetch_papers.py
    uv run python scripts/fetch_papers.py --max-per-query 10 --dry-run

What it does:
    1. Queries arXiv using a curated set of aerodynamics search terms.
    2. Downloads each paper's PDF to data/raw/<arxiv_id>.pdf.
    3. Writes / updates data/raw/manifest.json with rich metadata
       (title, authors, abstract, categories, published date) that the
       ingest script attaches to each ChromaDB chunk.
    4. Skips papers that are already present — fully idempotent.

arXiv API courtesy limits:
    The script enforces a 3-second delay between PDF downloads, as
    requested by arXiv's access policy:
    https://info.arxiv.org/help/robots.html
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root on sys.path when invoked directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import arxiv  # noqa: E402

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"
MANIFEST_FILENAME = "manifest.json"

# arXiv courtesy delay between HTTP requests (seconds)
ARXIV_RATE_LIMIT_S = 3.0

# ---------------------------------------------------------------------------
# Curated search queries
#
# Each entry is a dict with:
#   "query"    — arXiv search string (supports field prefixes like ti: ab:)
#   "category" — optional arXiv category filter (None = all physics/cs)
#   "label"    — human-readable label for logging
#
# Coverage targets:
#   • Fundamental aerodynamics (lift, drag, boundary layer)
#   • Computational methods (CFD, LES, RANS)
#   • Motorsport / vehicle aerodynamics
#   • Shape optimisation
#   • Experimental aerodynamics (wind tunnel, PIV)
# ---------------------------------------------------------------------------

SEARCH_QUERIES: list[dict] = [
    {
        "label": "Airfoil aerodynamics",
        "query": 'ti:(airfoil OR aerofoil) AND (abs:lift OR abs:drag OR abs:"boundary layer" OR abs:stall OR abs:transition)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Computational fluid dynamics turbulence",
        "query": 'ti:(turbulence OR turbulent) AND (abs:RANS OR abs:LES OR abs:DNS OR abs:"Reynolds stress" OR abs:k-epsilon OR abs:k-omega OR abs:SST)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Aerodynamic drag reduction",
        "query": '(abs:"drag reduction" OR abs:"reduced drag" OR abs:drag) AND (abs:aerodynamic OR abs:aerodynamics OR abs:vehicle OR abs:car)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Wing vortex downforce",
        "query": '(abs:wing OR abs:"inverted wing" OR abs:airfoil) AND (abs:vortex OR abs:downforce OR abs:wake OR abs:endplate OR abs:"tip vortex")',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Aerodynamic shape optimisation",
        "query": '(ti:(aerodynamic OR aerodynamics) OR abs:"shape optimization" OR abs:"shape optimisation") AND (ti:(optimization OR optimisation OR design) OR abs:adjoint OR abs:"gradient-based")',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Flow separation bluff body",
        "query": '(abs:"flow separation" OR abs:separation) AND (abs:"bluff body" OR abs:stall OR abs:recirculation OR abs:"reattachment" OR abs:"separation bubble")',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Ground effect vehicle aerodynamics",
        "query": '(abs:"ground effect" OR abs:ground-effect OR abs:"moving ground") AND (abs:vehicle OR abs:car OR abs:wing OR abs:diffuser OR abs:underbody)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Motorsport / racing car aerodynamics",
        "query": '(abs:"race car" OR abs:"racing car" OR abs:motorsport OR abs:"Formula One" OR abs:"Formula 1" OR abs:"Formula Student" OR abs:IndyCar OR abs:"sports prototype") AND (abs:aerodynamic OR abs:aerodynamics OR abs:downforce)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Wind tunnel experimental aerodynamics",
        "query": '(abs:"wind tunnel" OR abs:"moving belt" OR abs:"rolling road") AND (abs:vehicle OR abs:car OR abs:wing OR abs:underbody OR abs:"pressure coefficient" OR abs:PIV)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "CFD numerical methods applied aerodynamics",
        "query": '(abs:"Navier-Stokes" OR abs:"finite volume" OR abs:"finite element" OR abs:"discontinuous Galerkin" OR abs:"lattice Boltzmann") AND (abs:aerodynamic OR abs:aerodynamics OR abs:vehicle OR abs:car)',
        "category": "physics.flu-dyn",
    },

    # --- Added buckets for formula-car aero coverage ---

    {
        "label": "Underbody diffuser and venturi aerodynamics",
        "query": '(abs:diffuser OR abs:venturi OR abs:"underbody" OR abs:"under floor" OR abs:underfloor) AND (abs:downforce OR abs:suction OR abs:"pressure recovery" OR abs:"ride height")',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Front wing, endplates, and multi-element wings",
        "query": '(abs:"front wing" OR abs:"multi-element" OR abs:endplate OR abs:flap OR abs:slat) AND (abs:downforce OR abs:drag OR abs:vortex OR abs:wake)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Rear wing, beam wing, and wake interaction",
        "query": '(abs:"rear wing" OR abs:"beam wing" OR abs:spoiler) AND (abs:wake OR abs:"wake interaction" OR abs:downforce OR abs:drag OR abs:diffuser)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Vortex generators and flow control devices",
        "query": '(abs:"vortex generator" OR abs:VG OR abs:strake OR abs:canard OR abs:"leading edge extension") AND (abs:separation OR abs:reattachment OR abs:downforce OR abs:drag)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Boundary layer transition and surface effects",
        "query": '(abs:"boundary layer" OR abs:transition) AND (abs:roughness OR abs:"surface roughness" OR abs:tripping OR abs:"laminar-turbulent" OR abs:Reynolds)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Wheel aerodynamics and rotating wheels",
        "query": '(abs:wheel OR abs:tyre OR abs:tire OR abs:"rotating wheel" OR abs:"rolling wheel") AND (abs:drag OR abs:wake OR abs:downforce OR abs:ground)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Vehicle wake, base pressure, and bluff-body drag",
        "query": '(abs:wake OR abs:"base pressure" OR abs:"pressure drag") AND (abs:vehicle OR abs:car OR abs:"bluff body" OR abs:"Ahmed body")',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Yaw, crosswind, and aerodynamic stability",
        "query": '(abs:yaw OR abs:"crosswind" OR abs:"side force" OR abs:"aerodynamic stability") AND (abs:vehicle OR abs:car OR abs:downforce OR abs:wake)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Unsteady aerodynamics and transient effects",
        "query": '(abs:unsteady OR abs:transient OR abs:"dynamic stall" OR abs:"gust response") AND (abs:aerodynamic OR abs:aerodynamics OR abs:vehicle OR abs:wing)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Ride height, pitch, and heave sensitivity",
        "query": '(abs:"ride height" OR abs:pitch OR abs:heave OR abs:rake) AND (abs:downforce OR abs:"ground effect" OR abs:diffuser OR abs:underbody)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Cooling, ducting, and heat exchanger aerodynamics",
        "query": '(abs:cooling OR abs:duct OR abs:ducting OR abs:radiator OR abs:"heat exchanger" OR abs:"pressure loss") AND (abs:vehicle OR abs:car OR abs:aerodynamic OR abs:drag)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Active flow control and blowing/suction",
        "query": '(abs:"flow control" OR abs:blowing OR abs:suction OR abs:"synthetic jet" OR abs:"plasma actuator") AND (abs:separation OR abs:drag OR abs:lift OR abs:downforce)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Adjoint methods for aerodynamic optimisation",
        "query": '(abs:adjoint OR ti:adjoint) AND (abs:aerodynamic OR abs:aerodynamics OR abs:shape OR abs:optimization OR abs:optimisation)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Surrogate models and ML for aerodynamic prediction",
        "query": '(abs:"machine learning" OR abs:surrogate OR abs:"Gaussian process" OR abs:neural OR abs:"reduced-order") AND (abs:aerodynamic OR abs:aerodynamics OR abs:CFD)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Reduced-order modelling and wake models",
        "query": '(abs:"reduced-order" OR abs:ROM OR abs:"proper orthogonal decomposition" OR abs:POD OR abs:"dynamic mode decomposition" OR abs:DMD) AND (abs:wake OR abs:aerodynamic OR abs:vehicle)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Meshing, grid convergence, and CFD validation",
        "query": '(abs:mesh OR abs:meshing OR abs:"grid convergence" OR abs:"grid independence" OR abs:validation OR abs:verification) AND (abs:CFD OR abs:"Navier-Stokes" OR abs:aerodynamic)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Turbulence transition models for external aero",
        "query": '(abs:"transition model" OR abs:gamma-Re_theta OR abs:"intermittency" OR abs:"SST transition") AND (abs:RANS OR abs:CFD OR abs:aerodynamic)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Separated flows, vortices, and coherent structures",
        "query": '(abs:vortex OR abs:"coherent structure" OR abs:"shear layer" OR abs:"Kelvin-Helmholtz") AND (abs:separation OR abs:wake OR abs:vehicle OR abs:wing)',
        "category": "physics.flu-dyn",
    },
    {
        "label": "Noise and aeroacoustics (vehicle external flow)",
        "query": '(abs:aeroacoustic OR abs:"aerodynamic noise" OR abs:"flow-induced noise") AND (abs:vehicle OR abs:car OR abs:wing OR abs:wake)',
        "category": "physics.flu-dyn",
    },
]


# ---------------------------------------------------------------------------
# Manifest helpers
# ---------------------------------------------------------------------------


def load_manifest(data_dir: Path) -> dict[str, dict]:
    """Return the current manifest as ``{arxiv_id: metadata}``."""
    manifest_path = data_dir / MANIFEST_FILENAME
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {}


def save_manifest(data_dir: Path, manifest: dict[str, dict]) -> None:
    manifest_path = data_dir / MANIFEST_FILENAME
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _build_entry(result: arxiv.Result, filename: str) -> dict:
    """Convert an arxiv.Result into a manifest entry dict."""
    return {
        "arxiv_id": result.entry_id.split("/abs/")[-1],
        "title": result.title,
        "authors": [str(a) for a in result.authors],
        "abstract": result.summary,
        "published": result.published.isoformat() if result.published else None,
        "updated": result.updated.isoformat() if result.updated else None,
        "categories": result.categories,
        "journal_ref": result.journal_ref,
        "doi": result.doi,
        "primary_category": result.primary_category,
        "filename": filename,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Search + download
# ---------------------------------------------------------------------------


def search_query(
    label: str,
    query: str,
    category: str | None,
    max_results: int,
) -> list[arxiv.Result]:
    """Run a single arXiv query and return results."""
    # Build category filter string if specified
    full_query = query
    if category:
        full_query = f"cat:{category} AND ({query})"

    print(f"\n[fetch] 🔍  {label}")
    print(f"[fetch]     query   : {full_query}")

    search = arxiv.Search(
        query=full_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )

    client = arxiv.Client()
    results = list(client.results(search))
    print(f"[fetch]     results : {len(results)}")
    return results


def download_paper(
    result: arxiv.Result,
    data_dir: Path,
    manifest: dict[str, dict],
    dry_run: bool,
) -> bool:
    """Download a single paper PDF. Returns True if newly downloaded."""
    arxiv_id = result.entry_id.split("/abs/")[-1]
    # Sanitise the ID for use as a filename (replace "/" for versioned IDs
    # like "2301.12345v2" — keep the "v" suffix so re-runs don't collide)
    safe_id = arxiv_id.replace("/", "_")
    filename = f"{safe_id}.pdf"
    dest = data_dir / filename

    # Skip if already downloaded
    if arxiv_id in manifest:
        print(f"[fetch]   SKIP  {arxiv_id} — already in manifest")
        return False

    if dest.exists():
        # File present but not in manifest — add it without re-downloading
        print(f"[fetch]   INDEX {arxiv_id} — file exists, adding to manifest")
        manifest[arxiv_id] = _build_entry(result, filename)
        return False

    if dry_run:
        print(f"[fetch]   DRY   {arxiv_id}  {result.title[:70]}")
        return False

    try:
        print(f"[fetch]   GET   {arxiv_id}  {result.title[:60]}...")
        result.download_pdf(dirpath=str(data_dir), filename=filename)
        manifest[arxiv_id] = _build_entry(result, filename)
        print(f"[fetch]         → saved {filename}")
        return True
    except Exception as exc:
        print(f"[fetch]   ERROR downloading {arxiv_id}: {exc}")
        return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(
    data_dir: Path,
    max_per_query: int,
    dry_run: bool,
) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest(data_dir)

    print(f"[fetch] Data directory : {data_dir}")
    print(f"[fetch] Manifest size  : {len(manifest)} existing entries")
    print(f"[fetch] Max per query  : {max_per_query}")
    print(f"[fetch] Dry run        : {dry_run}")

    newly_downloaded = 0
    total_seen = 0

    for spec in SEARCH_QUERIES:
        results = search_query(
            label=spec["label"],
            query=spec["query"],
            category=spec.get("category"),
            max_results=max_per_query,
        )

        for result in results:
            total_seen += 1
            downloaded = download_paper(result, data_dir, manifest, dry_run)
            if downloaded:
                newly_downloaded += 1
                # Persist manifest after every successful download so partial
                # runs don't lose progress.
                save_manifest(data_dir, manifest)
                # Respect arXiv courtesy rate limit
                time.sleep(ARXIV_RATE_LIMIT_S)

    # Final manifest save (catch any index-only entries)
    if not dry_run:
        save_manifest(data_dir, manifest)

    print(f"\n[fetch] ─────────────────────────────────────────────────")
    print(f"[fetch] Total papers seen   : {total_seen}")
    print(f"[fetch] Newly downloaded    : {newly_downloaded}")
    print(f"[fetch] Manifest total      : {len(manifest)} papers")
    print(f"[fetch] Manifest location   : {data_dir / MANIFEST_FILENAME}")
    if dry_run:
        print("[fetch] (dry-run — no files written)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch aerodynamic arXiv papers into data/raw/."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help=f"Destination directory for PDFs and manifest (default: {DEFAULT_DATA_DIR})",
    )
    parser.add_argument(
        "--max-per-query",
        type=int,
        default=5,
        help="Maximum papers to fetch per search query (default: 5).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be downloaded without saving any files.",
    )
    args = parser.parse_args()
    main(
        data_dir=args.data_dir,
        max_per_query=args.max_per_query,
        dry_run=args.dry_run,
    )
