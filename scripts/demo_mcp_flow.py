"""Demo script showing MCP tool agent workflow.

This script demonstrates the MCP integration end-to-end:
  1. Create a new aerodynamic concept
  2. Trigger RAG evaluation
  3. Retrieve stored evaluation with citations

Run with:
    uv run python scripts/demo_mcp_flow.py
"""

from __future__ import annotations

import sys
import time

from app.mcp.tool_service import MCPToolService


def print_section(title: str) -> None:
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70)


def main() -> None:
    print_section("MCP AGENT WORKFLOW DEMONSTRATION")
    print("AeroInsight RAG MCP Server - End-to-End Tool Invocation")
    
    service = MCPToolService()
    
    # Step 1: List existing concepts (should start empty or show existing)
    print_section("STEP 1: list_concepts")
    print("Listing existing concepts...")
    
    initial_list = service.list_concepts(status="SUBMITTED", page=1, page_size=10)
    print(f"✓ Found {initial_list['total']} existing SUBMITTED concepts")
    
    # Step 2: Create a new concept
    print_section("STEP 2: create_concept")
    print("Creating test aerodynamic concept via MCP tool...")
    
    concept = service.create_concept(
        title="Agent-driven dynamic rear flap",
        description=(
            "An agentic control system for real-time rear flap adjustment based on "
            "yaw angle sensors and predictive corner analysis. Uses reinforcement "
            "learning to optimize downforce-drag balance lap-by-lap during qualifying."
        ),
        author="MCP Demo Agent",
        tags=["active-aero", "machine-learning", "rear-wing"],
    )
    
    concept_id = concept["id"]
    print(f"✓ Created concept ID={concept_id}: {concept['title']}")
    print(f"  Status: {concept['status']}")
    print(f"  Author: {concept['author']}")
    print(f"  Tags: {', '.join(concept['tags'])}")
    
    # Step 3: Evaluate the concept (triggers RAG pipeline)
    print_section("STEP 3: evaluate_concept")
    print(f"Triggering RAG evaluation for concept_id={concept_id}...")
    print("(This step embeds description → queries ChromaDB → calls GPT-4o)")
    
    start_time = time.time()
    
    try:
        evaluation = service.evaluate_concept(concept_id=concept_id)
        elapsed = time.time() - start_time
        
        print(f"✓ Evaluation completed in {elapsed:.2f}s")
        print(f"\n  NOVELTY SCORE:    {evaluation['novelty_score']:.2f}")
        print(f"  CONFIDENCE SCORE: {evaluation['confidence_score']:.2f}")
        print(f"\n  Mechanisms:")
        for mechanism in evaluation['mechanisms']:
            print(f"    • {mechanism}")
        
        print(f"\n  Regulatory Flags:")
        if evaluation['regulatory_flags']:
            for flag in evaluation['regulatory_flags']:
                print(f"    ⚠ {flag}")
        else:
            print("    (none identified)")
        
        print(f"\n  Similar References:")
        for ref in evaluation['similar_references'][:3]:
            print(f"    • {ref['title']} (similarity: {ref['similarity_score']:.2f})")
        
        print(f"\n  Existing Implementations:")
        if evaluation['existing_implementations']:
            for impl in evaluation['existing_implementations']:
                print(f"    🏎 {impl}")
        else:
            print("    (no known implementations)")
        
        print(f"\n  Retrieved Literature Context: {len(evaluation['retrieved_context'])} chunks")
        if evaluation['retrieved_context']:
            first_chunk = evaluation['retrieved_context'][0]
            print(f"    Example citation:")
            print(f"      Title: {first_chunk['citation']['title']}")
            print(f"      arXiv: {first_chunk['citation']['arxiv_id']}")
            print(f"      Similarity: {first_chunk['similarity_score']:.2f}")
    
    except Exception as e:
        print(f"✗ Evaluation failed: {e}")
        sys.exit(1)
    
    # Step 4: Re-fetch the evaluation (demonstrates GET endpoint)
    print_section("STEP 4: get_evaluation")
    print(f"Fetching stored evaluation for concept_id={concept_id}...")
    
    fetched = service.get_evaluation(concept_id=concept_id)
    print(f"✓ Retrieved evaluation ID={fetched['id']}")
    print(f"  Novelty: {fetched['novelty_score']:.2f}")
    print(f"  Confidence: {fetched['confidence_score']:.2f}")
    print(f"  Retrieved context chunks: {len(fetched['retrieved_context'])}")
    
    # Summary
    print_section("WORKFLOW COMPLETE")
    print("MCP tools successfully demonstrated full RAG evaluation pipeline:")
    print(f"  ✓ list_concepts - paginated concept retrieval")
    print(f"  ✓ create_concept - concept creation with validation")
    print(f"  ✓ evaluate_concept - RAG pipeline execution")
    print(f"  ✓ get_evaluation - cached evaluation retrieval")
    print(f"\nConcept ID {concept_id} is now available for inspection via REST or MCP.")


if __name__ == "__main__":
    main()
