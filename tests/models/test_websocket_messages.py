"""Tests for WebSocket message models.

Focus: Data validation and model structure only.
"""

import pytest
from pydantic import ValidationError

from app.models.websocket_messages import (
    AgentHandoverMessage,
    AgentMessage,
    AgentProcessingEndMessage,
    AgentProcessingStartMessage,
    CheckpointUpdateMessage,
    ConnectedMessage,
    ErrorMessage,
    HistoricalMessagesMessage,
    MessageType,
    MissionAllyServerMessage,
    MissionCommanderServerMessage,
    MissionCreatedMessage,
    PingMessage,
    PongMessage,
    SessionClosedMessage,
    UserMessage,
)


# ============================================================================
# MessageType Enum Tests
# ============================================================================


def test_message_type_enum_values():
    """Should have all expected message type values."""
    assert MessageType.USER_MESSAGE == "user_message"
    assert MessageType.AGENT_MESSAGE == "agent_message"
    assert MessageType.AGENT_HANDOVER == "agent_handover"
    assert MessageType.MISSION_CREATED == "mission_created"
    assert MessageType.CONNECTED == "connected"
    assert MessageType.PING == "ping"
    assert MessageType.PONG == "pong"
    assert MessageType.ERROR == "error"
    assert MessageType.CHECKPOINT_UPDATE == "checkpoint_update"
    assert MessageType.SESSION_CLOSED == "session_closed"
    assert MessageType.HISTORICAL_MESSAGES == "historical_messages"
    assert MessageType.AGENT_PROCESSING_START == "agent_processing_start"
    assert MessageType.AGENT_PROCESSING_END == "agent_processing_end"


# ============================================================================
# Client → Server Messages
# ============================================================================


def test_user_message_valid():
    """Should create UserMessage with valid data."""
    message = UserMessage(message="Hello, agent!")
    assert message.type == MessageType.USER_MESSAGE
    assert message.message == "Hello, agent!"


def test_user_message_empty_string_raises():
    """Should raise ValidationError for empty message."""
    with pytest.raises(ValidationError):
        UserMessage(message="")


def test_user_message_missing_message_raises():
    """Should raise ValidationError when message is missing."""
    with pytest.raises(ValidationError):
        UserMessage()


def test_ping_message_valid():
    """Should create PingMessage with correct type."""
    message = PingMessage()
    assert message.type == MessageType.PING


# ============================================================================
# Server → Client Messages
# ============================================================================


def test_connected_message_valid():
    """Should create ConnectedMessage with message."""
    message = ConnectedMessage(message="Connected successfully!")
    assert message.type == MessageType.CONNECTED
    assert message.message == "Connected successfully!"


def test_agent_message_valid():
    """Should create AgentMessage with message."""
    message = AgentMessage(message="Hello, user!")
    assert message.type == MessageType.AGENT_MESSAGE
    assert message.message == "Hello, user!"


def test_agent_handover_message_valid():
    """Should create AgentHandoverMessage with agent and message."""
    message = AgentHandoverMessage(agent="mission_sensei", message="Handing over...")
    assert message.type == MessageType.AGENT_HANDOVER
    assert message.agent == "mission_sensei"
    assert message.message == "Handing over..."


def test_agent_handover_message_missing_fields_raises():
    """Should raise ValidationError when required fields are missing."""
    with pytest.raises(ValidationError):
        AgentHandoverMessage(agent="mission_sensei")
    with pytest.raises(ValidationError):
        AgentHandoverMessage(message="Handing over...")


def test_mission_created_message_valid():
    """Should create MissionCreatedMessage with mission, enrollment, and message."""
    mission_data = {"id": "mission123", "title": "Test Mission"}
    enrollment_data = {"id": "enrollment123", "user_id": "user123"}
    message = MissionCreatedMessage(
        mission=mission_data, enrollment=enrollment_data, message="Mission created!"
    )
    assert message.type == MessageType.MISSION_CREATED
    assert message.mission == mission_data
    assert message.enrollment == enrollment_data
    assert message.message == "Mission created!"


def test_mission_created_message_missing_fields_raises():
    """Should raise ValidationError when required fields are missing."""
    with pytest.raises(ValidationError):
        MissionCreatedMessage(mission={"id": "m1"}, enrollment={"id": "e1"})
    with pytest.raises(ValidationError):
        MissionCreatedMessage(mission={"id": "m1"}, message="Created")
    with pytest.raises(ValidationError):
        MissionCreatedMessage(enrollment={"id": "e1"}, message="Created")


def test_pong_message_valid():
    """Should create PongMessage with correct type."""
    message = PongMessage()
    assert message.type == MessageType.PONG


def test_error_message_valid():
    """Should create ErrorMessage with message."""
    message = ErrorMessage(message="An error occurred")
    assert message.type == MessageType.ERROR
    assert message.message == "An error occurred"


def test_checkpoint_update_message_valid():
    """Should create CheckpointUpdateMessage with checkpoints and progress."""
    message = CheckpointUpdateMessage(
        completed_checkpoints=["checkpoint1", "checkpoint2"], progress=50.0
    )
    assert message.type == MessageType.CHECKPOINT_UPDATE
    assert message.completed_checkpoints == ["checkpoint1", "checkpoint2"]
    assert message.progress == 50.0


def test_checkpoint_update_message_empty_checkpoints():
    """Should allow empty completed_checkpoints list."""
    message = CheckpointUpdateMessage(completed_checkpoints=[], progress=0.0)
    assert message.completed_checkpoints == []
    assert message.progress == 0.0


def test_checkpoint_update_message_missing_fields_raises():
    """Should raise ValidationError when required fields are missing."""
    with pytest.raises(ValidationError):
        CheckpointUpdateMessage(completed_checkpoints=["cp1"])
    with pytest.raises(ValidationError):
        CheckpointUpdateMessage(progress=50.0)


def test_session_closed_message_valid():
    """Should create SessionClosedMessage with message."""
    message = SessionClosedMessage(message="Session closed successfully")
    assert message.type == MessageType.SESSION_CLOSED
    assert message.message == "Session closed successfully"


def test_historical_messages_message_valid():
    """Should create HistoricalMessagesMessage with messages list."""
    messages_list = [
        {"type": "user_message", "message": "Hello"},
        {"type": "agent_message", "message": "Hi there!"},
    ]
    message = HistoricalMessagesMessage(messages=messages_list)
    assert message.type == MessageType.HISTORICAL_MESSAGES
    assert message.messages == messages_list


def test_historical_messages_message_empty_list():
    """Should allow empty messages list."""
    message = HistoricalMessagesMessage(messages=[])
    assert message.messages == []


def test_historical_messages_message_missing_field_raises():
    """Should raise ValidationError when messages field is missing."""
    with pytest.raises(ValidationError):
        HistoricalMessagesMessage()


def test_agent_processing_start_message_valid():
    """Should create AgentProcessingStartMessage with correct type."""
    message = AgentProcessingStartMessage()
    assert message.type == MessageType.AGENT_PROCESSING_START


def test_agent_processing_end_message_valid():
    """Should create AgentProcessingEndMessage with correct type."""
    message = AgentProcessingEndMessage()
    assert message.type == MessageType.AGENT_PROCESSING_END


# ============================================================================
# Union Type Tests
# ============================================================================


def test_mission_commander_server_message_union():
    """Should accept all MissionCommander message types."""
    messages = [
        ConnectedMessage(message="Connected"),
        AgentMessage(message="Hello"),
        AgentHandoverMessage(agent="agent1", message="Handover"),
        MissionCreatedMessage(mission={"id": "m1"}, enrollment={"id": "e1"}, message="Created"),
        PongMessage(),
        ErrorMessage(message="Error"),
    ]

    for msg in messages:
        # Check that message is an instance of one of the union types
        union_types = MissionCommanderServerMessage.__args__
        assert any(
            isinstance(msg, msg_type) for msg_type in union_types
        ), f"Message {type(msg).__name__} should be part of MissionCommanderServerMessage union"


def test_mission_ally_server_message_union():
    """Should accept all MissionAlly message types."""
    messages = [
        ConnectedMessage(message="Connected"),
        AgentMessage(message="Hello"),
        AgentHandoverMessage(agent="agent1", message="Handover"),
        PongMessage(),
        ErrorMessage(message="Error"),
        CheckpointUpdateMessage(completed_checkpoints=["cp1"], progress=25.0),
        SessionClosedMessage(message="Closed"),
        HistoricalMessagesMessage(messages=[]),
        AgentProcessingStartMessage(),
        AgentProcessingEndMessage(),
    ]

    for msg in messages:
        # Check that message is an instance of one of the union types
        union_types = MissionAllyServerMessage.__args__
        assert any(
            isinstance(msg, msg_type) for msg_type in union_types
        ), f"Message {type(msg).__name__} should be part of MissionAllyServerMessage union"


# ============================================================================
# Model Serialization Tests
# ============================================================================


def test_user_message_model_dump():
    """Should serialize UserMessage to dict."""
    message = UserMessage(message="Hello")
    data = message.model_dump(mode="json")
    assert data == {"type": "user_message", "message": "Hello"}


def test_agent_message_model_dump():
    """Should serialize AgentMessage to dict."""
    message = AgentMessage(message="Response")
    data = message.model_dump(mode="json")
    assert data == {"type": "agent_message", "message": "Response"}


def test_checkpoint_update_message_model_dump():
    """Should serialize CheckpointUpdateMessage to dict."""
    message = CheckpointUpdateMessage(completed_checkpoints=["cp1", "cp2"], progress=66.67)
    data = message.model_dump(mode="json")
    assert data == {
        "type": "checkpoint_update",
        "completed_checkpoints": ["cp1", "cp2"],
        "progress": 66.67,
    }


def test_mission_created_message_model_dump():
    """Should serialize MissionCreatedMessage to dict."""
    mission_data = {"id": "m1", "title": "Test"}
    enrollment_data = {"id": "e1", "user_id": "u1"}
    message = MissionCreatedMessage(
        mission=mission_data, enrollment=enrollment_data, message="Created"
    )
    data = message.model_dump(mode="json")
    assert data["type"] == "mission_created"
    assert data["mission"] == mission_data
    assert data["enrollment"] == enrollment_data
    assert data["message"] == "Created"


def test_agent_processing_start_message_model_dump():
    """Should serialize AgentProcessingStartMessage to dict."""
    message = AgentProcessingStartMessage()
    data = message.model_dump(mode="json")
    assert data == {"type": "agent_processing_start"}


def test_agent_processing_end_message_model_dump():
    """Should serialize AgentProcessingEndMessage to dict."""
    message = AgentProcessingEndMessage()
    data = message.model_dump(mode="json")
    assert data == {"type": "agent_processing_end"}


# ============================================================================
# Edge Cases
# ============================================================================


def test_progress_can_be_zero():
    """Should allow progress of 0.0."""
    message = CheckpointUpdateMessage(completed_checkpoints=[], progress=0.0)
    assert message.progress == 0.0


def test_progress_can_be_100():
    """Should allow progress of 100.0."""
    message = CheckpointUpdateMessage(completed_checkpoints=["cp1", "cp2", "cp3"], progress=100.0)
    assert message.progress == 100.0


def test_progress_can_be_float():
    """Should allow fractional progress values."""
    message = CheckpointUpdateMessage(completed_checkpoints=["cp1"], progress=33.333)
    assert message.progress == 33.333


def test_agent_handover_message_can_have_empty_strings():
    """Should allow empty strings in agent and message fields."""
    message = AgentHandoverMessage(agent="", message="")
    assert message.agent == ""
    assert message.message == ""


def test_error_message_can_have_empty_string():
    """Should allow empty string in error message."""
    message = ErrorMessage(message="")
    assert message.message == ""
