from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError

from app.api.v1.routes.mission_commander import (
    AgentHandoverMessage,
    AgentMessage,
    ConnectionManager,
    ErrorMessage,
    MissionCreatedMessage,
    UserMessage,
    handle_disconnect,
    process_agent_flow,
    validate_session,
)
from app.models.enrollment import Enrollment
from app.models.mission import Mission
from app.models.session_log import SessionLog


# Mark all tests as async using anyio
pytestmark = pytest.mark.anyio


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def mock_db():
    """Mock database connection."""
    return MagicMock()


@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_json = AsyncMock()
    ws.close = AsyncMock()
    ws.app.state.db = MagicMock()
    ws.query_params = {"token": "test_token"}
    ws.cookies = {}  # Add cookies support
    ws.headers = {}  # Add headers support
    return ws


@pytest.fixture
def active_session():
    """Active session for testing."""
    return SessionLog(
        id="session123",
        user_id="user123",
        status="active",
        mission_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        completed_at=None,
    )


@pytest.fixture
def test_mission():
    """Test mission data."""
    return Mission(
        id="mission123",
        creator_id="user123",
        title="Learn Python",
        short_description="Master Python basics",
        description="Comprehensive Python course",
        level="Beginner",
        topics_to_cover=["Variables", "Functions"],
        learning_goal="Learn Python fundamentals",
        byte_size_checkpoints=["Intro", "Variables", "Functions"],
        skills=["Python", "Programming"],
        is_public=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def test_enrollment():
    """Test enrollment data."""
    return Enrollment(
        id="enrollment123",
        user_id="user123",
        mission_id="mission123",
        progress={},
        status="in_progress",
        started_at=datetime.now(),
        updated_at=datetime.now(),
    )


# ============================================================================
# Message Validation Tests
# ============================================================================


def test_user_message_validation_success():
    """Should validate correct user message."""
    msg = UserMessage(type="user_message", message="Hello")
    assert msg.message == "Hello"


def test_user_message_validation_fails_empty():
    """Should reject empty message."""
    with pytest.raises(ValidationError):
        UserMessage(type="user_message", message="")


def test_user_message_validation_fails_missing_field():
    """Should reject message without required field."""
    with pytest.raises(ValidationError):
        UserMessage(type="user_message")


# ============================================================================
# validate_session() Tests
# ============================================================================


async def test_validate_session_success(mock_websocket, active_session):
    """Should validate active session successfully."""
    with patch("app.api.v1.routes.mission_commander.SessionLogService") as mock_service:
        mock_service.return_value.get_session.return_value = active_session

        result = await validate_session(mock_websocket, "session123", "test_token")

        assert result is not None
        service, user_id = result
        assert user_id == "user123"


async def test_validate_session_via_cookie(mock_websocket, active_session):
    """Should validate session using cookie token."""
    mock_websocket.query_params = {}  # No query param token
    mock_websocket.cookies = {"token": "cookie_token"}

    with patch("app.api.v1.routes.mission_commander.SessionLogService") as mock_service:
        mock_service.return_value.get_session.return_value = active_session

        result = await validate_session(mock_websocket, "session123", None)

        assert result is not None
        service, user_id = result
        assert user_id == "user123"


async def test_validate_session_via_authorization_header(mock_websocket, active_session):
    """Should validate session using Authorization header."""
    mock_websocket.query_params = {}  # No query param token
    mock_websocket.cookies = {}  # No cookie
    mock_websocket.headers = {"authorization": "Bearer header_token"}

    with patch("app.api.v1.routes.mission_commander.SessionLogService") as mock_service:
        mock_service.return_value.get_session.return_value = active_session

        result = await validate_session(mock_websocket, "session123", None)

        assert result is not None
        service, user_id = result
        assert user_id == "user123"


async def test_validate_session_prefers_query_param_over_cookie(mock_websocket, active_session):
    """Should prefer query param token over cookie (backward compatibility)."""
    mock_websocket.query_params = {}
    mock_websocket.cookies = {"token": "cookie_token"}

    with patch("app.api.v1.routes.mission_commander.SessionLogService") as mock_service:
        mock_service.return_value.get_session.return_value = active_session

        # Pass query param explicitly
        result = await validate_session(mock_websocket, "session123", "query_token")

        assert result is not None
        # Query param should be used
        service, user_id = result
        assert user_id == "user123"


async def test_validate_session_missing_token(mock_websocket):
    """Should close connection when token is missing from all sources."""
    mock_websocket.query_params = {}
    mock_websocket.cookies = {}
    mock_websocket.headers = {}

    result = await validate_session(mock_websocket, "session123", None)

    assert result is None
    mock_websocket.close.assert_called_once()


async def test_validate_session_token_not_present_anywhere(mock_websocket):
    """Should close connection when token is completely absent (not in query, cookie, or header)."""
    mock_websocket.query_params = {}
    mock_websocket.cookies = {}
    mock_websocket.headers = {}

    result = await validate_session(mock_websocket, "session123", None)

    assert result is None
    mock_websocket.close.assert_called_once()
    close_call_args = mock_websocket.close.call_args
    if close_call_args and close_call_args[1]:
        assert "code" in close_call_args[1]
        assert close_call_args[1]["code"] == 1008


async def test_validate_session_inactive_session(mock_websocket):
    """Should close connection when session is inactive."""
    inactive_session = SessionLog(
        id="session123",
        user_id="user123",
        status="completed",
        mission_id="mission123",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        completed_at=datetime.now(),
    )

    with patch("app.api.v1.routes.mission_commander.SessionLogService") as mock_service:
        mock_service.return_value.get_session.return_value = inactive_session

        result = await validate_session(mock_websocket, "session123", "test_token")

        assert result is None
        mock_websocket.close.assert_called_once()


async def test_validate_session_not_found(mock_websocket):
    """Should close connection when session not found."""
    with patch("app.api.v1.routes.mission_commander.SessionLogService") as mock_service:
        mock_service.return_value.get_session.side_effect = Exception("Not found")

        result = await validate_session(mock_websocket, "session123", "test_token")

        assert result is None
        mock_websocket.close.assert_called_once()


# ============================================================================
# handle_disconnect() Tests
# ============================================================================


async def test_handle_disconnect_marks_incomplete_session_abandoned():
    """Should mark session as abandoned if no mission created."""
    mock_service = MagicMock()
    mock_session = MagicMock()
    mock_session.state = {"creator_id": "user123"}  # No mission_create

    with patch("app.api.v1.routes.mission_commander.manager") as mock_manager:
        mock_manager.session_service.get_session = AsyncMock(return_value=mock_session)
        mock_manager.disconnect = MagicMock()

        await handle_disconnect("session123", "user123", mock_service)

        mock_service.mark_session_abandoned.assert_called_once_with("session123")
        mock_manager.disconnect.assert_called_once_with("session123")


async def test_handle_disconnect_does_not_mark_completed_session():
    """Should not mark session as abandoned if mission was created."""
    mock_service = MagicMock()
    mock_session = MagicMock()
    mock_session.state = {
        "creator_id": "user123",
        "mission_create": {"title": "Test"},
    }

    with patch("app.api.v1.routes.mission_commander.manager") as mock_manager:
        mock_manager.session_service.get_session = AsyncMock(return_value=mock_session)
        mock_manager.disconnect = MagicMock()

        await handle_disconnect("session123", "user123", mock_service)

        mock_service.mark_session_abandoned.assert_not_called()
        mock_manager.disconnect.assert_called_once_with("session123")


# ============================================================================
# process_agent_flow() Tests
# ============================================================================


async def test_process_agent_flow_sends_agent_messages():
    """Should send agent text messages to client."""
    manager = MagicMock()
    manager.send_message = AsyncMock()

    # Mock agent event with text content
    mock_event = MagicMock()
    mock_event.actions = None
    mock_event.author = "polaris"
    mock_event.content.parts = [MagicMock(text="Hello, what would you like to learn?")]

    manager.runner.run = MagicMock(return_value=[mock_event])

    # Mock session without mission_create
    mock_session = MagicMock()
    mock_session.state = {"creator_id": "user123"}
    manager.session_service.get_session = AsyncMock(return_value=mock_session)

    mission_service = MagicMock()
    session_log_service = MagicMock()

    await process_agent_flow(
        "session123",
        "user123",
        manager,
        mission_service,
        session_log_service,
        "I want to learn Python",
    )

    # Should have sent the agent message
    assert manager.send_message.call_count >= 1
    calls = manager.send_message.call_args_list
    agent_messages = [call for call in calls if isinstance(call[0][1], AgentMessage)]
    assert len(agent_messages) > 0


async def test_process_agent_flow_detects_agent_transfer():
    """Should detect and send handover message on agent transfer."""
    manager = MagicMock()
    manager.send_message = AsyncMock()

    # Mock transfer event
    mock_transfer_event = MagicMock()
    mock_transfer_event.actions.transfer_to_agent = "mission_curator"
    mock_transfer_event.author = "polaris"
    mock_transfer_event.content = None

    manager.runner.run = MagicMock(return_value=[mock_transfer_event])

    # Mock session
    mock_session = MagicMock()
    mock_session.state = {"creator_id": "user123"}
    manager.session_service.get_session = AsyncMock(return_value=mock_session)

    mission_service = MagicMock()
    session_log_service = MagicMock()

    await process_agent_flow(
        "session123", "user123", manager, mission_service, session_log_service, "yes, proceed"
    )

    # Should have sent handover message
    calls = manager.send_message.call_args_list
    handover_messages = [call for call in calls if isinstance(call[0][1], AgentHandoverMessage)]
    assert len(handover_messages) == 1
    assert handover_messages[0][0][1].agent == "mission_curator"


async def test_process_agent_flow_creates_mission_on_completion():
    """Should create mission and send mission_created message."""
    manager = MagicMock()
    manager.send_message = AsyncMock()

    # Mock event
    mock_event = MagicMock()
    mock_event.actions = None
    mock_event.author = "mission_curator"
    mock_event.content = None

    manager.runner.run = MagicMock(return_value=[mock_event])

    # Mock session with mission_create
    mission_data = {
        "title": "Learn Python",
        "short_description": "Python basics",
        "description": "Comprehensive Python course",
        "creator_id": "user123",
        "level": "Beginner",
        "topics_to_cover": ["Variables"],
        "learning_goal": "Learn Python",
        "byte_size_checkpoints": ["Intro", "Variables", "Functions", "Conclusion"],
        "skills": ["Python"],
        "is_public": True,
    }

    mock_session = MagicMock()
    mock_session.state = {"creator_id": "user123", "mission_create": mission_data}
    manager.session_service.get_session = AsyncMock(return_value=mock_session)

    # Mock services
    mission_service = MagicMock()
    test_mission = MagicMock()
    test_mission.id = "mission123"
    test_mission.model_dump = MagicMock(return_value={"id": "mission123"})

    test_enrollment = MagicMock()
    test_enrollment.id = "enrollment123"
    test_enrollment.model_dump = MagicMock(return_value={"id": "enrollment123"})

    test_enrollment_session_log = MagicMock()
    test_enrollment_session_log.id = "enrollment_session_log123"
    test_enrollment_session_log.model_dump = MagicMock(
        return_value={"id": "enrollment_session_log123"}
    )

    mission_service.create_mission_with_enrollment.return_value = (
        test_mission,
        test_enrollment,
        test_enrollment_session_log,
    )

    session_log_service = MagicMock()

    await process_agent_flow(
        "session123", "user123", manager, mission_service, session_log_service, "yes"
    )

    # Should create mission
    mission_service.create_mission_with_enrollment.assert_called_once()

    # Should mark session as completed
    session_log_service.mark_session_completed.assert_called_once_with(
        "session123", mission_id="mission123"
    )

    # Should send mission_created message
    calls = manager.send_message.call_args_list
    mission_messages = [call for call in calls if isinstance(call[0][1], MissionCreatedMessage)]
    assert len(mission_messages) == 1


async def test_process_agent_flow_filters_mission_curator_text():
    """Should not send text from mission_curator (internal processing)."""
    manager = MagicMock()
    manager.send_message = AsyncMock()

    # Mock mission_curator event with text
    mock_event = MagicMock()
    mock_event.actions = None
    mock_event.author = "mission_curator"
    mock_event.content.parts = [MagicMock(text="Internal processing text")]

    manager.runner.run = MagicMock(return_value=[mock_event])

    # Mock session
    mock_session = MagicMock()
    mock_session.state = {"creator_id": "user123"}
    manager.session_service.get_session = AsyncMock(return_value=mock_session)

    mission_service = MagicMock()
    session_log_service = MagicMock()

    await process_agent_flow(
        "session123", "user123", manager, mission_service, session_log_service, "test"
    )

    # Should NOT have sent agent message from mission_curator
    calls = manager.send_message.call_args_list
    agent_messages = [call for call in calls if isinstance(call[0][1], AgentMessage)]
    assert len(agent_messages) == 0


async def test_process_agent_flow_handles_errors():
    """Should mark session as error and send error message on exception."""
    manager = MagicMock()
    manager.send_message = AsyncMock()

    # Mock runner to raise exception
    manager.runner.run = MagicMock(side_effect=Exception("Agent error"))

    mission_service = MagicMock()
    session_log_service = MagicMock()

    await process_agent_flow(
        "session123", "user123", manager, mission_service, session_log_service, "test"
    )

    # Should mark session as error
    session_log_service.mark_session_error.assert_called_once_with("session123")

    # Should send error message
    calls = manager.send_message.call_args_list
    error_messages = [call for call in calls if isinstance(call[0][1], ErrorMessage)]
    assert len(error_messages) == 1


# ============================================================================
# ConnectionManager Tests (Additional)
# ============================================================================


async def test_connection_manager_send_message_serializes_correctly():
    """Should serialize Pydantic message models correctly."""
    manager = ConnectionManager()
    mock_ws = MagicMock()
    mock_ws.send_json = AsyncMock()

    manager.active_connections["session123"] = mock_ws

    msg = AgentMessage(message="Test message")
    await manager.send_message("session123", msg)

    mock_ws.send_json.assert_called_once()
    call_args = mock_ws.send_json.call_args[0][0]
    assert call_args["type"] == "agent_message"
    assert call_args["message"] == "Test message"


async def test_connection_manager_send_to_nonexistent_session():
    """Should gracefully handle sending to non-existent session."""
    manager = ConnectionManager()

    # Should not raise error
    await manager.send_message("nonexistent", AgentMessage(message="test"))
