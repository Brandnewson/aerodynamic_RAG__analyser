# AeroInsight API Documentation

**Version:** 0.1.0  
**Base URL:** `http://localhost:8001/api/v1`  
**Interactive Documentation:** http://localhost:8001/docs

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Health & Discovery](#health--discovery)
   - [Concepts](#concepts)
   - [Evaluations](#evaluations)
5. [Data Models](#data-models)
6. [Examples](#examples)

---

## Overview

AeroInsight is a REST-based AI-augmented aerodynamic concept evaluation platform. Submit design ideas and receive structured, evidence-based analysis generated through Retrieval-Augmented Generation (RAG) over curated aerodynamic literature.

### Key Features

- **Concept Management**: Create, update, list, and delete aerodynamic concepts
- **RAG Evaluation**: AI-powered concept evaluation using GPT-4o and 31,652 chunks from 248 arXiv papers
- **Citation Tracking**: Every evaluation includes citations from retrieved research papers
- **MCP Integration**: Model Context Protocol support for agent-native workflows

---

## Authentication

**Current Version:** No authentication required (development mode)

**Production Considerations:**
- Future versions will support JWT-based authentication
- API keys for rate limiting
- OAuth2 for third-party integrations

---

## Error Handling

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Human-readable error message",
  "code": "machine_readable_error_code",
  "additional_context": "Optional extra information"
}
```

### HTTP Status Codes

| Code | Meaning | When it occurs |
|------|---------|----------------|
| **200** | OK | Successful GET request |
| **201** | Created | Successful POST request creating a resource |
| **202** | Accepted | Request accepted, processing started |
| **204** | No Content | Successful DELETE request |
| **400** | Bad Request | Invalid request syntax |
| **404** | Not Found | Resource does not exist |
| **409** | Conflict | Resource already exists (e.g., duplicate evaluation) |
| **422** | Unprocessable Entity | Validation error (invalid data types, missing fields) |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Unexpected server error |
| **503** | Service Unavailable | External service (ChromaDB, OpenAI) unavailable |

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `concept_not_found` | 404 | Concept with specified ID does not exist |
| `evaluation_not_found` | 404 | Evaluation for concept does not exist |
| `evaluation_exists` | 409 | Concept already has an evaluation |
| `validation_error` | 422 | Input validation failed |
| `vector_store_error` | 503 | ChromaDB unavailable or query failed |
| `llm_service_error` | 503 | OpenAI API unavailable or request failed |
| `database_error` | 500 | Database operation failed |
| `rate_limit_error` | 429 | Too many requests |

### Example Error Responses

**404 Not Found:**
```json
{
  "detail": "Concept with id 999 not found",
  "code": "concept_not_found",
  "concept_id": 999
}
```

**409 Conflict:**
```json
{
  "detail": "Concept 123 already has an evaluation",
  "code": "evaluation_exists",
  "concept_id": 123
}
```

**422 Validation Error:**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "description"],
      "msg": "String should have at least 20 characters",
      "input": "Too short"
    }
  ]
}
```

---

## Endpoints

### Health & Discovery

#### GET /health

Check API health and system status.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "database": "connected",
  "vector_store": "connected"
}
```

**Example Request:**
```bash
curl http://localhost:8001/api/v1/health
```

---

#### GET /mcp

Discover available MCP (Model Context Protocol) tools.

**Response:** `200 OK`

```json
{
  "tools": [
    {
      "name": "list_concepts",
      "description": "List aerodynamic concepts with optional filtering"
    },
    {
      "name": "create_concept",
      "description": "Create a new aerodynamic concept"
    },
    {
      "name": "evaluate_concept",
      "description": "Trigger RAG evaluation for a concept"
    },
    {
      "name": "get_evaluation",
      "description": "Retrieve stored evaluation results"
    }
  ]
}
```

**Example Request:**
```bash
curl http://localhost:8001/api/v1/mcp
```

---

### Concepts

#### POST /concepts

Create a new aerodynamic concept.

**Request Body:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | ✅ | 3-255 chars | Short descriptive title |
| `description` | string | ✅ | 20+ chars | Detailed concept description |
| `author` | string | ❌ | max 255 chars | Submitter name |
| `tags` | array[string] | ❌ | - | Taxonomy tags |

**Response:** `201 Created`

```json
{
  "id": 1,
  "title": "Ground effect diffuser with active flow control",
  "description": "A ground effect diffuser that uses active flow control via synthetic jets to delay separation and increase downforce efficiency in low-speed corners.",
  "status": "SUBMITTED",
  "author": "Dr. Jane Smith",
  "tags": ["ground-effect", "active-aero", "diffuser"],
  "created_at": "2026-03-08T10:30:00Z",
  "updated_at": "2026-03-08T10:30:00Z"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8001/api/v1/concepts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Ground effect diffuser with active flow control",
    "description": "A ground effect diffuser that uses active flow control via synthetic jets to delay separation and increase downforce efficiency in low-speed corners. The system dynamically adjusts jet frequency based on ride height sensors.",
    "author": "Dr. Jane Smith",
    "tags": ["ground-effect", "active-aero", "diffuser"]
  }'
```

**Possible Errors:**
- `422` - Validation error (title too short, description missing, etc.)

---

#### GET /concepts

List concepts with optional filtering and pagination.

**Query Parameters:**

| Parameter | Type | Required | Default | Constraints | Description |
|-----------|------|----------|---------|-------------|-------------|
| `status` | string | ❌ | - | SUBMITTED \| ANALYSED | Filter by status |
| `page` | integer | ❌ | 1 | ≥ 1 | Page number (1-based) |
| `page_size` | integer | ❌ | 20 | 1-100 | Items per page |

**Response:** `200 OK`

```json
{
  "items": [
    {
      "id": 1,
      "title": "Ground effect diffuser with active flow control",
      "description": "A ground effect diffuser that uses active flow control...",
      "status": "ANALYSED",
      "author": "Dr. Jane Smith",
      "tags": ["ground-effect", "active-aero"],
      "created_at": "2026-03-08T10:30:00Z",
      "updated_at": "2026-03-08T10:35:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**Example Requests:**
```bash
# List all concepts
curl http://localhost:8001/api/v1/concepts

# Filter by status
curl "http://localhost:8001/api/v1/concepts?status=SUBMITTED"

# Pagination
curl "http://localhost:8001/api/v1/concepts?page=2&page_size=10"
```

**Possible Errors:**
- `422` - Invalid page/page_size values

---

#### GET /concepts/{id}

Retrieve a single concept by ID.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Concept ID |

**Response:** `200 OK`

```json
{
  "id": 1,
  "title": "Ground effect diffuser with active flow control",
  "description": "A ground effect diffuser that uses active flow control...",
  "status": "ANALYSED",
  "author": "Dr. Jane Smith",
  "tags": ["ground-effect", "active-aero"],
  "created_at": "2026-03-08T10:30:00Z",
  "updated_at": "2026-03-08T10:35:00Z"
}
```

**Example Request:**
```bash
curl http://localhost:8001/api/v1/concepts/1
```

**Possible Errors:**
- `404` - Concept not found

---

#### PATCH /concepts/{id}

Update an existing concept (partial update).

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Concept ID |

**Request Body:** (all fields optional)

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `title` | string | 3-255 chars | Updated title |
| `description` | string | 20+ chars | Updated description |
| `author` | string | max 255 chars | Updated author |
| `tags` | array[string] | - | Updated tags |
| `status` | string | SUBMITTED \| ANALYSED | Updated status |

**Response:** `200 OK`

```json
{
  "id": 1,
  "title": "Updated ground effect diffuser design",
  "description": "A ground effect diffuser that uses active flow control...",
  "status": "ANALYSED",
  "author": "Dr. Jane Smith",
  "tags": ["ground-effect", "active-aero", "updated"],
  "created_at": "2026-03-08T10:30:00Z",
  "updated_at": "2026-03-08T11:00:00Z"
}
```

**Example Request:**
```bash
curl -X PATCH http://localhost:8001/api/v1/concepts/1 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated ground effect diffuser design",
    "tags": ["ground-effect", "active-aero", "updated"]
  }'
```

**Possible Errors:**
- `404` - Concept not found
- `422` - Validation error

---

#### DELETE /concepts/{id}

Delete a concept (cascade deletes associated evaluation).

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Concept ID |

**Response:** `204 No Content`

**Example Request:**
```bash
curl -X DELETE http://localhost:8001/api/v1/concepts/1
```

**Possible Errors:**
- `404` - Concept not found

---

### Evaluations

#### POST /concepts/{id}/evaluate

Trigger RAG evaluation for a concept (3-5 seconds processing time).

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Concept ID |

**Response:** `202 Accepted`

```json
{
  "id": 1,
  "concept_id": 1,
  "novelty_score": 0.82,
  "confidence_score": 0.91,
  "mechanisms": [
    "Boundary layer suction reduces separation",
    "Synthetic jets energize near-wall flow",
    "Dynamic frequency adjustment maintains optimal separation point"
  ],
  "tradeoffs": {
    "complexity": "Increased mechanical complexity vs performance gain",
    "power": "Jet actuation power consumption vs drag reduction",
    "reliability": "Sensor dependency introduces failure modes"
  },
  "regulatory_flags": [
    "Active aerodynamic devices may be restricted under FIA regulations",
    "Ground clearance sensors require homologation"
  ],
  "summary": "Moderately novel concept combining established active flow control with ground effect aerodynamics. The dynamic adjustment based on sensors is innovative, though individual components have precedent in literature.",
  "retrieved_context": [
    {
      "text": "Synthetic jets have been shown to delay separation on diffusers by up to 15% in wind tunnel testing...",
      "chunk_index": 42,
      "similarity_score": 0.89,
      "citation": {
        "arxiv_id": "2301.12345",
        "title": "Active Flow Control for High-Lift Systems",
        "authors": "J. Doe, M. Smith",
        "published": "2023-01-15",
        "url": "https://arxiv.org/abs/2301.12345"
      }
    }
  ],
  "created_at": "2026-03-08T10:35:00Z"
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8001/api/v1/concepts/1/evaluate
```

**Possible Errors:**
- `404` - Concept not found
- `409` - Evaluation already exists (concept already evaluated)
- `503` - Vector store or LLM service unavailable

---

#### GET /concepts/{id}/evaluation

Retrieve cached evaluation for a concept.

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `id` | integer | Concept ID |

**Response:** `200 OK`

```json
{
  "id": 1,
  "concept_id": 1,
  "novelty_score": 0.82,
  "confidence_score": 0.91,
  "mechanisms": [
    "Boundary layer suction reduces separation"
  ],
  "tradeoffs": {
    "complexity": "Increased mechanical complexity vs performance gain"
  },
  "regulatory_flags": [
    "Active aerodynamic devices may be restricted"
  ],
  "summary": "Moderately novel concept...",
  "retrieved_context": [...],
  "created_at": "2026-03-08T10:35:00Z"
}
```

**Example Request:**
```bash
curl http://localhost:8001/api/v1/concepts/1/evaluation
```

**Possible Errors:**
- `404` - Concept not found OR evaluation does not exist

---

## Data Models

### ConceptCreate

Request model for creating concepts.

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | ✅ | 3-255 chars | Concept title |
| `description` | string | ✅ | 20+ chars | Detailed description |
| `author` | string | ❌ | max 255 chars | Submitter name |
| `tags` | array[string] | ❌ | - | Taxonomy tags |

**Example:**
```json
{
  "title": "Morphing wing with active camber control",
  "description": "A wing design that dynamically changes camber using piezoelectric actuators to optimize aerodynamic performance across different flight regimes and conditions.",
  "author": "Dr. Jane Smith",
  "tags": ["morphing", "active-control", "wing"]
}
```

---

### ConceptResponse

Response model for concept objects.

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique identifier |
| `title` | string | Concept title |
| `description` | string | Full description |
| `status` | string | SUBMITTED \| ANALYSED |
| `author` | string \| null | Submitter name |
| `tags` | array[string] | Taxonomy tags |
| `created_at` | datetime | Creation timestamp (ISO 8601) |
| `updated_at` | datetime | Last update timestamp (ISO 8601) |

---

### EvaluationResponse

Response model for evaluation results.

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique identifier |
| `concept_id` | integer | Associated concept ID |
| `novelty_score` | float | Novelty score (0.0-1.0) |
| `confidence_score` | float | LLM confidence (0.0-1.0) |
| `mechanisms` | array[string] | Identified aerodynamic mechanisms |
| `tradeoffs` | object | Engineering tradeoffs (key-value pairs) |
| `regulatory_flags` | array[string] | Regulatory/safety concerns |
| `summary` | string | Natural language summary |
| `retrieved_context` | array[RetrievedChunk] | Citations from retrieved papers |
| `created_at` | datetime | Evaluation timestamp (ISO 8601) |

---

### RetrievedChunk

Citation with retrieved text and similarity score.

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Retrieved text chunk |
| `chunk_index` | integer | Chunk position in source |
| `similarity_score` | float | Cosine similarity (0.0-1.0) |
| `citation` | Citation | Paper metadata |

---

### Citation

arXiv paper metadata.

| Field | Type | Description |
|-------|------|-------------|
| `arxiv_id` | string \| null | arXiv identifier |
| `title` | string | Paper title |
| `authors` | string | Comma-separated authors |
| `published` | string \| null | Publication date (ISO 8601) |
| `url` | string \| null | Full arXiv URL |

---

## Examples

### Complete Workflow Example

```bash
# 1. Create a concept
CONCEPT=$(curl -X POST http://localhost:8001/api/v1/concepts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Vortex generator array for wing-body junction",
    "description": "Strategic placement of micro-vortex generators at the wing-body junction to reduce interference drag by energizing the boundary layer and delaying separation in the junction region.",
    "author": "Engineer A",
    "tags": ["vortex-generator", "interference-drag", "wing-body"]
  }' | jq -r '.id')

echo "Created concept ID: $CONCEPT"

# 2. List all submitted concepts
curl "http://localhost:8001/api/v1/concepts?status=SUBMITTED" | jq

# 3. Trigger evaluation
curl -X POST "http://localhost:8001/api/v1/concepts/$CONCEPT/evaluate" | jq

# 4. Retrieve evaluation
curl "http://localhost:8001/api/v1/concepts/$CONCEPT/evaluation" | jq

# 5. Update concept
curl -X PATCH "http://localhost:8001/api/v1/concepts/$CONCEPT" \
  -H "Content-Type: application/json" \
  -d '{
    "tags": ["vortex-generator", "interference-drag", "wing-body", "validated"]
  }' | jq

# 6. Delete concept
curl -X DELETE "http://localhost:8001/api/v1/concepts/$CONCEPT"
```

---

### Python Example

```python
import requests

BASE_URL = "http://localhost:8001/api/v1"

# Create a concept
response = requests.post(
    f"{BASE_URL}/concepts",
    json={
        "title": "Adaptive rear diffuser with moving strakes",
        "description": "A rear diffuser system with movable strakes that adjust angle based on yaw rate to maintain consistent downforce through corner transitions.",
        "author": "Research Team",
        "tags": ["diffuser", "adaptive", "downforce"]
    }
)
concept = response.json()
concept_id = concept["id"]

# Evaluate the concept
evaluation_response = requests.post(
    f"{BASE_URL}/concepts/{concept_id}/evaluate"
)
evaluation = evaluation_response.json()

print(f"Novelty Score: {evaluation['novelty_score']:.2f}")
print(f"Confidence: {evaluation['confidence_score']:.2f}")
print(f"Mechanisms: {', '.join(evaluation['mechanisms'])}")
```

---

### JavaScript/Node.js Example

```javascript
const BASE_URL = "http://localhost:8001/api/v1";

async function evaluateConcept() {
  // Create concept
  const createResponse = await fetch(`${BASE_URL}/concepts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: "Blown diffuser with exhaust integration",
      description: "Integration of exhaust flow into the rear diffuser to increase energization and downforce production through the Coanda effect.",
      author: "CFD Team",
      tags: ["blown-diffuser", "exhaust", "coanda"]
    })
  });
  
  const concept = await createResponse.json();
  
  // Evaluate
  const evalResponse = await fetch(
    `${BASE_URL}/concepts/${concept.id}/evaluate`,
    { method: "POST" }
  );
  
  const evaluation = await evalResponse.json();
  
  console.log(`Novelty: ${evaluation.novelty_score}`);
  console.log(`Retrieved ${evaluation.retrieved_context.length} papers`);
}

evaluateConcept();
```

---

## Rate Limits

**Current:** No rate limits implemented (development mode)

**Planned:**
- 100 requests per minute per IP
- 10 evaluations per hour per IP (LLM API cost management)

---

## Versioning

API version is included in:
- Base URL path: `/api/v1`
- Response headers: `X-API-Version: 0.1.0`

---

## Support

- **Interactive Documentation:** http://localhost:8001/docs
- **Alternative Docs:** http://localhost:8001/redoc
- **OpenAPI Spec:** http://localhost:8001/openapi.json
- **GitHub Issues:** [Project Repository]

---

*Generated: March 8, 2026*  
*Version: 0.1.0*
