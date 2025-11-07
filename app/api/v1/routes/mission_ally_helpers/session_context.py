"""Session context management for WebSocket connections"""

import logging

from app.models.enrollment import Enrollment
from app.models.enrollment_session_log import EnrollmentSessionLog
from app.models.mission import Mission
from app.models.user import User, UserEnrolledMission
from app.services.enrollment_service import EnrollmentService
from app.services.enrollment_session_log_service import EnrollmentSessionLogService
from app.services.mission_service import MissionService
from app.services.user_service import UserService


logger = logging.getLogger(__name__)


class SessionContext:
    """Caches database-fetched data and ADK session during WebSocket lifecycle"""

    def __init__(self, db, user_id: str, mission_id: str, session_service):
        self.db = db
        self.user_id = user_id
        self.mission_id = mission_id
        self.session_service = session_service

        self.user_service = UserService(db)
        self.mission_service = MissionService(db)
        self.enrollment_service = EnrollmentService(db)
        self.enrollment_session_log_service = EnrollmentSessionLogService(db)

        self._user: User | None = None
        self._mission: Mission | None = None
        self._enrollment: Enrollment | None = None
        self._enrolled_mission: UserEnrolledMission | None = None
        self._enrollment_session_log: EnrollmentSessionLog | None = None
        self._adk_session = None
        self._initialized = False

    async def initialize(self) -> tuple[dict, bool, bool]:
        """
        Fetch and cache all required data.
        Returns (initial_state_dict, was_started, is_completed)
        """
        if self._initialized:
            raise ValueError("SessionContext already initialized")

        await self._fetch_user()
        await self._fetch_mission()
        await self._fetch_enrollment()
        await self._fetch_enrolled_mission()
        await self._fetch_enrollment_session_log()

        is_completed = self._enrollment_session_log.status == "completed"
        was_started = False

        if not is_completed:
            was_started = self._enrollment_session_log.status == "started"
            if self._enrollment_session_log.status == "created":
                self.enrollment_session_log_service.mark_session_started(
                    self._enrollment_session_log.id
                )

        initial_state = self._build_initial_state()
        self._initialized = True
        return initial_state, was_started, is_completed

    async def get_or_create_adk_session(self, session_id: str, initial_state: dict):
        """Get existing ADK session or create new one"""
        if self._adk_session is not None:
            return self._adk_session

        try:
            self._adk_session = await self.session_service.get_session(
                app_name="mission-ally",
                user_id=self.user_id,
                session_id=session_id,
            )
            if self._adk_session is None:
                raise ValueError(f"Session {session_id} not found")
            logger.info(f"Retrieved existing ADK session: {session_id}")
        except Exception as get_error:
            logger.info(f"Creating new ADK session: {session_id}")
            try:
                await self.session_service.create_session(
                    app_name="mission-ally",
                    user_id=self.user_id,
                    session_id=session_id,
                    state=initial_state,
                )
                self._adk_session = await self.session_service.get_session(
                    app_name="mission-ally",
                    user_id=self.user_id,
                    session_id=session_id,
                )
            except Exception as create_error:
                from .utils import sanitize_error_message

                sanitized = sanitize_error_message(str(create_error))
                error_message = (
                    f"Failed to create session: {session_id}. "
                    f"Get error: {str(get_error)}. Create error: {sanitized}"
                )
                logger.error(f"ADK session creation failed: {error_message}", exc_info=True)
                raise ValueError(error_message) from create_error

        return self._adk_session

    async def refresh_adk_session(self, session_id: str):
        """Refresh cached ADK session with latest data"""
        try:
            self._adk_session = await self.session_service.get_session(
                app_name="mission-ally",
                user_id=self.user_id,
                session_id=session_id,
            )
            return self._adk_session
        except Exception as e:
            logger.error(f"Failed to refresh ADK session: {e}", exc_info=True)
            raise

    async def _fetch_user(self):
        """Fetch and cache user"""
        try:
            self._user = self.user_service.get_user(self.user_id)
        except Exception as e:
            logger.error(f"Failed to retrieve user {self.user_id}: {e}", exc_info=True)
            raise ValueError(f"User not found: {self.user_id}") from e

    async def _fetch_mission(self):
        """Fetch and cache mission"""
        from fastapi import HTTPException

        try:
            self._mission = self.mission_service.get_mission(self.mission_id)
        except HTTPException as e:
            if e.status_code == 404:
                raise ValueError(f"Mission not found: {self.mission_id}") from e
            raise ValueError(f"Failed to retrieve mission: {str(e)}") from e
        except Exception as e:
            logger.error(f"Failed to retrieve mission: {e}", exc_info=True)
            raise ValueError(f"Failed to retrieve mission: {str(e)}") from e

    async def _fetch_enrollment(self):
        """Fetch and cache enrollment"""
        from fastapi import HTTPException

        try:
            self._enrollment = self.enrollment_service.get_enrollment(self.user_id, self.mission_id)
        except HTTPException as e:
            if e.status_code == 404:
                raise ValueError(f"Enrollment not found for user {self.user_id}") from e
            raise ValueError(f"Failed to retrieve enrollment: {str(e)}") from e
        except Exception as e:
            logger.error(f"Failed to retrieve enrollment: {e}", exc_info=True)
            raise ValueError(f"Failed to retrieve enrollment: {str(e)}") from e

    async def _fetch_enrolled_mission(self):
        """Fetch and cache enrolled mission"""
        try:
            self._enrolled_mission = self.user_service.get_enrolled_mission(
                self.user_id, self.mission_id
            )
        except Exception as e:
            logger.error(f"Failed to retrieve enrolled mission: {e}", exc_info=True)
            raise ValueError(f"Failed to retrieve enrolled mission: {str(e)}") from e

    async def _fetch_enrollment_session_log(self):
        """Fetch and cache enrollment session log"""
        try:
            self._enrollment_session_log = self.enrollment_session_log_service.get_session_log_by_user_and_enrollment_and_mission(
                user_id=self.user_id,
                enrollment_id=self._enrollment.id,
                mission_id=self.mission_id,
            )
            if not self._enrollment_session_log:
                raise ValueError(f"Enrollment session log not found for user {self.user_id}")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"Failed to retrieve enrollment session log: {str(e)}") from e

    def _build_initial_state(self) -> dict:
        """Build initial state dictionary for ADK session"""
        starting_index = self._find_starting_checkpoint_index()
        return {
            "mission_id": self.mission_id,
            "user_profile": self._user.model_dump(mode="json", exclude_none=True),
            "enrolled_mission": self._enrolled_mission.model_dump(mode="json", exclude_none=True),
            "mission_details": self._mission.model_dump(mode="json", exclude_none=True),
            "enrollment_session_log_id": self._enrollment_session_log.id,
            "current_checkpoint_index": starting_index,
            "current_checkpoint_goal": (
                "Ended"
                if starting_index == -1
                else self._enrolled_mission.byte_size_checkpoints[starting_index]
            ),
            "completed_checkpoints": self._enrolled_mission.completed_checkpoints or [],
            "content_search_result": "",
            "video_selection_result": {},
        }

    def _find_starting_checkpoint_index(self) -> int:
        """Find the index of the first incomplete checkpoint"""
        all_checkpoints = self._enrolled_mission.byte_size_checkpoints
        completed = self._enrolled_mission.completed_checkpoints or []

        for idx, checkpoint in enumerate(all_checkpoints):
            if checkpoint not in completed:
                return idx
        return -1

    @property
    def adk_session(self):
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._adk_session

    @property
    def user(self) -> User:
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._user

    @property
    def mission(self) -> Mission:
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._mission

    @property
    def enrollment(self) -> Enrollment:
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._enrollment

    @property
    def enrolled_mission(self) -> UserEnrolledMission:
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._enrolled_mission

    @property
    def enrollment_session_log(self) -> EnrollmentSessionLog:
        if not self._initialized:
            raise ValueError("SessionContext not initialized")
        return self._enrollment_session_log
