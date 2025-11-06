"""WebSocket message models for Mission Commander and Mission Ally"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """WebSocket message types"""

    USER_MESSAGE = "user_message"
    AGENT_MESSAGE = "agent_message"
    AGENT_HANDOVER = "agent_handover"
    MISSION_CREATED = "mission_created"
    CONNECTED = "connected"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"
    CHECKPOINT_UPDATE = "checkpoint_update"
    SESSION_CLOSED = "session_closed"
    HISTORICAL_MESSAGES = "historical_messages"
    AGENT_PROCESSING_START = "agent_processing_start"
    AGENT_PROCESSING_END = "agent_processing_end"


# ============================================================================
# Client → Server Messages
# ============================================================================


class UserMessage(BaseModel):
    """User message from client"""

    type: Literal[MessageType.USER_MESSAGE] = MessageType.USER_MESSAGE
    message: str = Field(..., min_length=1)


class PingMessage(BaseModel):
    """Ping message for connection keepalive"""

    type: Literal[MessageType.PING] = MessageType.PING


ClientMessage = UserMessage | PingMessage


# ============================================================================
# Server → Client Messages
# ============================================================================


class ConnectedMessage(BaseModel):
    """Initial connection confirmation"""

    type: Literal[MessageType.CONNECTED] = MessageType.CONNECTED
    message: str


class AgentMessage(BaseModel):
    """Agent response during conversation"""

    type: Literal[MessageType.AGENT_MESSAGE] = MessageType.AGENT_MESSAGE
    message: str


class AgentHandoverMessage(BaseModel):
    """Notification when transferring between agents"""

    type: Literal[MessageType.AGENT_HANDOVER] = MessageType.AGENT_HANDOVER
    agent: str
    message: str


class MissionCreatedMessage(BaseModel):
    """Final message with created mission details"""

    type: Literal[MessageType.MISSION_CREATED] = MessageType.MISSION_CREATED
    mission: dict[str, Any]
    enrollment: dict[str, Any]
    message: str


class PongMessage(BaseModel):
    """Response to ping for connection keepalive"""

    type: Literal[MessageType.PONG] = MessageType.PONG


class ErrorMessage(BaseModel):
    """Error notification"""

    type: Literal[MessageType.ERROR] = MessageType.ERROR
    message: str


class CheckpointUpdateMessage(BaseModel):
    """Checkpoint progress update"""

    type: Literal[MessageType.CHECKPOINT_UPDATE] = MessageType.CHECKPOINT_UPDATE
    completed_checkpoints: list[str]
    progress: float


class SessionClosedMessage(BaseModel):
    """Session closed notification"""

    type: Literal[MessageType.SESSION_CLOSED] = MessageType.SESSION_CLOSED
    message: str


class HistoricalMessagesMessage(BaseModel):
    """Historical messages from previous session"""

    type: Literal[MessageType.HISTORICAL_MESSAGES] = MessageType.HISTORICAL_MESSAGES
    messages: list[dict]


class AgentProcessingStartMessage(BaseModel):
    """Notification that agent has started processing a user message"""

    type: Literal[MessageType.AGENT_PROCESSING_START] = MessageType.AGENT_PROCESSING_START


class AgentProcessingEndMessage(BaseModel):
    """Notification that agent has finished processing a user message"""

    type: Literal[MessageType.AGENT_PROCESSING_END] = MessageType.AGENT_PROCESSING_END


# Union types for each endpoint
MissionCommanderServerMessage = (
    ConnectedMessage
    | AgentMessage
    | AgentHandoverMessage
    | MissionCreatedMessage
    | PongMessage
    | ErrorMessage
)

MissionAllyServerMessage = (
    ConnectedMessage
    | AgentMessage
    | AgentHandoverMessage
    | PongMessage
    | ErrorMessage
    | CheckpointUpdateMessage
    | SessionClosedMessage
    | HistoricalMessagesMessage
    | AgentProcessingStartMessage
    | AgentProcessingEndMessage
)
