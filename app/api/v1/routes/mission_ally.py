"""WebSocket endpoint for Mission Ally agent interaction - Optimized"""

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from firebase_admin import auth
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.genai.types import Content, Part


try:
    from google.cloud.sql.connector import Connector
except ImportError:
    Connector = None

from app.agents.mission_ally.agent import root_agent
from app.core.config import settings
from app.models.enrollment import Enrollment, EnrollmentUpdate
from app.models.enrollment_session_log import EnrollmentSessionLog
from app.models.mission import Mission
from app.models.user import User, UserEnrolledMission
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
    PongMessage,
    SessionClosedMessage,
    UserMessage,
)
from app.models.websocket_messages import MissionAllyServerMessage as ServerMessage
from app.services.enrollment_service import EnrollmentService
from app.services.enrollment_session_log_service import EnrollmentSessionLogService
from app.services.mission_service import MissionService
from app.services.user_service import UserService


logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Error Handling Utilities
# ============================================================================


def _sanitize_error_message(error_msg: str) -> str:
    """
    Sanitize error messages to prevent leaking sensitive information like database URLs.
    Returns a safe, user-friendly error message.
    """
    sanitized = error_msg

    # Check for database URL patterns
    if "postgresql://" in sanitized or "postgres://" in sanitized:
        if "module not found" in sanitized.lower() or "not found for URL" in sanitized.lower():
            return "Database driver not found"
        return "Database connection error"

    # Check for other database-related errors
    if "DATABASE_URL" in sanitized:
        return "Database configuration error"

    if "postgres" in sanitized.lower() and "database" in sanitized.lower():
        if "module" in sanitized.lower():
            return "Database driver not found"
        return "Database configuration error"

    if (
        "postgres" in sanitized.lower() or "database" in sanitized.lower()
    ) and "module" in sanitized.lower():
        return "Database driver not found"

    if "No module named" in sanitized or "ImportError" in sanitized:
        if "psycopg2" in sanitized.lower() or "asyncpg" in sanitized.lower():
            return "Database driver not found"
        return "Database driver not found"

    return sanitized


def _handle_http_exception(e: Exception, resource_name: str, resource_id: str) -> ValueError:
    """
    Handle HTTPException from service calls and convert to ValueError with sanitized message.

    Args:
        e: The exception to handle
        resource_name: Name of the resource (e.g., "Mission", "Enrollment")
        resource_id: ID of the resource

    Returns:
        ValueError with sanitized error message
    """
    if isinstance(e, HTTPException):
        if e.status_code == 404:
            return ValueError(f"{resource_name} not found: {resource_id}")
        else:
            logger.error(
                f"[_handle_http_exception] Error retrieving {resource_name.lower()}: {e}",
                exc_info=True,
            )
            return ValueError(f"Failed to retrieve {resource_name.lower()}: {str(e)}")
    else:
        logger.error(
            f"[_handle_http_exception] Unexpected error retrieving {resource_name.lower()}: {e}",
            exc_info=True,
        )
        return ValueError(f"Failed to retrieve {resource_name.lower()}: {str(e)}")


async def _close_websocket_with_error(
    websocket: WebSocket,
    session_id: str | None,
    error: Exception,
    close_code: int = status.WS_1011_INTERNAL_ERROR,
) -> None:
    """Close WebSocket connection with sanitized error message."""
    sanitized = _sanitize_error_message(str(error))
    logger.error(f"[_close_websocket_with_error] WebSocket error: {sanitized}", exc_info=True)

    try:
        if websocket.client_state.name == "CONNECTED":
            await websocket.send_json(ErrorMessage(message=sanitized).model_dump(mode="json"))
    except Exception:
        pass

    try:
        safe_reason = sanitized[:123] if len(sanitized) <= 123 else "Internal server error"
        if websocket.client_state.name == "CONNECTED":
            await websocket.close(code=close_code, reason=safe_reason)
    except Exception:
        pass


def _get_mission_id_from_session_state(session_state: dict) -> str | None:
    """
    Extract mission_id from session state dictionary.
    Handles both dict and object representations.
    """
    enrolled_mission = session_state.get("enrolled_mission")
    if enrolled_mission:
        if isinstance(enrolled_mission, dict):
            mission_id = enrolled_mission.get("mission_id")
        elif hasattr(enrolled_mission, "mission_id"):
            mission_id = enrolled_mission.mission_id
        else:
            mission_id = None

        if mission_id:
            return mission_id

    mission_details = session_state.get("mission_details")
    if mission_details:
        if isinstance(mission_details, dict):
            return mission_details.get("id")
        elif hasattr(mission_details, "id"):
            return mission_details.id

    return None


# ============================================================================
# Session Context (Cache Layer)
# ============================================================================


class SessionContext:
    """
    Caches all database-fetched data and ADK session during WebSocket session lifecycle.
    Eliminates redundant database calls by fetching once and reusing.
    """

    def __init__(self, db, user_id: str, mission_id: str, session_service):
        self.db = db
        self.user_id = user_id
        self.mission_id = mission_id
        self.session_service = session_service

        # Services (initialized once, reused throughout)
        self.user_service = UserService(db)
        self.mission_service = MissionService(db)
        self.enrollment_service = EnrollmentService(db)
        self.enrollment_session_log_service = EnrollmentSessionLogService(db)

        # Cached data (fetched once during initialization)
        self._user: User | None = None
        self._mission: Mission | None = None
        self._enrollment: Enrollment | None = None
        self._enrolled_mission: UserEnrolledMission | None = None
        self._enrollment_session_log: EnrollmentSessionLog | None = None
        self._adk_session = None  # Cached ADK session
        self._initialized = False

    async def initialize(self) -> tuple[dict, bool]:
        """
        Fetch and cache all required data for the session.
        Returns (initial_state_dict, was_started) where was_started indicates if session was already started.
        """
        if self._initialized:
            raise ValueError("SessionContext already initialized")

        # Fetch user
        try:
            self._user = self.user_service.get_user(self.user_id)
        except Exception as e:
            logger.error(
                f"[SessionContext.initialize] Failed to retrieve user {self.user_id}: {e}",
                exc_info=True,
            )
            raise ValueError(f"User not found: {self.user_id}") from e

        # Fetch mission
        try:
            self._mission = self.mission_service.get_mission(self.mission_id)
        except Exception as e:
            raise _handle_http_exception(e, "Mission", self.mission_id) from e

        # Fetch enrollment
        try:
            self._enrollment = self.enrollment_service.get_enrollment(self.user_id, self.mission_id)
        except Exception as e:
            raise _handle_http_exception(
                e, f"Enrollment for user {self.user_id}", self.mission_id
            ) from e

        # Fetch enrolled mission
        try:
            self._enrolled_mission = self.user_service.get_enrolled_mission(
                self.user_id, self.mission_id
            )
        except Exception as e:
            logger.error(
                f"[SessionContext.initialize] Failed to retrieve enrolled mission: {e}",
                exc_info=True,
            )
            raise ValueError(f"Failed to retrieve enrolled mission: {str(e)}") from e

        # Fetch enrollment session log
        try:
            self._enrollment_session_log = self.enrollment_session_log_service.get_session_log_by_user_and_enrollment_and_mission(
                user_id=self.user_id,
                enrollment_id=self._enrollment.id,
                mission_id=self.mission_id,
            )
            if not self._enrollment_session_log:
                raise ValueError(
                    f"Enrollment session log not found for user {self.user_id}, "
                    f"enrollment {self._enrollment.id}, mission {self.mission_id}"
                )
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to retrieve enrollment session log: {str(e)}") from e

        # Validate session status
        if self._enrollment_session_log.status == "completed":
            raise ValueError("Cannot start WebSocket: enrollment session is already completed")

        was_started = self._enrollment_session_log.status == "started"
        if self._enrollment_session_log.status == "created":
            self.enrollment_session_log_service.mark_session_started(
                self._enrollment_session_log.id
            )

        # Build initial state
        starting_index = _find_starting_checkpoint_index(self._enrolled_mission)
        initial_state = {
            "mission_id": self.mission_id,
            "user_profile": self._user.model_dump(mode="json"),
            "enrolled_mission": self._enrolled_mission.model_dump(mode="json"),
            "mission_details": self._mission.model_dump(mode="json"),
            "enrollment_session_log_id": self._enrollment_session_log.id,
            "current_checkpoint_index": starting_index,
            "current_checkpoint_goal": (
                "Ended"
                if starting_index == -1
                else self._enrolled_mission.byte_size_checkpoints[starting_index]
            ),
            "completed_checkpoints": self._enrolled_mission.completed_checkpoints or [],
        }

        self._initialized = True
        return initial_state, was_started

    async def get_or_create_adk_session(self, session_id: str, initial_state: dict):
        """
        Get existing ADK session or create new one if it doesn't exist.
        Caches the session for subsequent calls.
        """
        if self._adk_session is not None:
            return self._adk_session

        try:
            # Try to get existing session
            self._adk_session = await self.session_service.get_session(
                app_name="mission-ally",
                user_id=self.user_id,
                session_id=session_id,
            )
            if self._adk_session is None:
                raise ValueError(f"Session {session_id} not found (returned None)")
            logger.info(
                f"[SessionContext.get_or_create_adk_session] Retrieved existing ADK session: {session_id}"
            )
        except Exception as get_error:
            # Session doesn't exist, create it
            logger.info(
                f"[SessionContext.get_or_create_adk_session] ADK session not found, creating new one: {session_id}"
            )
            try:
                await self.session_service.create_session(
                    app_name="mission-ally",
                    user_id=self.user_id,
                    session_id=session_id,
                    state=initial_state,
                )
                logger.info(
                    f"[SessionContext.get_or_create_adk_session] Successfully created ADK session: {session_id}"
                )

                # Fetch the newly created session
                self._adk_session = await self.session_service.get_session(
                    app_name="mission-ally",
                    user_id=self.user_id,
                    session_id=session_id,
                )
            except Exception as create_error:
                error_details = {
                    "error": "Failed to create ADK session in database",
                    "app_name": "mission-ally",
                    "user_id": self.user_id,
                    "session_id": session_id,
                    "get_session_error": str(get_error),
                    "create_session_error": str(create_error),
                }
                logger.error(
                    f"[SessionContext.get_or_create_adk_session] ADK session creation failed: {error_details}",
                    exc_info=True,
                )
                sanitized = _sanitize_error_message(str(create_error))
                error_message = (
                    f"Failed to create session: {session_id}. "
                    f"Parameters used: app_name='mission-ally', user_id='{self.user_id}', session_id='{session_id}'. "
                    f"Get session error: {str(get_error)}. "
                    f"Create session error: {sanitized}"
                )
                raise ValueError(error_message) from create_error

        return self._adk_session

    async def refresh_adk_session(self, session_id: str):
        """
        Refresh the cached ADK session with latest data from database.
        Call this after operations that modify session state.
        """
        try:
            self._adk_session = await self.session_service.get_session(
                app_name="mission-ally",
                user_id=self.user_id,
                session_id=session_id,
            )
            return self._adk_session
        except Exception as e:
            logger.error(
                f"[SessionContext.refresh_adk_session] Failed to refresh ADK session: {e}",
                exc_info=True,
            )
            raise

    @property
    def adk_session(self):
        """Get cached ADK session (must call get_or_create_adk_session first)"""
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._adk_session

    @property
    def user(self) -> User:
        """Get cached user"""
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._user

    @property
    def mission(self) -> Mission:
        """Get cached mission"""
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._mission

    @property
    def enrollment(self) -> Enrollment:
        """Get cached enrollment"""
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._enrollment

    @property
    def enrolled_mission(self) -> UserEnrolledMission:
        """Get cached enrolled mission"""
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._enrolled_mission

    @property
    def enrollment_session_log(self) -> EnrollmentSessionLog:
        """Get cached enrollment session log"""
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._enrollment_session_log


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self._session_service = None
        self._runner = None
        self._connector = None

    def _create_cloud_sql_connection(self):
        """Create Cloud SQL connection using connector"""
        if Connector is None:
            raise ImportError(
                "cloud-sql-python-connector package is not installed. "
                "Install it with: pip install 'cloud-sql-python-connector[pg8000]'"
            )

        if self._connector is None:
            self._connector = Connector(refresh_strategy="LAZY")

        return self._connector.connect(
            settings.INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME,
        )

    @property
    def session_service(self):
        if self._session_service is None:
            try:
                if settings.use_cloud_sql_connector:
                    logger.info(
                        "[ConnectionManager.session_service] Initializing DatabaseSessionService with Cloud SQL Connector"
                    )
                    db_url = "postgresql+pg8000://"

                    self._session_service = DatabaseSessionService(
                        db_url=db_url,
                        creator=self._create_cloud_sql_connection,
                        pool_size=5,
                        max_overflow=2,
                        pool_timeout=30,
                        pool_recycle=1800,
                    )
                else:
                    logger.info(
                        "[ConnectionManager.session_service] Initializing DatabaseSessionService with DATABASE_URL"
                    )
                    db_url = settings.DATABASE_URL
                    if not db_url:
                        raise ValueError("DATABASE_URL is not configured")

                    if not (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
                        raise ValueError("Invalid database URL format")

                    db_url = db_url.strip()
                    self._session_service = DatabaseSessionService(db_url=db_url)
            except ValueError:
                raise
            except Exception as e:
                sanitized = _sanitize_error_message(str(e))
                logger.error(
                    f"[ConnectionManager.session_service] Failed to initialize DatabaseSessionService: {sanitized}",
                    exc_info=True,
                )
                raise ValueError(sanitized) from None
        return self._session_service

    @property
    def runner(self):
        if self._runner is None:
            session_service = self.session_service
            self._runner = Runner(
                agent=root_agent, app_name="mission-ally", session_service=session_service
            )
        return self._runner

    def disconnect(self, session_id: str):
        self.active_connections.pop(session_id, None)

    async def send_message(self, session_id: str, message: ServerMessage):
        websocket = self.active_connections.get(session_id)
        if websocket and websocket.client_state.name == "CONNECTED":
            try:
                await websocket.send_json(message.model_dump(mode="json"))
            except Exception:
                self.disconnect(session_id)

    def cleanup(self):
        """Cleanup Cloud SQL connector on shutdown"""
        if self._connector is not None:
            try:
                self._connector.close()
            except Exception as e:
                logger.error(f"[ConnectionManager.cleanup] Error closing Cloud SQL connector: {e}")


_manager_instance = None


def get_manager() -> ConnectionManager:
    """Get or create the ConnectionManager instance (lazy initialization)."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ConnectionManager()
    return _manager_instance


def _find_starting_checkpoint_index(enrolled_mission):
    all_checkpoints = enrolled_mission.byte_size_checkpoints
    completed = enrolled_mission.completed_checkpoints or []

    for idx, checkpoint in enumerate(all_checkpoints):
        if checkpoint not in completed:
            return idx

    return -1


async def _get_historical_messages(
    session_id: str, context: SessionContext
) -> HistoricalMessagesMessage:
    """
    Retrieve historical messages from the cached session.
    Returns a HistoricalMessagesMessage containing a list of message dicts.
    """
    try:
        session = context.adk_session
        if session is None:
            logger.warning(
                f"[_get_historical_messages] Session {session_id} not found when retrieving historical messages"
            )
            return HistoricalMessagesMessage(messages=[])

        if not hasattr(session, "events") or session.events is None:
            logger.debug(f"[_get_historical_messages] Session {session_id} has no events")
            return HistoricalMessagesMessage(messages=[])

        events = session.events
        messages = []
        for event in events:
            if not event:
                continue
            if hasattr(event, "author") and hasattr(event, "content") and event.content:
                if hasattr(event.content, "parts") and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            if event.author == "user":
                                messages.append(
                                    UserMessage(message=part.text).model_dump(mode="json")
                                )
                            else:
                                messages.append(
                                    AgentMessage(message=part.text).model_dump(mode="json")
                                )
        return HistoricalMessagesMessage(messages=messages)
    except Exception as e:
        logger.error(
            f"[_get_historical_messages] Failed to retrieve historical messages for session {session_id}: {e}",
            exc_info=True,
        )
        return HistoricalMessagesMessage(messages=[])


async def _update_progress_and_send_checkpoint_update(
    session_id: str, context: SessionContext, completed_checkpoints: list[str]
):
    """
    Update enrollment progress based on completed checkpoints and send checkpoint update message.
    Progress = (completed_checkpoints / total_checkpoints) * 100
    Uses cached mission data from context to avoid DB call.
    """
    manager = get_manager()
    try:
        mission = context.mission
        total_checkpoints = (
            len(mission.byte_size_checkpoints) if mission.byte_size_checkpoints else 1
        )
        progress = min(100.0, (len(completed_checkpoints) / total_checkpoints) * 100.0)

        enrollment_update = EnrollmentUpdate(
            progress=progress, completed_checkpoints=completed_checkpoints
        )
        context.enrollment_service.update_enrollment(
            context.user_id, context.mission_id, enrollment_update
        )

        await manager.send_message(
            session_id,
            CheckpointUpdateMessage(completed_checkpoints=completed_checkpoints, progress=progress),
        )
    except Exception as e:
        logger.error(
            f"[_update_progress_and_send_checkpoint_update] Failed to update progress for session {session_id}: {e}",
            exc_info=True,
        )


async def _handle_agent_transfer(event, session_id: str, manager: ConnectionManager):
    if not hasattr(event, "actions") or not event.actions:
        return False
    if not hasattr(event.actions, "transfer_to_agent") or not event.actions.transfer_to_agent:
        return False

    transfer_target = event.actions.transfer_to_agent

    # Handle wrapper agent transfer - this means mission is complete
    if transfer_target == "lumina_wrapper":
        return "close"

    await manager.send_message(
        session_id,
        AgentHandoverMessage(
            agent=transfer_target, message=f"Handing over to {transfer_target}..."
        ),
    )
    return True


async def _send_text_content(event, session_id: str, manager: ConnectionManager):
    if not hasattr(event, "content") or not event.content or not hasattr(event.content, "parts"):
        return

    for part in event.content.parts:
        if hasattr(part, "text") and part.text:
            await manager.send_message(session_id, AgentMessage(message=part.text))


async def _handle_mission_completion(
    session_id: str,
    context: SessionContext,
    completed_checkpoints: list[str],
    manager: ConnectionManager,
):
    """Handle mission completion: update progress to 100% and mark session as completed."""
    try:
        mission = context.mission
        total_checkpoints = (
            len(mission.byte_size_checkpoints) if mission.byte_size_checkpoints else 1
        )

        # Ensure all checkpoints are marked as completed
        if len(completed_checkpoints) < total_checkpoints:
            all_checkpoints = mission.byte_size_checkpoints or []
            completed_checkpoints = all_checkpoints.copy()

        # Update enrollment progress to 100%
        enrollment_update = EnrollmentUpdate(
            progress=100.0, completed_checkpoints=completed_checkpoints
        )
        context.enrollment_service.update_enrollment(
            context.user_id, context.mission_id, enrollment_update
        )

        # Mark enrollment session log as completed
        context.enrollment_session_log_service.mark_session_completed(
            context.enrollment_session_log.id
        )
    except Exception as e:
        logger.error(f"[_handle_mission_completion] Failed to complete mission: {e}", exc_info=True)

    # Send closing message and close connection
    await manager.send_message(
        session_id,
        SessionClosedMessage(message="Congratulations! You've completed the mission!"),
    )
    await asyncio.sleep(0.1)

    websocket = manager.active_connections.get(session_id)
    if websocket:
        try:
            await websocket.close()
        except Exception:
            pass
    manager.disconnect(session_id)


async def process_agent_flow(session_id: str, context: SessionContext, user_message: str):
    """Process agent flow for a user message, using cached context data."""
    manager = get_manager()
    try:
        # Send processing start notification
        await manager.send_message(session_id, AgentProcessingStartMessage())

        # Get completed checkpoints before processing (from cached session)
        session_before = context.adk_session
        completed_checkpoints_before = (
            session_before.state.get("completed_checkpoints", [])
            if session_before and session_before.state
            else []
        )

        user_content = Content(parts=[Part(text=user_message)])
        wrapper_transferred = False

        for event in manager.runner.run(
            user_id=context.user_id, session_id=session_id, new_message=user_content
        ):
            transfer_result = await _handle_agent_transfer(event, session_id, manager)
            if transfer_result == "close":
                wrapper_transferred = True
            await _send_text_content(event, session_id, manager)

        # Refresh session to get latest state
        await context.refresh_adk_session(session_id)
        session_after = context.adk_session

        # Handle mission completion if wrapper was transferred
        if wrapper_transferred:
            if session_after and session_after.state:
                completed_checkpoints = session_after.state.get("completed_checkpoints", [])
                await _handle_mission_completion(
                    session_id, context, completed_checkpoints, manager
                )
            # Send processing end notification before returning
            try:
                await manager.send_message(session_id, AgentProcessingEndMessage())
            except Exception:
                pass
            return

        # Check if completed_checkpoints changed (mark_complete was called)
        if session_after and session_after.state:
            completed_checkpoints_after = session_after.state.get("completed_checkpoints", [])
            if len(completed_checkpoints_after) > len(completed_checkpoints_before):
                await _update_progress_and_send_checkpoint_update(
                    session_id, context, completed_checkpoints_after
                )

        await _check_and_mark_completed(session_id, context)

        # Send processing end notification
        await manager.send_message(session_id, AgentProcessingEndMessage())
    except Exception as e:
        logger.error(f"[_process_agent_flow] Agent processing error: {e}", exc_info=True)
        # Send processing end even on error
        try:
            await manager.send_message(session_id, AgentProcessingEndMessage())
        except Exception:
            pass
        await manager.send_message(session_id, ErrorMessage(message=f"Processing error: {str(e)}"))


async def _check_and_mark_completed(session_id: str, context: SessionContext):
    """Check if all checkpoints are completed and mark session as completed if so."""
    session = context.adk_session

    if not session or not session.state:
        return

    if session.state.get("current_checkpoint_index", -1) == -1:
        if context.enrollment_session_log.status != "completed":
            context.enrollment_session_log_service.mark_session_completed(
                context.enrollment_session_log.id
            )


async def _process_message(data: dict, session_id: str, context: SessionContext):
    """Process incoming message using cached context."""
    manager = get_manager()
    message_type = data.get("type")

    if message_type == MessageType.USER_MESSAGE:
        client_msg = UserMessage(**data)
        await process_agent_flow(session_id, context, client_msg.message)
    elif message_type == MessageType.PING:
        await manager.send_message(session_id, PongMessage())
    else:
        raise ValueError(f"Unknown message type: {message_type}")


async def _get_user_from_websocket(websocket: WebSocket, db) -> User:
    """
    Authenticate user from WebSocket connection.
    Supports both Firebase ID tokens and session cookies.
    """
    token = (
        websocket.query_params.get("token")
        or websocket.cookies.get("session")
        or (websocket.headers.get("authorization") or "").replace("Bearer ", "")
    )

    if not token:
        raise ValueError("Missing authentication token")

    user_service = UserService(db)
    decoded_claims = None

    # Try to verify as session cookie first (for backward compatibility)
    try:
        decoded_claims = auth.verify_session_cookie(token, check_revoked=True)
    except Exception as session_error:
        # If it fails with issuer error, it might be an ID token
        error_str = str(session_error).lower()
        is_issuer_error = (
            "iss" in error_str
            and "issuer" in error_str
            and (
                "securetoken.google.com" in error_str or "session.firebase.google.com" in error_str
            )
        )

        if is_issuer_error:
            # Try verifying as ID token
            try:
                decoded_claims = auth.verify_id_token(token, check_revoked=True)
            except Exception as id_token_error:
                raise ValueError(
                    f"Invalid authentication token (tried both session cookie and ID token): {str(id_token_error)}"
                ) from id_token_error
        else:
            raise ValueError(
                f"Invalid authentication token: {str(session_error)}"
            ) from session_error

    # Get user by email from decoded claims
    email = decoded_claims.get("email")
    if not email:
        raise ValueError("Token does not contain email claim")

    return user_service.get_user_by_email(email)


async def _handle_websocket_error(websocket: WebSocket, session_id: str | None, error: Exception):
    """Handle WebSocket errors by sending error message to client and disconnecting."""
    manager = get_manager()
    sanitized = _sanitize_error_message(str(error))
    logger.error(f"[_handle_websocket_error] WebSocket error: {sanitized}", exc_info=True)

    try:
        if session_id:
            await manager.send_message(session_id, ErrorMessage(message=sanitized))
        elif websocket.client_state.name == "CONNECTED":
            await websocket.send_json(ErrorMessage(message=sanitized).model_dump(mode="json"))
    except Exception:
        pass

    if session_id:
        manager.disconnect(session_id)

    try:
        safe_reason = sanitized[:123] if len(sanitized) <= 123 else "Internal server error"
        if websocket.client_state.name == "CONNECTED":
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason=safe_reason)
    except Exception:
        pass


@router.websocket("/ws")
async def mission_ally_websocket(websocket: WebSocket, mission_id: str):
    """WebSocket endpoint for Mission Ally agent interaction."""
    session_id = None
    manager = get_manager()
    context: SessionContext | None = None

    try:
        await websocket.accept()
        db = websocket.app.state.db

        # Authenticate user
        try:
            user = await _get_user_from_websocket(websocket, db)
        except Exception as e:
            sanitized = _sanitize_error_message(str(e))
            if "database" in sanitized.lower():
                sanitized = f"Authentication failed: {sanitized}"
            await _close_websocket_with_error(
                websocket, None, ValueError(sanitized), status.WS_1008_POLICY_VIOLATION
            )
            return

        # Initialize SessionContext (fetches and caches all required data)
        try:
            context = SessionContext(db, user.id, mission_id, manager.session_service)
            initial_state, was_started = await context.initialize()
            session_id = context.enrollment_session_log.id
        except ValueError as e:
            await _close_websocket_with_error(websocket, None, e, status.WS_1008_POLICY_VIOLATION)
            return
        except Exception as e:
            sanitized = _sanitize_error_message(str(e))
            await _close_websocket_with_error(
                websocket, None, ValueError(sanitized), status.WS_1011_INTERNAL_ERROR
            )
            return

        # Get or create ADK session (single place, using cached context)
        try:
            await context.get_or_create_adk_session(session_id, initial_state)
        except ValueError as e:
            await _close_websocket_with_error(websocket, None, e, status.WS_1011_INTERNAL_ERROR)
            return
        except Exception as e:
            sanitized = _sanitize_error_message(str(e))
            error_message = f"Session initialization failed: {sanitized}"
            await _close_websocket_with_error(
                websocket, None, ValueError(error_message), status.WS_1011_INTERNAL_ERROR
            )
            return

        # Register WebSocket connection
        manager.active_connections[session_id] = websocket

        # Send initial connection message
        try:
            await manager.send_message(
                session_id,
                ConnectedMessage(message="Connected to Lumina. Ready to start learning!"),
            )
        except Exception:
            pass  # Non-critical

        # Send historical messages if they exist
        try:
            historical_messages = await _get_historical_messages(session_id, context)
            await manager.send_message(session_id, historical_messages)
        except Exception as e:
            logger.error(
                f"[_handle_websocket_error] Failed to get/send historical messages: {e}",
                exc_info=True,
            )

        # Message processing loop
        while True:
            # Check if websocket is still connected before receiving
            if websocket.client_state.name != "CONNECTED":
                manager.disconnect(session_id)
                break

            try:
                data = await websocket.receive_json()
                await _process_message(data, session_id, context)
            except RuntimeError as e:
                # Handle websocket connection errors
                if "not connected" in str(e).lower() or "accept" in str(e).lower():
                    manager.disconnect(session_id)
                    break
                raise
            except (ValueError, TypeError) as e:
                if websocket.client_state.name == "CONNECTED":
                    try:
                        await manager.send_message(
                            session_id, ErrorMessage(message=f"Invalid message format: {str(e)}")
                        )
                    except Exception:
                        pass
            except WebSocketDisconnect:
                manager.disconnect(session_id)
                break
            except json.JSONDecodeError:
                if websocket.client_state.name == "CONNECTED":
                    try:
                        await manager.send_message(
                            session_id, ErrorMessage(message="Invalid JSON format")
                        )
                    except Exception:
                        pass
            except Exception as e:
                sanitized = _sanitize_error_message(str(e))
                logger.error(
                    f"[_handle_websocket_error] Message processing error: {sanitized}",
                    exc_info=True,
                )
                if websocket.client_state.name == "CONNECTED":
                    try:
                        await manager.send_message(
                            session_id, ErrorMessage(message=f"Processing error: {sanitized}")
                        )
                    except Exception:
                        manager.disconnect(session_id)
                        break
                else:
                    manager.disconnect(session_id)
                    break
    except ValueError as e:
        sanitized = _sanitize_error_message(str(e))
        await _close_websocket_with_error(
            websocket, session_id, ValueError(sanitized), status.WS_1008_POLICY_VIOLATION
        )
    except Exception as e:
        await _handle_websocket_error(websocket, session_id, e)
