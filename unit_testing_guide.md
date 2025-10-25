# Unit Testing Guide

Use this as context to writing unit testing.

## Core Principles

1. **Small & Fast** - Test one thing per test
2. **Independent** - Tests run in any order
3. **Repeatable** - Same result every time
4. **Reusable Mocks** - Centralized mock factories

---

## File Structure

```
tests/
├── conftest.py           # Shared fixtures
├── mocks/
│   ├── __init__.py
│   └── firestore.py      # Reusable mock factories
├── model/
│   ├── test_user.py
├── service/
│   ├── test_user_service.py
```

---

## 1. Reusable Mocks (Keep Small!)

**Pattern: Centralized Mock Factory**

```python
# tests/mocks/firestore.py (< 100 lines)
class FirestoreMocks:
    @staticmethod
    def collection_empty():
        """Empty collection for create operations."""
        collection = MagicMock()
        collection.where.return_value.limit.return_value.get.return_value = []
        collection.document.return_value.id = "new_id"
        return collection

    @staticmethod
    def collection_with_user(user_data):
        """Collection with existing user."""
        collection = MagicMock()
        doc = MagicMock()
        doc.to_dict.return_value = user_data
        collection.where.return_value.limit.return_value.get.return_value = [doc]
        return collection

    @staticmethod
    def document_exists(doc_id, data):
        doc = MagicMock()
        doc.exists = True
        doc.id = doc_id
        doc.to_dict.return_value = data
        return doc
```

**Benefits:**
- Reuse across all test files
- Single place to update mocks
- Keeps tests clean and small

---

## 2. Testing Models

**Goal: Validate data structures only**

```python
# tests/unit/test_models.py
from app.models.user import User

def test_user_model_creation():
    user = User(
        id="123",
        email="test@example.com",
        name="Test"
    )
    assert user.id == "123"
    assert user.email == "test@example.com"

def test_user_model_validation():
    with pytest.raises(ValidationError):
        User(email="invalid-email")

@pytest.mark.parametrize("email", ["", None, "no-at-sign"])
def test_user_email_validation(email):
    with pytest.raises(ValidationError):
        User(id="1", email=email, name="Test")
```

**Keep it minimal:**
- Only test validation logic
- Don't test framework features (Pydantic does that)
- Test edge cases (None, empty, invalid formats)

---

## 3. Testing Services

**Goal: Test business logic with mocked dependencies**

```python
# tests/unit/test_services.py
from tests.mocks.firestore import FirestoreMocks

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def valid_user_data():
    return {"email": "test@example.com", "name": "Test"}

# Test success case
def test_create_user_success(mock_db, valid_user_data):
    collection = FirestoreMocks.collection_empty()
    mock_db.collection.return_value = collection
    service = UserService(mock_db)

    user = service.create_user(valid_user_data)

    assert user.email == "test@example.com"
    collection.document.assert_called_once()

# Test error case
def test_create_user_duplicate_raises_400(mock_db, valid_user_data):
    existing = {"id": "1", "email": "test@example.com", "name": "Existing"}
    collection = FirestoreMocks.collection_with_user(existing)
    mock_db.collection.return_value = collection
    service = UserService(mock_db)

    with pytest.raises(HTTPException) as exc:
        service.create_user(valid_user_data)

    assert exc.value.status_code == 400
```

**Pattern:**
1. Setup mocks using factory
2. Call service method
3. Assert result + verify mock calls

---

## 4. Testing Endpoints

**Goal: Test HTTP layer only**

```python
# tests/unit/test_endpoints.py
from fastapi.testclient import TestClient
from unittest.mock import patch

client = TestClient(app)

@patch('app.api.routes.user_service')
def test_create_user_endpoint_success(mock_service):
    mock_service.create_user.return_value = User(
        id="123",
        email="test@example.com",
        name="Test"
    )

    response = client.post("/users", json={
        "email": "test@example.com",
        "name": "Test"
    })

    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
    mock_service.create_user.assert_called_once()

@patch('app.api.routes.user_service')
def test_create_user_endpoint_validation_error(mock_service):
    response = client.post("/users", json={
        "email": "invalid"  # missing required fields
    })

    assert response.status_code == 422

@patch('app.api.routes.user_service')
def test_create_user_endpoint_duplicate_email(mock_service):
    mock_service.create_user.side_effect = HTTPException(
        status_code=400,
        detail="Email exists"
    )

    response = client.post("/users", json={
        "email": "test@example.com",
        "name": "Test"
    })

    assert response.status_code == 400
```

**Pattern:**
1. Mock the service layer
2. Make HTTP request via TestClient
3. Assert status code + response body

---

## 5. Byte-Size Testing (Keep Tests Small)

**Target: < 15 lines per test**

### Good (Small & Focused)
```python
def test_create_user_success(mock_db, user_data):
    collection = FirestoreMocks.collection_empty()
    mock_db.collection.return_value = collection
    service = UserService(mock_db)

    user = service.create_user(user_data)

    assert user.email == user_data["email"]
```

### Bad (Too Large)
```python
def test_user_full_lifecycle():
    # 50+ lines testing create, update, delete, get...
    # Split into separate tests!
```

**How to keep small:**
- Use fixtures for setup
- Use mock factories
- One assertion focus per test
- Use parametrize for similar cases

---

## 6. Fixtures Pattern

**CRITICAL RULE: Keep test data visible, hide infrastructure!**

### Philosophy
- **Test Data** → Keep in test file (even if shared) - makes tests readable
- **Infrastructure** → Put in conftest.py - generic setup that's not test-specific

### ❌ Bad: Test data hidden in conftest.py
```python
# conftest.py - DON'T DO THIS
@pytest.fixture
def valid_user_data():  # Test data should be in test file!
    return {"email": "test@example.com", "name": "Test"}

@pytest.fixture
def existing_mission():  # Test data should be in test file!
    return {"id": "123", "title": "Test Mission"}
```

### ✅ Good: Test data in test file (even if shared across tests)
```python
# tests/services/test_user_service.py
from datetime import datetime
import pytest

@pytest.fixture
def valid_user_create_data():
    """Test data - keep visible in the test file."""
    from app.models.user import UserCreate
    return UserCreate(
        name="Test User",
        firebase_uid="uid123",
        email="test@example.com",
        picture="http://example.com/picture.jpg"
    )

@pytest.fixture
def existing_user():
    """Test data - visible and specific to these tests."""
    return {
        "id": "user123",
        "email": "existing@example.com",
        "name": "Existing",
        "created_at": datetime(2025, 1, 1, 12, 0, 0),
        "updated_at": datetime(2025, 1, 1, 12, 0, 0),
    }

def test_create_user(valid_user_create_data):
    # Can see exactly what data is being tested
    pass
```

### ✅ Good: Infrastructure/setup in conftest.py
```python
# conftest.py - Generic infrastructure shared across ALL tests
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_db():
    """Database mock - generic infrastructure."""
    return MagicMock()

@pytest.fixture
def mock_firestore_client():
    """Firestore client mock - generic infrastructure."""
    client = MagicMock()
    client.collection.return_value = MagicMock()
    return client

@pytest.fixture
def test_client():
    """FastAPI test client - generic infrastructure."""
    from fastapi.testclient import TestClient
    from app.core.app import create_app
    return TestClient(create_app())
```

### Decision Rule:
- **Test Data** (user objects, mission data, etc.) → IN the test file
- **Infrastructure** (mock db, mock client, test setup) → conftest.py
- **When in doubt** → Keep it in the test file for visibility

**Benefits:**
- ✅ Tests are self-documenting (can see the test data)
- ✅ Easy to modify test data without affecting other tests
- ✅ No jumping between files to understand what's being tested
- ✅ Infrastructure stays DRY in conftest

---

## 7. Parametrized Tests (Test Multiple Cases)

```python
@pytest.mark.parametrize("email,valid", [
    ("test@example.com", True),
    ("invalid-email", False),
    ("", False),
    (None, False),
])
def test_email_validation(email, valid):
    if valid:
        user = User(id="1", email=email, name="Test")
        assert user.email == email
    else:
        with pytest.raises(ValidationError):
            User(id="1", email=email, name="Test")
```

---

## 8. Quick Reference

### Test Naming
```python
def test_<method>_<scenario>_<result>():
    pass

# Examples:
def test_create_user_valid_data_returns_user():
def test_get_user_not_found_raises_404():
def test_delete_user_success_returns_true():
```

### What to Mock
- Database connections
- External APIs
- File system
- datetime.now()
- Never mock: Your models
- Never mock: Simple data structures

### What to Test
- Success paths
- Error cases (404, 400, 500)
- Edge cases (None, empty, invalid)
- Validation logic
- Do not test Framework internals
- Do not test Third-party libraries

---

## Complete Example

```python
# tests/mocks/firestore.py - Reusable mock factories
class FirestoreMocks:
    @staticmethod
    def collection_empty():
        collection = MagicMock()
        collection.where.return_value.limit.return_value.get.return_value = []
        doc = MagicMock()
        doc.id = "auto_generated_id"
        doc.set = MagicMock()
        collection.document.return_value = doc
        return collection

# tests/conftest.py - Generic infrastructure only
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_db():
    """Generic database mock used across all service tests."""
    return MagicMock()

# tests/services/test_user_service.py - Test data stays here!
from datetime import datetime
import pytest
from tests.mocks.firestore import FirestoreMocks

@pytest.fixture
def valid_user_create_data():
    """Test-specific data - visible in this file."""
    from app.models.user import UserCreate
    return UserCreate(
        name="Test User",
        firebase_uid="uid123",
        email="test@example.com",
        picture="http://example.com/picture.jpg"
    )

def test_create_user_success(mock_db, valid_user_create_data):
    """Can see exactly what's being tested without jumping files."""
    collection = FirestoreMocks.collection_empty()
    mock_db.collection.return_value = collection
    service = UserService(mock_db)

    user = service.create_user(valid_user_create_data)

    assert user.email == "test@example.com"
    assert user.id == "auto_generated_id"
```

---

## Checklist

Before committing tests:
- [ ] Each test < 15 lines
- [ ] Using reusable mocks
- [ ] Clear test name
- [ ] One thing tested
- [ ] Test data fixtures are in the test file (visible)
- [ ] Infrastructure mocks are in conftest.py (if shared)
- [ ] Tests run independently
- [ ] No hardcoded values in assertions
