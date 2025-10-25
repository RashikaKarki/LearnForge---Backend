"""WebSocket endpoint for Mission Commander agent interaction"""

import json
from typing import Dict

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from google.adk.tools import ToolContext
from google.adk.sessions import InMemorySessionService, Session

from app.agents.mission_commander.agent import root_agent
from app.dependencies.auth import get_current_user
from app.initializers.firestore import get_db
from app.models.mission import MissionCreate
from app.models.user import User
from app.services.mission_service import MissionService
from app.services.session_log_service import SessionLogService

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections and agent sessions for Mission Commander"""

    def __init__(self):
        # Store active WebSocket connections: {session_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # Store agent sessions: {session_id: Session}
        self.agent_sessions: Dict[str, Session] = {}
        # Store session service
        self.session_service = InMemorySessionService()

    async def connect(self, session_id: str, websocket: WebSocket, user_id: str):
        """Accept new WebSocket connection and initialize agent session"""
        await websocket.accept()
        self.active_connections[session_id] = websocket

        # Create agent session with user context
        session = Session(session_id, service=self.session_service)
        session.state["creator_id"] = user_id
        self.agent_sessions[session_id] = session

    def disconnect(self, session_id: str):
        """Remove WebSocket connection and clean up session"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.agent_sessions:
            del self.agent_sessions[session_id]

    async def send_message(self, session_id: str, message: dict):
        """Send JSON message to connected client"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_json(message)

    def get_session(self, session_id: str) -> Session | None:
        """Get agent session for given session ID"""
        return self.agent_sessions.get(session_id)


# Global connection manager instance
manager = ConnectionManager()


@router.websocket("/ws")
async def mission_commander_websocket(
    websocket: WebSocket,
    session_id: str,
):
    """
    WebSocket endpoint for Mission Commander agent interaction.

    Prerequisites:
    1. Call POST /api/v1/sessions to create a session and get session_id
    2. Use the returned session_id to connect to this WebSocket

    Flow:
    1. Client connects with session_id (from sessions endpoint) and authentication token
    2. Server validates session exists and belongs to authenticated user
    3. Agent automatically starts with Pathfinder
    4. Client sends user messages, receives agent responses
    5. When mission is created, server sends mission JSON and updates session
    6. Connection closes

    Message Format:
    - From client: {"type": "user_message", "content": "user text"}
    - From server: {"type": "agent_message", "content": "agent text"}
    - From server: {"type": "mission_created", "mission": {...}}
    - From server: {"type": "error", "message": "error details"}
    """
    db = None
    session_log_service = None
    user_id = None
    
    try:
        # Extract token from query params
        token = websocket.query_params.get("token")
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
            return

        # Get database connection from app state
        db = websocket.app.state.db
        session_log_service = SessionLogService(db)
        
        # Validate session exists in database
        try:
            session_log = session_log_service.get_session(session_id)
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid session_id")
            return
        
        # Verify session is active
        if session_log.status != "active":
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason=f"Session is {session_log.status}")
            return
        
        # Use user_id from session (more secure than query param)
        user_id = session_log.user_id

        # Connect and initialize
        await manager.connect(session_id, websocket, user_id)
        mission_service = MissionService(db)

        # Send connection confirmation
        await manager.send_message(
            session_id,
            {
                "type": "connected",
                "message": "Connected to Mission Commander. Starting your learning journey...",
            },
        )

        # Get agent session
        session = manager.get_session(session_id)
        if not session:
            await manager.send_message(
                session_id, {"type": "error", "message": "Failed to initialize session"}
            )
            return

        # Create tool context
        ctx = ToolContext(session=session)

        # Listen for client messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()
                message_type = data.get("type")
                content = data.get("content", "")

                if message_type == "user_message":
                    # Process user message through agent
                    await process_agent_flow(
                        ctx, session_id, manager, mission_service, session_log_service, content
                    )
                    
                    # Check if mission was created (agent completed)
                    if "mission_create" in ctx.session.state:
                        # Mission created, close connection
                        break

                elif message_type == "ping":
                    # Heartbeat
                    await manager.send_message(session_id, {"type": "pong"})

            except WebSocketDisconnect:
                # Mark session as abandoned if disconnected without completion
                if session_log_service and "mission_create" not in ctx.session.state:
                    try:
                        session_log_service.mark_session_abandoned(session_id)
                    except Exception:
                        pass
                manager.disconnect(session_id)
                break
            except json.JSONDecodeError:
                await manager.send_message(
                    session_id,
                    {"type": "error", "message": "Invalid JSON format"},
                )
            except Exception as e:
                # Mark session as error
                if session_log_service:
                    try:
                        session_log_service.mark_session_error(session_id)
                    except Exception:
                        pass
                await manager.send_message(
                    session_id,
                    {"type": "error", "message": f"Error processing message: {str(e)}"},
                )

    except Exception as e:
        # Mark session as error on exception
        if session_log_service:
            try:
                session_log_service.mark_session_error(session_id)
            except Exception:
                pass
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        manager.disconnect(session_id)


async def process_agent_flow(
    ctx: ToolContext,
    session_id: str,
    manager: ConnectionManager,
    mission_service: MissionService,
    session_log_service: SessionLogService,
    user_message: str = "",
):
    """
    Process the agent flow and stream events to WebSocket client.

    Args:
        ctx: Tool context with session state
        session_id: WebSocket session identifier
        manager: Connection manager instance
        mission_service: Service for mission database operations
        session_log_service: Service for session log operations
        user_message: Latest user message (if any)
    """
    try:
        # Run agent and stream responses
        # The agent will handle conversation flow internally
        response = await root_agent.run_async(ctx, user_message=user_message)
        
        # Send agent's response to client
        if response:
            await manager.send_message(
                session_id,
                {"type": "agent_message", "content": response},
            )

        # After agent completes, check if mission was created
        if "mission_create" in ctx.session.state:
            mission_data: MissionCreate = ctx.session.state["mission_create"]
            user_id = ctx.session.state.get("creator_id")

            # Save mission to database and auto-enroll creator
            mission, enrollment = mission_service.create_mission_with_enrollment(
                mission_data, user_id
            )

            # Update session as completed with mission ID
            session_log_service.mark_session_completed(session_id, mission_id=mission.id)

            # Send completed mission to client
            await manager.send_message(
                session_id,
                {
                    "type": "mission_created",
                    "mission": mission.model_dump(mode="json"),
                    "enrollment": enrollment.model_dump(mode="json"),
                    "message": "Mission created successfully!",
                },
            )

    except Exception as e:
        # Mark session as error
        try:
            session_log_service.mark_session_error(session_id)
        except Exception:
            pass
        
        await manager.send_message(
            session_id,
            {"type": "error", "message": f"Agent error: {str(e)}"},
        )
