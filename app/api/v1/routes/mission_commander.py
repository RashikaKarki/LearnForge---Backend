"""WebSocket endpoint for Mission Commander agent interaction"""

import json
import logging
from enum import Enum
from typing import Any, Dict, Literal, Optional, Union

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, Session
from google.genai.types import Content, Part
from pydantic import BaseModel, Field

from app.agents.mission_commander.agent import root_agent
from app.models.mission import MissionCreate
from app.services.mission_service import MissionService
from app.services.session_log_service import SessionLogService

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Message Type Definitions
# ============================================================================


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


# Client → Server Messages
class UserMessage(BaseModel):
    """User message from client"""

    type: Literal[MessageType.USER_MESSAGE] = MessageType.USER_MESSAGE
    message: str = Field(..., min_length=1)


class PingMessage(BaseModel):
    """Ping message for connection keepalive"""

    type: Literal[MessageType.PING] = MessageType.PING


ClientMessage = Union[UserMessage, PingMessage]


# Server → Client Messages
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
    mission: Dict[str, Any]
    enrollment: Dict[str, Any]
    message: str


class PongMessage(BaseModel):
    """Response to ping for connection keepalive"""

    type: Literal[MessageType.PONG] = MessageType.PONG


class ErrorMessage(BaseModel):
    """Error notification"""

    type: Literal[MessageType.ERROR] = MessageType.ERROR
    message: str


ServerMessage = Union[
    ConnectedMessage,
    AgentMessage,
    AgentHandoverMessage,
    MissionCreatedMessage,
    PongMessage,
    ErrorMessage,
]


# ============================================================================
# Connection Manager
# ============================================================================


class ConnectionManager:
    """Manages WebSocket connections and agent sessions"""

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.agent_sessions: Dict[str, Session] = {}
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=root_agent, app_name="mission-commander", session_service=self.session_service
        )

    async def connect(self, session_id: str, websocket: WebSocket, user_id: str):
        """Initialize WebSocket connection and create agent session"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        session = await self.session_service.create_session(
            app_name="mission-commander",
            user_id=user_id,
            session_id=session_id,
            state={"creator_id": user_id},
        )
        self.agent_sessions[session_id] = session
        logger.info(f"Connection established: session={session_id}, user={user_id}")

    def disconnect(self, session_id: str):
        """Clean up connection and session resources"""
        self.active_connections.pop(session_id, None)
        self.agent_sessions.pop(session_id, None)
        logger.info(f"Connection closed: session={session_id}")

    async def send_message(self, session_id: str, message: ServerMessage):
        """Send typed message to client"""
        websocket = self.active_connections.get(session_id)
        if websocket:
            await websocket.send_json(message.model_dump(mode="json"))

    def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve agent session by ID"""
        return self.agent_sessions.get(session_id)


manager = ConnectionManager()


# ============================================================================
# Helper Functions
# ============================================================================


async def validate_session(
    websocket: WebSocket, session_id: str, token: Optional[str]
) -> Optional[tuple[SessionLogService, str]]:
    """
    Validate session authenticity and status.
    Returns (SessionLogService, user_id) if valid, None otherwise.
    """
    if not token:
        logger.warning(f"Missing authentication token for session {session_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
        return None

    try:
        db = websocket.app.state.db
        session_log_service = SessionLogService(db)
        session_log = session_log_service.get_session(session_id)

        if session_log.status != "active":
            logger.warning(f"Session {session_id} is {session_log.status}, not active")
            await websocket.close(
                code=status.WS_1008_POLICY_VIOLATION, reason=f"Session is {session_log.status}"
            )
            return None

        return session_log_service, session_log.user_id

    except Exception as e:
        logger.error(f"Session validation failed for {session_id}: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid session")
        return None


async def handle_disconnect(session_id: str, user_id: str, session_log_service: SessionLogService):
    """Mark incomplete sessions as abandoned on disconnect"""
    try:
        updated_session = await manager.session_service.get_session(
            app_name="mission-commander", user_id=user_id, session_id=session_id
        )

        if "mission_create" not in updated_session.state:
            session_log_service.mark_session_abandoned(session_id)
            logger.info(f"Session {session_id} marked as abandoned")
    except Exception as e:
        logger.error(f"Error handling disconnect for {session_id}: {e}")
    finally:
        manager.disconnect(session_id)


async def process_agent_flow(
    session_id: str,
    user_id: str,
    manager: ConnectionManager,
    mission_service: MissionService,
    session_log_service: SessionLogService,
    user_message: str,
):
    """
    Process user message through agent system and handle responses.
    Streams agent responses and handles mission creation.
    """
    try:
        user_content = Content(parts=[Part(text=user_message)])
        current_agent = None

        # Stream agent events
        for event in manager.runner.run(
            user_id=user_id, session_id=session_id, new_message=user_content
        ):
            # Detect agent transfers
            if hasattr(event, "actions") and event.actions:
                if hasattr(event.actions, "transfer_to_agent") and event.actions.transfer_to_agent:
                    transfer_target = event.actions.transfer_to_agent
                    logger.info(f"Agent handover to {transfer_target} in session {session_id}")

                    if transfer_target == "mission_curator":
                        await manager.send_message(
                            session_id,
                            AgentHandoverMessage(
                                agent="mission_curator",
                                message="Creating your personalized learning mission...",
                            ),
                        )

            # Track current agent
            if hasattr(event, "author") and event.author:
                current_agent = event.author

            # Send text content to client (skip internal mission_curator messages)
            if hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts"):
                    for part in event.content.parts:
                        if (
                            hasattr(part, "text")
                            and part.text
                            and current_agent != "mission_curator"
                        ):
                            await manager.send_message(session_id, AgentMessage(message=part.text))

        # Check if mission was created
        updated_session = await manager.session_service.get_session(
            app_name="mission-commander", user_id=user_id, session_id=session_id
        )

        if "mission_create" in updated_session.state:
            mission_data_dict = updated_session.state["mission_create"]
            creator_id = updated_session.state.get("creator_id")

            # Convert to MissionCreate model
            mission_data = (
                MissionCreate(**mission_data_dict)
                if isinstance(mission_data_dict, dict)
                else mission_data_dict
            )

            # Create mission and enroll user
            mission, enrollment = mission_service.create_mission_with_enrollment(
                mission_data, creator_id
            )
            logger.info(
                f"Mission {mission.id} created for user {creator_id} in session {session_id}"
            )

            # Update session status
            session_log_service.mark_session_completed(session_id, mission_id=mission.id)

            # Send final message with mission details
            await manager.send_message(
                session_id,
                MissionCreatedMessage(
                    mission=mission.model_dump(mode="json"),
                    enrollment=enrollment.model_dump(mode="json"),
                    message="Mission created successfully!",
                ),
            )

    except Exception as e:
        logger.error(f"Agent processing error in session {session_id}: {e}", exc_info=True)
        session_log_service.mark_session_error(session_id)
        await manager.send_message(session_id, ErrorMessage(message=f"Processing error: {str(e)}"))


# ============================================================================
# WebSocket Endpoint
# ============================================================================


@router.websocket("/ws")
async def mission_commander_websocket(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for conversational mission creation.

    Prerequisites:
    1. Create session: POST /api/v1/sessions → get session_id
    2. Connect with: ws://host/api/v1/mission-commander/ws?session_id=X&token=Y

    Flow:
    1. Client connects → receives 'connected' message
    2. Client sends 'user_message' → agent responds
    3. Conversation continues until mission requirements gathered
    4. Agent creates mission → client receives 'mission_created'
    5. Connection closes
    """
    session_log_service = None
    user_id = None

    try:
        # Validate session and authenticate
        token = websocket.query_params.get("token")
        validation_result = await validate_session(websocket, session_id, token)
        if not validation_result:
            return

        session_log_service, user_id = validation_result

        # Initialize connection and services
        await manager.connect(session_id, websocket, user_id)
        mission_service = MissionService(websocket.app.state.db)

        # Send connection confirmation
        await manager.send_message(
            session_id,
            ConnectedMessage(
                message="Connected to Mission Commander. Starting your learning journey..."
            ),
        )

        # Retrieve agent session
        session = manager.get_session(session_id)
        if not session:
            logger.error(f"Agent session creation failed for {session_id}")
            await manager.send_message(
                session_id, ErrorMessage(message="Failed to initialize session")
            )
            return

        # Message processing loop
        while True:
            try:
                data = await websocket.receive_json()
                message_type = data.get("type")

                # Handle user messages
                if message_type == MessageType.USER_MESSAGE:
                    client_msg = UserMessage(**data)
                    await process_agent_flow(
                        session_id,
                        user_id,
                        manager,
                        mission_service,
                        session_log_service,
                        client_msg.message,
                    )

                    # Check if mission created (conversation complete)
                    updated_session = await manager.session_service.get_session(
                        app_name="mission-commander", user_id=user_id, session_id=session_id
                    )
                    if "mission_create" in updated_session.state:
                        logger.info(f"Mission created, closing session {session_id}")
                        break

                # Handle ping keepalive
                elif message_type == MessageType.PING:
                    PingMessage(**data)  # Validate
                    await manager.send_message(session_id, PongMessage())

                # Invalid message type
                else:
                    raise ValueError(f"Unknown message type: {message_type}")

            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid message format in session {session_id}: {e}")
                await manager.send_message(
                    session_id, ErrorMessage(message=f"Invalid message format: {str(e)}")
                )

            except WebSocketDisconnect:
                logger.info(f"Client disconnected: session={session_id}")
                await handle_disconnect(session_id, user_id, session_log_service)
                break

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON from session {session_id}: {e}")
                await manager.send_message(session_id, ErrorMessage(message="Invalid JSON format"))

            except Exception as e:
                logger.error(
                    f"Message processing error in session {session_id}: {e}", exc_info=True
                )
                if session_log_service:
                    session_log_service.mark_session_error(session_id)
                await manager.send_message(
                    session_id, ErrorMessage(message=f"Processing error: {str(e)}")
                )

    except Exception as e:
        logger.error(f"Fatal WebSocket error in session {session_id}: {e}", exc_info=True)
        if session_log_service:
            try:
                session_log_service.mark_session_error(session_id)
            except Exception as se:
                logger.error(f"Failed to mark session error: {se}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        manager.disconnect(session_id)
