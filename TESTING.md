# Testing & Error Handling

This document covers the comprehensive testing strategy and error handling implementation for AeroInsight.

## Test Coverage Summary

**Total: 49 Tests (100% passing)**

| Test Suite | Tests | Status |
|------------|-------|--------|
| API Error Tests | 16 | ✅ 100% |
| Concept Tests | 13 | ✅ 100% |
| Database Tests | 13 | ✅ 100% |
| E2E Tests | 7 | ✅ 100% |

---

## Running Tests

```bash
# Activate virtual environment
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac

# Run all tests
uv run pytest tests/ -v

# Run specific test suite
uv run pytest tests/test_api_errors.py -v
uv run pytest tests/test_database_errors.py -v
uv run pytest tests/test_e2e.py -v
uv run pytest tests/test_concepts.py -v

# Run with coverage report
uv run pytest tests/ --cov=app --cov-report=html

# Run tests matching pattern
uv run pytest tests/ -k "error" -v

# Stop after first 3 failures
uv run pytest tests/ --maxfail=3
```

---

## Custom Exception System

### Exception Hierarchy

```python
AeroInsightError (Base)
├── ConceptNotFoundError (404)
├── EvaluationNotFoundError (404)
├── EvaluationExistsError (409)
├── ValidationError (422)
├── VectorStoreError (503)
├── LLMServiceError (503)
├── DatabaseError (500)
├── RateLimitError (429)
└── ServiceUnavailableError (503)
```

### Exception Response Format

All API errors return consistent JSON:

```json
{
  "detail": "Concept with id 123 not found",
  "code": "concept_not_found",
  "concept_id": 123
}
```

### Usage Example

```python
from app.core.exceptions import ConceptNotFoundError

def get_concept(db: Session, concept_id: int):
    concept = db.query(AeroConcept).filter(AeroConcept.id == concept_id).first()
    if not concept:
        raise ConceptNotFoundError(concept_id)
    return concept
```

---

## Frontend Error Handling

### Error Utilities (`frontend/src/utils/errors.js`)

- **parseApiError()** - Normalize errors from different sources
- **getErrorMessage()** - Map error codes to user-friendly messages
- **isNetworkError() / isClientError() / isServerError()** - Error type checking
- **retryWithBackoff()** - Exponential backoff retry logic

### Error Display Components

**Toast Notifications** (`components/common/Toast.jsx`):
```javascript
import { useToast } from '../components/common/Toast';

const { showError, showSuccess } = useToast();

try {
  await createConcept(data);
  showSuccess('Concept created!');
} catch (error) {
  showError(getErrorMessage(error));
}
```

**Error Boundary** (`components/common/ErrorBoundary.jsx`):
```javascript
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

**Error Display** (`components/common/ErrorDisplay.jsx`):
- `<ErrorDisplay />` - Full error with retry/dismiss actions
- `<FieldError />` - Inline form field errors
- `<EmptyState />` - Empty state displays
- `<LoadingError />` - Loading failure with retry

---

## Test Suites

### 1. API Error Tests (`tests/test_api_errors.py`)

**16 tests covering:**
- 404 Not Found (nonexistent concepts/evaluations)
- 409 Conflict (duplicate evaluations)
- 422 Validation errors (invalid input, pagination)
- 500 Internal Server errors (database failures)
- 503 Service Unavailable (vector store, LLM failures)
- Consistent error response structure

**Example:**
```python
def test_nonexistent_concept_returns_404(client: TestClient):
    response = client.get("/api/v1/concepts/9999")
    assert response.status_code == 404
    assert response.json()["code"] == "concept_not_found"
```

### 2. Database Transaction Tests (`tests/test_database_errors.py`)

**13 tests covering:**
- Transaction rollbacks on failures
- Cascade deletes (evaluation → concept)
- Concurrent evaluation prevention
- Connection failure handling
- Data integrity constraints (status enums, score precision, JSON fields)
- Foreign key constraints
- Session cleanup after errors

**Example:**
```python
def test_cascade_delete_removes_evaluation(db_session: Session):
    concept = create_concept_with_evaluation(db_session)
    db_session.delete(concept)
    db_session.commit()
    
    # Verify evaluation was cascade deleted
    assert db_session.query(ConceptEvaluation).count() == 0
```

### 3. End-to-End Tests (`tests/test_e2e.py`)

**7 tests covering:**
- Complete concept lifecycle (create → evaluate → delete)
- Multiple concepts workflow with pagination
- Evaluation caching (409 on duplicate)
- Health check and MCP discovery endpoints
- Update preservation of evaluations
- Error recovery workflows

**Example:**
```python
def test_complete_concept_lifecycle(client: TestClient):
    # Create concept
    response = client.post("/api/v1/concepts", json={
        "title": "Morphing Wing",
        "description": "A wing design that changes camber in flight",
        "author": "Test Engineer"
    })
    concept_id = response.json()["id"]
    
    # Evaluate
    eval_response = client.post(f"/api/v1/concepts/{concept_id}/evaluate")
    assert eval_response.status_code == 202
    
    # Verify status
    get_response = client.get(f"/api/v1/concepts/{concept_id}")
    assert get_response.json()["status"] == "ANALYSED"
    
    # Delete
    delete_response = client.delete(f"/api/v1/concepts/{concept_id}")
    assert delete_response.status_code == 204
```

### 4. Concept CRUD Tests (`tests/test_concepts.py`)

**13 tests covering:**
- Basic CRUD operations
- List filtering and pagination
- Tag parsing and storage
- Status transitions
- Input validation

---

## Test Configuration

### Isolated Test Database

Tests use in-memory SQLite with `StaticPool` for isolation:

```python
TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
```

### Mocking Strategy

- **External Dependencies**: Mock LLM and vector store calls
- **Database Operations**: Use real SQLAlchemy with test database
- **Low-Level Mocking**: Mock `vector_store.query()` and `get_llm_client()` to allow DB operations

```python
# Low-level mocking pattern
with patch("app.services.rag_service.vector_store.query") as mock_vector:
    with patch("app.services.rag_service.get_llm_client") as mock_llm:
        mock_vector.return_value = []
        mock_llm_client.chat.return_value = '{"novelty_score": 0.8, ...}'
        # Actual DB operations execute normally
        response = client.post(f"/api/v1/concepts/{id}/evaluate")
```

---

## Common Testing Patterns

### Creating Test Concepts

```python
def create_test_concept(client: TestClient) -> dict:
    response = client.post("/api/v1/concepts", json={
        "title": "Test Concept",
        "description": "This is a test description that meets minimum length",
        "author": "Test User",
        "tags": ["test", "validation"]
    })
    return response.json()
```

### Validating Error Responses

```python
def assert_error_response(response, expected_status: int, expected_code: str):
    assert response.status_code == expected_status
    error = response.json()
    assert "detail" in error
    assert error["code"] == expected_code
```

### Mocking RAG Pipeline

```python
@patch("app.services.rag_service.vector_store.query")
@patch("app.services.rag_service.get_llm_client")
def test_evaluation(mock_llm_client, mock_vector, client):
    mock_vector.return_value = []
    mock_llm = MagicMock()
    mock_llm.chat.return_value = '{"novelty_score": 0.8, ...}'
    mock_llm_client.return_value = mock_llm
    
    response = client.post("/api/v1/concepts/1/evaluate")
    assert response.status_code == 202
```

---

## Troubleshooting Tests

### SQLite Foreign Key Constraints

If you see "foreign key constraint failed" errors:

```python
# Add to conftest.py or test file
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

### Description Length Validation

Concepts require descriptions ≥ 20 characters:

```python
# ❌ Too short
description = "Test description"  # 16 chars

# ✅ Valid
description = "This is a test description for validation"  # 45 chars
```

### Evaluation Caching

Evaluations are cached (one per concept). Testing duplicate evaluation:

```python
# First evaluation succeeds
response1 = client.post(f"/api/v1/concepts/{id}/evaluate")
assert response1.status_code == 202

# Second evaluation returns conflict
response2 = client.post(f"/api/v1/concepts/{id}/evaluate")
assert response2.status_code == 409
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install uv
        uv pip install -r requirements.txt
    
    - name: Run tests
      run: uv run pytest tests/ -v --cov=app
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

---

## Best Practices

1. **Isolation**: Each test should be independent and not rely on state from other tests
2. **Mocking**: Mock external dependencies (LLM, vector store) but test real DB logic
3. **Fast Execution**: Use in-memory database and mocked services for speed
4. **Clear Assertions**: Test one thing per test with descriptive names
5. **Fixtures**: Share common setup code via pytest fixtures
6. **Coverage**: Aim for 80%+ coverage on business logic

---

## Adding New Tests

### 1. Create Test File

```python
# tests/test_new_feature.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_new_feature(client):
    response = client.get("/api/v1/new-endpoint")
    assert response.status_code == 200
```

### 2. Add to Test Suite

Tests are automatically discovered by pytest if:
- File name starts with `test_`
- Function name starts with `test_`
- Located in `tests/` directory

### 3. Update Documentation

Update this file with:
- Test count in summary
- Brief description of what's tested
- Example test if pattern is new

---

## Performance Testing

For load testing (not included in standard suite):

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def load_test_evaluations():
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(client.post, f"/api/v1/concepts/{i}/evaluate")
            for i in range(100)
        ]
        results = [f.result() for f in futures]
    
    # Analyze response times, error rates
```

---

*Last Updated: March 2026*
