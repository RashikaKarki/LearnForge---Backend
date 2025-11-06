"""Firebase Session Cookie Middleware - Alternative to ID token verification"""

import re
from datetime import timedelta

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

            user_create_object = UserCreate(
                firebase_uid=decoded_claims["uid"],
                email=decoded_claims.get("email"),
                name=decoded_claims.get("name"),
                picture=decoded_claims.get("picture"),
            )

            user_service = UserService(request.app.state.db)
            user: User = user_service.get_or_create_user(user_create_object)

            request.state.current_user = user

        except ExpiredSessionCookieError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Session expired", "error_code": "SESSION_EXPIRED"},
            )
        except RevokedSessionCookieError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Session revoked", "error_code": "SESSION_REVOKED"},
            )
        except InvalidSessionCookieError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid session", "error_code": "SESSION_INVALID"},
            )
        except Exception as e:
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
