"""WebSocket endpoint for Mission Ally agent interaction"""

import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from firebase_admin import auth

from app.models.websocket_messages import (
    AgentMessage,
    ConnectedMessage,
    ErrorMessage,
    HistoricalMessagesMessage,
    MessageType,
    PongMessage,
    SessionClosedMessage,
    UserMessage,
)
from app.services.user_service import UserService

from .mission_ally_helpers.agent_processor import AgentProcessor
from .mission_ally_helpers.connection_manager import ConnectionManager, get_manager
from .mission_ally_helpers.session_context import SessionContext
from .mission_ally_helpers.utils import sanitize_error_message


logger = logging.getLogger(__name__)
router = APIRouter()


class WebSocketHandler:
    def __init__(self, websocket: WebSocket, mission_id: str, manager: ConnectionManager):
        self.websocket = websocket
        self.mission_id = mission_id
        self.manager = manager
        self.session_id: str | None = None
        self.context: SessionContext | None = None

    async def authenticate(self, db) -> str:
        """Authenticate user and return user ID"""
        token = (
            self.websocket.query_params.get("token")
            or self.websocket.cookies.get("session")
            or (self.websocket.headers.get("authorization") or "").replace("Bearer ", "")
        )

        if not token:
            raise ValueError("Missing authentication token")

        user_service = UserService(db)
        decoded_claims = None

        try:
            decoded_claims = auth.verify_session_cookie(token, check_revoked=True)
        except Exception as session_error:
            error_str = str(session_error).lower()
            is_issuer_error = (
                "iss" in error_str
                and "issuer" in error_str
                and (
                    "securetoken.google.com" in error_str
                    or "session.firebase.google.com" in error_str
                )
            )

            if is_issuer_error:
                try:
                    decoded_claims = auth.verify_id_token(token, check_revoked=True)
                except Exception as id_token_error:
                    raise ValueError(
                        f"Invalid authentication token: {str(id_token_error)}"
                    ) from id_token_error
            else:
                raise ValueError(
                    f"Invalid authentication token: {str(session_error)}"
                ) from session_error

        email = decoded_claims.get("email")
        if not email:
            raise ValueError("Token does not contain email claim")

        user = user_service.get_user_by_email(email)
        return user.id

    async def initialize_session(self, db, user_id: str):
        """Initialize session context and ADK session"""
        self.context = SessionContext(db, user_id, self.mission_id, self.manager.session_service)
        initial_state, was_started, is_completed = await self.context.initialize()
        self.session_id = self.context.enrollment_session_log.id

        await self.context.get_or_create_adk_session(self.session_id, initial_state)
        self.manager.active_connections[self.session_id] = self.websocket

        return is_completed

    async def send_initial_messages(self):
        """Send connection confirmation and historical messages"""
        await self.manager.send_message(
            self.session_id,
            ConnectedMessage(message="Connected to Lumina. Ready to start learning!"),
        )

        try:
            historical_messages = await self._get_historical_messages()
            await self.manager.send_message(self.session_id, historical_messages)
        except Exception as e:
            logger.error(f"Failed to get/send historical messages: {e}", exc_info=True)

    async def handle_completed_mission(self):
        """Handle case where mission is already completed"""
        await self.send_initial_messages()
        await self.manager.send_message(
            self.session_id,
            SessionClosedMessage(message="Congratulations! You've completed the mission!"),
        )
        await asyncio.sleep(0.1)
        await self._close_connection()

    async def process_messages(self):
        """Main message processing loop"""
        processor = AgentProcessor(self.manager, self.context)

        while True:
            if self.websocket.client_state.name != "CONNECTED":
                self.manager.disconnect(self.session_id)
                break

            try:
                data = await self.websocket.receive_json()
                await self._handle_message(data, processor)
            except RuntimeError as e:
                if "not connected" in str(e).lower() or "accept" in str(e).lower():
                    self.manager.disconnect(self.session_id)
                    break
                raise
            except (ValueError, TypeError) as e:
                await self._send_error(f"Invalid message format: {str(e)}")
            except WebSocketDisconnect:
                self.manager.disconnect(self.session_id)
                break
            except json.JSONDecodeError:
                await self._send_error("Invalid JSON format")
            except Exception as e:
                sanitized = sanitize_error_message(str(e))
                logger.error(f"Message processing error: {sanitized}", exc_info=True)
                if not await self._send_error(f"Processing error: {sanitized}"):
                    break

    async def _handle_message(self, data: dict, processor: AgentProcessor):
        """Handle individual message based on type"""
        message_type = data.get("type")

        if message_type == MessageType.USER_MESSAGE:
            client_msg = UserMessage(**data)
            await processor.process_user_message(self.session_id, client_msg.message)
        elif message_type == MessageType.PING:
            await self.manager.send_message(self.session_id, PongMessage())
        else:
            raise ValueError(f"Unknown message type: {message_type}")

    async def _get_historical_messages(self) -> HistoricalMessagesMessage:
        """Retrieve historical messages from cached session"""
        try:
            session = self.context.adk_session
            if not session or not hasattr(session, "events") or session.events is None:
                return HistoricalMessagesMessage(messages=[])

            messages = []
            for event in session.events:
                if not event or not hasattr(event, "author") or not hasattr(event, "content"):
                    continue
                if not event.content or not hasattr(event.content, "parts"):
                    continue
                if not event.content.parts:
                    continue

                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        if event.author == "user":
                            messages.append(UserMessage(message=part.text).model_dump(mode="json"))
                        else:
                            messages.append(AgentMessage(message=part.text).model_dump(mode="json"))

            return HistoricalMessagesMessage(messages=messages)
        except Exception as e:
            logger.error(f"Failed to retrieve historical messages: {e}", exc_info=True)
            return HistoricalMessagesMessage(messages=[])

    async def _send_error(self, message: str) -> bool:
        """Send error message, return False if connection should close"""
        if self.websocket.client_state.name == "CONNECTED":
            try:
                await self.manager.send_message(self.session_id, ErrorMessage(message=message))
                return True
            except Exception:
                self.manager.disconnect(self.session_id)
                return False
        else:
            self.manager.disconnect(self.session_id)
            return False

    async def _close_connection(self):
        """Close websocket connection"""
        if self.websocket.client_state.name == "CONNECTED":
            try:
                await self.websocket.close()
            except Exception:
                pass
        self.manager.disconnect(self.session_id)

    async def close_with_error(
        self, error: Exception, close_code: int = status.WS_1011_INTERNAL_ERROR
    ):
        """Close connection with error message"""
        sanitized = sanitize_error_message(str(error))
        logger.error(f"WebSocket error: {sanitized}", exc_info=True)

        try:
            if self.websocket.client_state.name == "CONNECTED":
                await self.websocket.send_json(
                    ErrorMessage(message=sanitized).model_dump(mode="json")
                )
        except Exception:
            pass

        try:
            safe_reason = sanitized[:123] if len(sanitized) <= 123 else "Internal server error"
            if self.websocket.client_state.name == "CONNECTED":
                await self.websocket.close(code=close_code, reason=safe_reason)
        except Exception:
            pass


@router.websocket("/ws")
async def mission_ally_websocket(websocket: WebSocket, mission_id: str):
    """WebSocket endpoint for Mission Ally agent interaction"""
    await websocket.accept()
    manager = get_manager()
    handler = WebSocketHandler(websocket, mission_id, manager)

    try:
        db = websocket.app.state.db

        user_id = await handler.authenticate(db)
        is_completed = await handler.initialize_session(db, user_id)

        if is_completed:
            await handler.handle_completed_mission()
            return

        await handler.send_initial_messages()
        await handler.process_messages()

    except ValueError as e:
        sanitized = sanitize_error_message(str(e))
        await handler.close_with_error(ValueError(sanitized), status.WS_1008_POLICY_VIOLATION)
    except Exception as e:
        await handler.close_with_error(e)
