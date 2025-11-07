"""Connection manager for WebSocket connections"""

import logging

from fastapi import WebSocket
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService


try:
    from google.cloud.sql.connector import Connector
except ImportError:
    Connector = None

from app.agents.mission_ally.agent import root_agent
from app.core.config import settings
from app.models.websocket_messages import MissionAllyServerMessage as ServerMessage

from .utils import sanitize_error_message


logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self._session_service = None
        self._runner = None
        self._connector = None

    @property
    def session_service(self):
        if self._session_service is None:
            self._session_service = self._create_session_service()
        return self._session_service

    @property
    def runner(self):
        if self._runner is None:
            self._runner = Runner(
                agent=root_agent, app_name="mission-ally", session_service=self.session_service
            )
        return self._runner

    def _create_session_service(self):
        """Create and configure DatabaseSessionService"""
        try:
            if settings.use_cloud_sql_connector:
                logger.info("Initializing DatabaseSessionService with Cloud SQL Connector")
                return self._create_cloud_sql_session_service()
            else:
                logger.info("Initializing DatabaseSessionService with DATABASE_URL")
                return self._create_standard_session_service()
        except ValueError:
            raise
        except Exception as e:
            sanitized = sanitize_error_message(str(e))
            logger.error(f"Failed to initialize DatabaseSessionService: {sanitized}", exc_info=True)
            raise ValueError(sanitized) from None

    def _create_cloud_sql_session_service(self):
        """Create session service with Cloud SQL Connector"""
        if Connector is None:
            raise ImportError(
                "cloud-sql-python-connector package is not installed. "
                "Install it with: pip install 'cloud-sql-python-connector[pg8000]'"
            )

        if self._connector is None:
            self._connector = Connector(refresh_strategy="LAZY")

        db_url = "postgresql+pg8000://"
        return DatabaseSessionService(
            db_url=db_url,
            creator=self._create_cloud_sql_connection,
            pool_size=10,
            max_overflow=5,
            pool_timeout=60,
            pool_recycle=1800,
        )

    def _create_standard_session_service(self):
        """Create session service with standard DATABASE_URL"""
        db_url = settings.DATABASE_URL
        if not db_url:
            raise ValueError("DATABASE_URL is not configured")
        if not (db_url.startswith("postgresql://") or db_url.startswith("postgres://")):
            raise ValueError("Invalid database URL format")

        return DatabaseSessionService(db_url=db_url.strip())

    def _create_cloud_sql_connection(self):
        """Create Cloud SQL connection using connector"""
        return self._connector.connect(
            settings.INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            db=settings.DB_NAME,
        )

    def disconnect(self, session_id: str):
        """Remove connection from active connections"""
        self.active_connections.pop(session_id, None)

    async def send_message(self, session_id: str, message: ServerMessage):
        """Send message to connected client"""
        websocket = self.active_connections.get(session_id)
        if websocket and websocket.client_state.name == "CONNECTED":
            try:
                await websocket.send_json(message.model_dump(mode="json"))
            except Exception:
                self.disconnect(session_id)

    def cleanup(self):
        """Cleanup resources on shutdown"""
        if self._connector is not None:
            try:
                self._connector.close()
            except Exception as e:
                logger.error(f"Error closing Cloud SQL connector: {e}")


_manager_instance = None


def get_manager() -> ConnectionManager:
    """Get or create the ConnectionManager instance (lazy initialization)"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = ConnectionManager()
    return _manager_instance
