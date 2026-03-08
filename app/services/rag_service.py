"""RAGService — orchestrates retrieval and LLM evaluation.

This service implements the full RAG pipeline:
  1. Embed the concept description using SentenceTransformers
  2. Retrieve top-k similar chunks from ChromaDB
  3. Build a structured prompt with retrieved context
  4. Call OpenAI for structured evaluation
  5. Parse response and persist evaluation

The embedding model MUST match the one used in ingest_documents.py
to ensure query and document vectors live in the same semantic space.
"""

from __future__ import annotations

import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.models import AeroConcept, ConceptEvaluation, ConceptStatus
from app.domain.schemas import Citation, EvaluationResponse, RetrievedChunk, SimilarReference
from app.infrastructure.llm_client import get_llm_client
from app.infrastructure.vector_store import vector_store

logger = logging.getLogger(__name__)

# Must match the model in ingest_documents.py
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_embedding_model = None


def _get_embedding_model():
    """Lazy-load the SentenceTransformer model (singleton pattern)."""
    global _embedding_model  # noqa: PLW0603
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer  # noqa: PLC0415

        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _embed_text(text: str) -> list[float]:
    """Embed a single text string into a vector."""
    model = _get_embedding_model()
    embedding = model.encode([text], show_progress_bar=False)
    return embedding[0].tolist()


def _build_citation(metadata: dict) -> Citation:
    """Build a Citation object from ChromaDB chunk metadata."""
    arxiv_id = metadata.get("arxiv_id") or None
    return Citation(
        arxiv_id=arxiv_id,
        title=metadata.get("title", "Unknown"),
        authors=metadata.get("authors", "Unknown"),
        published=metadata.get("published"),
        url=f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else None,
    )


class RAGService:
    """Coordinates embedding, retrieval, prompting, and result persistence."""

    def evaluate_concept(
        self, db: Session, concept: AeroConcept
    ) -> tuple[ConceptEvaluation, list[RetrievedChunk]]:
        """Generate a structured evaluation for the given concept.

        Workflow:
          1. Embed concept.description via SentenceTransformers
          2. Query ChromaDB for top-k similar literature chunks
          3. Build a structured prompt from the chunks
          4. Call OpenAI API and parse the JSON response
          5. Persist the evaluation and update concept status

        Returns:
            Tuple of (evaluation, retrieved_chunks) for proper API response
        """
        logger.info(f"Starting RAG evaluation for concept_id={concept.id}")

        # Step 1: Embed the concept description
        query_embedding = _embed_text(concept.description)

        # Step 2: Retrieve similar chunks from ChromaDB
        top_k = settings.RETRIEVAL_TOP_K
        chunks = vector_store.query(query_embedding=query_embedding, top_k=top_k)
        logger.info(f"Retrieved {len(chunks)} chunks from ChromaDB")

        if not chunks:
            logger.warning("No chunks retrieved — ChromaDB may be empty")

        # Step 3: Build the prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(concept, chunks)

        # Step 4: Call LLM
        try:
            llm_client = get_llm_client()
            response = llm_client.chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.2,
                max_tokens=2048,
            )
            logger.info(f"LLM response received, length: {len(response) if response else 0}")

            # Parse JSON response
            if not response or not response.strip():
                raise ValueError(f"LLM returned empty response")
            
            # Strip markdown code fences if present (GPT-4 sometimes wraps JSON in ```json ... ```)
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]  # Remove ```json
            elif response_clean.startswith("```"):
                response_clean = response_clean[3:]  # Remove ```
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]  # Remove trailing ```
            response_clean = response_clean.strip()
            
            parsed = json.loads(response_clean)
            logger.info("LLM response parsed successfully")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.error(f"Raw response: {response[:500] if response else 'EMPTY'}")
            raise ValueError(f"LLM returned invalid JSON: {e}. Response: {response[:200] if response else 'EMPTY'}") from e
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

        # Step 5: Build evaluation model and persist
        evaluation = self._build_evaluation(
            concept=concept,
            parsed_response=parsed,
            chunks=chunks,
            raw_llm_response=response,
        )

        db.add(evaluation)
        concept.status = ConceptStatus.ANALYSED
        db.commit()
        db.refresh(evaluation)

        # Build retrieved chunks for API response
        retrieved_chunks = self._build_retrieved_chunks(chunks)

        logger.info(f"Evaluation persisted for concept_id={concept.id}")
        return evaluation, retrieved_chunks

    def _build_system_prompt(self) -> str:
        """System prompt that defines the LLM's role and output format."""
        return """You are an expert aerodynamics researcher analyzing novel aerodynamic concepts.

Your task is to evaluate a proposed concept against retrieved academic literature and provide a structured assessment.

Output ONLY valid JSON matching this schema:
{
  "novelty_score": <float 0.0-1.0>,
  "confidence_score": <float 0.0-1.0>,
  "mechanisms": [<string>, ...],
  "tradeoffs": {<key>: <value>, ...},
  "regulatory_flags": [<string>, ...],
  "similar_references": [{"title": <string>, "similarity_score": <float>}, ...],
  "existing_implementations": [<string>, ...]
}

CRITICAL GUIDELINES:

**novelty_score** (0.0-1.0):
- How novel/original is this concept compared to existing literature?
- 0.9-1.0: Genuinely new approach, no clear precedent in literature
- 0.7-0.9: Novel combination or application, some existing components
- 0.5-0.7: Incremental improvement on existing concepts
- 0.2-0.5: Minor variation on established techniques
- 0.0-0.2: Clear precedent exists in literature

**confidence_score** (0.0-1.0):
- How confident are you in this assessment? MUST reflect uncertainty!
- 0.9-1.0: Strong academic literature support, clear precedent or clear innovation
- 0.7-0.9: Good literature support, some gaps remain
- 0.5-0.7: Mixed evidence, some key aspects unclear from retrieved papers
- 0.3-0.5: Limited literature coverage, significant gaps in understanding concept
- 0.0-0.3: Very little information available, high uncertainty in assessment

IMPORTANT: Low confidence (0.3-0.6) is EXPECTED when literature is sparse or concept poorly defined!

**regulatory_flags** [<string>, ...]:
- Specific FIA/motorsport regulation concerns (NOT vague)
- List ACTUAL rules, years, and impact
- Examples:
  * "Violates 2024 F1 Technical Regulation 10.2.2 (wing angle limits)"
  * "May exceed DRS deployment height restriction (2023 FIA rules)"
  * "Potential safety concern: structural loading in 50g crash"
  * "Compatible with current Super Formula regulations"
- DO NOT just say "FIA regulations" - be specific!
- If no specific regulatory issue identified, use a well-thought out reasonable list of where the regulatory flags might come in.

**existing_implementations** [<string>, ...]:
- Real-world examples from F1, speedway, motorsport, or aerodynamic applications
- Identify SPECIFIC team/vehicle implementations
- Examples:
  * "Mercedes W15 (2024) - DRS flap angle variation"
  * "Red Bull RB20 - active suspension control"
  * "Ferrari SF-24 - F-duct inlet placement (revival of 2010 concept)"
  * "Porsche 911 GT3 RS - gurney flap on rear wing"
- Only include if literature or general knowledge supports implementation
- If no known implementations, use empty array

Be concise but technically precise. Return ONLY the JSON, no markdown or commentary."""

    def _build_user_prompt(self, concept: AeroConcept, chunks: list[dict]) -> str:
        """User prompt with concept details and retrieved literature context."""
        prompt = f"""# Concept to Evaluate

**Title:** {concept.title}

**Description:**
{concept.description}

**Author:** {concept.author or "Anonymous"}

**Tags:** {", ".join(concept.tags) if concept.tags else "None"}

---

# Retrieved Literature Context

The following passages were retrieved from academic papers based on semantic similarity:

"""
        for i, chunk in enumerate(chunks, 1):
            meta = chunk.get("metadata", {})
            doc = chunk.get("document", "")
            distance = chunk.get("distance", 1.0)
            similarity = max(0.0, 1.0 - distance)

            title = meta.get("title", "Unknown")
            authors = meta.get("authors", "Unknown")
            arxiv_id = meta.get("arxiv_id", "")

            prompt += f"""
**[{i}] {title}**
- Authors: {authors}
- arXiv: {arxiv_id}
- Similarity: {similarity:.3f}
- Excerpt: {doc[:300]}{"..." if len(doc) > 300 else ""}

"""

        prompt += """---

Now provide your structured evaluation as JSON."""
        return prompt

    def _build_evaluation(
        self,
        concept: AeroConcept,
        parsed_response: dict,
        chunks: list[dict],
        raw_llm_response: str,
    ) -> ConceptEvaluation:
        """Build the ConceptEvaluation ORM model from parsed LLM response."""
        # Extract and validate core fields
        novelty_score = float(parsed_response.get("novelty_score", 0.0))
        confidence_score = float(parsed_response.get("confidence_score", 0.0))

        # Clamp scores to valid range
        novelty_score = max(0.0, min(1.0, novelty_score))
        confidence_score = max(0.0, min(1.0, confidence_score))

        mechanisms = parsed_response.get("mechanisms", [])
        tradeoffs = parsed_response.get("tradeoffs", {})
        regulatory_flags = parsed_response.get("regulatory_flags", [])
        similar_refs = parsed_response.get("similar_references", [])
        existing_implementations = parsed_response.get("existing_implementations", [])

        # Convert similar_references from LLM to SimilarReference schema
        similar_references = []
        for ref in similar_refs[:3]:  # Limit to top 3
            if isinstance(ref, dict) and "title" in ref:
                similar_references.append(
                    {
                        "title": ref["title"],
                        "similarity_score": max(0.0, min(1.0, ref.get("similarity_score", 0.0))),
                    }
                )

        return ConceptEvaluation(
            concept_id=concept.id,
            novelty_score=novelty_score,
            confidence_score=confidence_score,
            mechanisms=mechanisms,
            tradeoffs=tradeoffs,
            regulatory_flags=regulatory_flags,
            similar_references=similar_references,
            existing_implementations=existing_implementations,
            llm_raw_response=raw_llm_response,
        )

    def _build_retrieved_chunks(self, chunks: list[dict]) -> list[RetrievedChunk]:
        """Convert ChromaDB results into RetrievedChunk schema objects."""
        retrieved = []
        for chunk in chunks:
            meta = chunk.get("metadata", {})
            doc = chunk.get("document", "")
            distance = chunk.get("distance", 1.0)
            similarity = max(0.0, 1.0 - distance)

            citation = _build_citation(meta)
            chunk_index = meta.get("chunk_index", 0)

            retrieved.append(
                RetrievedChunk(
                    text=doc,
                    chunk_index=chunk_index,
                    similarity_score=similarity,
                    citation=citation,
                )
            )
        return retrieved

    def get_retrieved_context_for_concept(self, concept: AeroConcept) -> list[RetrievedChunk]:
        """Re-fetch retrieved context for a concept (used when viewing cached evaluations).
        
        This allows the GET /evaluation endpoint to show the same literature context
        that was used during the original evaluation, without persisting it in the database.
        """
        logger.info(f"Re-fetching retrieved context for concept_id={concept.id}")
        
        # Embed the concept description
        query_embedding = _embed_text(concept.description)
        
        # Query ChromaDB for similar chunks (same logic as during evaluation)
        top_k = settings.RETRIEVAL_TOP_K
        chunks = vector_store.query(query_embedding=query_embedding, top_k=top_k)
        
        # Build and return retrieved chunks
        return self._build_retrieved_chunks(chunks)


# Module-level singleton
rag_service = RAGService()
