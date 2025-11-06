"""Firebase Session Cookie Middleware - Alternative to ID token verification"""

from datetime import timedelta
import logging
import re

from fastapi import Request
from firebase_admin import auth
from firebase_admin.auth import (
    ExpiredSessionCookieError,
    InvalidSessionCookieError,
    RevokedSessionCookieError,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.models.user import User, UserCreate
from app.services.user_service import UserService


logger = logging.getLogger(__name__)


EXCLUDED_PATHS = {
    r"^/api/v1/auth/create-session$",
    r"^/api/v1/auth/session-status$",
    r"^/api/health$",
    r"^/docs$",
    r"^/openapi\.json$",
    r"^/redoc$",
}


class FirebaseSessionMiddleware(BaseHTTPMiddleware):
    COOKIE_NAME = "session"
    SESSION_DURATION = timedelta(days=2)

    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or any(
            re.match(pattern, request.url.path) for pattern in EXCLUDED_PATHS
        ):
            return await call_next(request)

        session_cookie = request.cookies.get(self.COOKIE_NAME)
        if not session_cookie:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Missing session cookie",
                    "error_code": "SESSION_MISSING",
                },
            )

        try:
            # Verify the session cookie. In this case, additional check for revocation is done.
            decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
            logger.debug(f"Session cookie verified for uid: {decoded_claims.get('uid')}")

            # Extract user information from claims
            firebase_uid = decoded_claims.get("uid")
            email = decoded_claims.get("email")
            name = decoded_claims.get("name") or decoded_claims.get("display_name") or "User"
            picture = decoded_claims.get("picture")

            # Validate required fields
            if not firebase_uid:
                logger.error("Firebase UID missing from decoded claims")
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Invalid authentication token: missing user ID",
                        "error_code": "MISSING_UID",
                    },
                )

            if not email:
                logger.error(f"Email missing from Firebase claims for uid: {firebase_uid}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": "Invalid authentication token: email required",
                        "error_code": "MISSING_EMAIL",
                    },
                )

            logger.info(
                f"Creating/getting user: email={email}, firebase_uid={firebase_uid}, name={name}"
            )

            try:
                user_create_object = UserCreate(
                    firebase_uid=firebase_uid,
                    email=email,
                    name=name,
                    picture=picture,
                )
            except Exception as e:
                logger.error(f"Failed to create UserCreate object: {e}, claims: {decoded_claims}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": f"Invalid user data: {str(e)}",
                        "error_code": "INVALID_USER_DATA",
                    },
                )

            user_service = UserService(request.app.state.db)
            try:
                user: User = user_service.get_or_create_user(user_create_object)
                logger.info(
                    f"User retrieved/created successfully: id={user.id}, email={user.email}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to get or create user: {e}, email={email}, firebase_uid={firebase_uid}"
                )
                return JSONResponse(
                    status_code=500,
                    content={
                        "detail": f"Failed to retrieve or create user: {str(e)}",
                        "error_code": "USER_CREATION_FAILED",
                    },
                )

            request.state.current_user = user

        except ExpiredSessionCookieError:
            logger.warning("Session cookie expired")
            return JSONResponse(
                status_code=401,
                content={"detail": "Session expired", "error_code": "SESSION_EXPIRED"},
            )
        except RevokedSessionCookieError:
            logger.warning("Session cookie revoked")
            return JSONResponse(
                status_code=401,
                content={"detail": "Session revoked", "error_code": "SESSION_REVOKED"},
            )
        except InvalidSessionCookieError:
            logger.warning("Invalid session cookie")
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid session", "error_code": "SESSION_INVALID"},
            )
        except Exception as e:
            logger.exception(f"Unexpected error in Firebase session middleware: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "detail": f"Internal server error: {str(e)}",
                    "error_code": "INTERNAL_ERROR",
                },
            )

        return await call_next(request)

    @staticmethod
    def create_session_cookie(id_token: str) -> str:
        """
        Create a session cookie from an ID token.
        Call this from your auth endpoint.

        Example:
            cookie = FirebaseSessionMiddleware.create_session_cookie(id_token)
            response.set_cookie(
                key="session",
                value=cookie,
                httponly=True,
                secure=True,  # HTTPS only
                samesite="lax",
                max_age=60 * 60 * 24 * 5  # 5 days
            )
        """
        return auth.create_session_cookie(
            id_token, expires_in=FirebaseSessionMiddleware.SESSION_DURATION
        )
