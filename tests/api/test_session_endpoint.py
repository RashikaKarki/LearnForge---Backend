"""Unit tests for session endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from fastapi import FastAPI, Request
from starlette.testclient import TestClient

from app.api.v1.routes.session import router
from app.models.session_log import SessionLog
from app.models.user import User


# Test data fixtures (visible in test file per unit testing guide)
def get_test_user():
    """Test user for authentication."""
    return User(
        id="user123",
        firebase_uid="firebase_uid_123",
        name="Test User",
        email="test@example.com",
    )


def get_test_session():
    """Test session log data."""
    return SessionLog(
        id="session123",
        user_id="user123",
        status="active",
        mission_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        completed_at=None,
    )


def create_test_app():
    """Create FastAPI app with mocked database and user."""
    app = FastAPI()

    # Initialize app state with mock database
    app.state.db = MagicMock()

    @app.middleware("http")
    async def mock_user(request: Request, call_next):
        request.state.current_user = get_test_user()
        return await call_next(request)

    app.include_router(router, prefix="/sessions")
    return app


# Create session endpoint tests
def test_create_session_success_returns_201():
    """Should return 201 when creating a new session."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.create_session.return_value = get_test_session()

        client = TestClient(app)
        response = client.post("/sessions/")

        assert response.status_code == 201


def test_create_session_returns_session_id():
    """Should return session_id in response."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.create_session.return_value = get_test_session()

        client = TestClient(app)
        response = client.post("/sessions/")

        assert response.json()["session_id"] == "session123"


def test_create_session_returns_user_id():
    """Should return user_id in response."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.create_session.return_value = get_test_session()

        client = TestClient(app)
        response = client.post("/sessions/")

        assert response.json()["user_id"] == "user123"


def test_create_session_returns_active_status():
    """Should return 'active' status for new session."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.create_session.return_value = get_test_session()

        client = TestClient(app)
        response = client.post("/sessions/")

        assert response.json()["status"] == "active"


def test_create_session_includes_created_at():
    """Should include created_at timestamp."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.create_session.return_value = get_test_session()

        client = TestClient(app)
        response = client.post("/sessions/")

        assert "created_at" in response.json()


def test_create_session_uses_authenticated_user_id():
    """Should use authenticated user's ID for session."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.create_session.return_value = get_test_session()

        client = TestClient(app)
        client.post("/sessions/")

        # Verify service was called with correct user_id
        call_args = mock_service.return_value.create_session.call_args[0][0]
        assert call_args.user_id == "user123"


# Get session endpoint tests
def test_get_session_success_returns_200():
    """Should return 200 when getting an existing session."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.get_session.return_value = get_test_session()

        client = TestClient(app)
        response = client.get("/sessions/session123")

        assert response.status_code == 200


def test_get_session_returns_session_details():
    """Should return session details."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.get_session.return_value = get_test_session()

        client = TestClient(app)
        response = client.get("/sessions/session123")

        data = response.json()
        assert data["session_id"] == "session123"
        assert data["user_id"] == "user123"
        assert data["status"] == "active"


def test_get_session_forbidden_for_different_user():
    """Should return 403 when accessing another user's session."""
    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        # Return session belonging to different user
        different_user_session = SessionLog(
            id="session123",
            user_id="different_user",
            status="active",
            mission_id=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completed_at=None,
        )
        mock_service.return_value.get_session.return_value = different_user_session

        client = TestClient(app)
        response = client.get("/sessions/session123")

        assert response.status_code == 403


def test_get_session_not_found_returns_404():
    """Should return 404 when session doesn't exist."""
    from fastapi import HTTPException

    app = create_test_app()

    with patch("app.api.v1.routes.session.SessionLogService") as mock_service:
        mock_service.return_value.get_session.side_effect = HTTPException(
            status_code=404, detail="Session not found"
        )

        client = TestClient(app)
        response = client.get("/sessions/missing")

        assert response.status_code == 404
