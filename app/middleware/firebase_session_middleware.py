"""Firebase Session Cookie Middleware - Alternative to ID token verification"""

from datetime import timedelta
import re

from fastapi import Request
from firebase_admin import auth
from firebase_admin.auth import (
    ExpiredIdTokenError,
    ExpiredSessionCookieError,
    InvalidIdTokenError,
    InvalidSessionCookieError,
    RevokedIdTokenError,
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

        # Try to get token from cookie or Authorization header
        token = request.cookies.get(self.COOKIE_NAME)
        if not token:
            # Check Authorization header
            auth_header = request.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                token = auth_header.replace("Bearer ", "")

        if not token:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Missing authentication token. Provide either a session cookie or Authorization header with Bearer token",
                    "error_code": "AUTH_MISSING",
                },
            )

        try:
            decoded_claims = auth.verify_session_cookie(token, check_revoked=True)
        except (
            ExpiredSessionCookieError,
            RevokedSessionCookieError,
            InvalidSessionCookieError,
        ) as session_error:
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
                except ExpiredIdTokenError:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "ID token expired", "error_code": "TOKEN_EXPIRED"},
                    )
                except RevokedIdTokenError:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "ID token revoked", "error_code": "TOKEN_REVOKED"},
                    )
                except InvalidIdTokenError:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid ID token", "error_code": "TOKEN_INVALID"},
                    )
                except Exception as id_token_error:
                    return JSONResponse(
                        status_code=401,
                        content={
                            "detail": f"Invalid authentication token: {str(id_token_error)}",
                            "error_code": "TOKEN_INVALID",
                        },
                    )
            else:
                # Re-raise session cookie errors
                if isinstance(session_error, ExpiredSessionCookieError):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Session expired", "error_code": "SESSION_EXPIRED"},
                    )
                elif isinstance(session_error, RevokedSessionCookieError):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Session revoked", "error_code": "SESSION_REVOKED"},
                    )
                elif isinstance(session_error, InvalidSessionCookieError):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid session", "error_code": "SESSION_INVALID"},
                    )
                else:
                    return JSONResponse(
                        status_code=401,
                        content={
                            "detail": f"Invalid authentication token: {str(session_error)}",
                            "error_code": "AUTH_INVALID",
                        },
                    )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={
                    "detail": f"Internal server error: {str(e)}",
                    "error_code": "INTERNAL_ERROR",
                },
            )

        # Create user from decoded claims
        user_create_object = UserCreate(
            firebase_uid=decoded_claims["uid"],
            email=decoded_claims.get("email"),
            name=decoded_claims.get("name"),
            picture=decoded_claims.get("picture"),
        )

        user_service = UserService(request.app.state.db)
        user: User = user_service.get_or_create_user(user_create_object)

        request.state.current_user = user

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
