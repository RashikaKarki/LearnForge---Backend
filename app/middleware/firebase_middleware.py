from fastapi import Request
from firebase_admin import auth
from firebase_admin.auth import (
    ExpiredIdTokenError,
    InvalidIdTokenError,
    RevokedIdTokenError,
)
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.models.user import User
from app.services.user_service import UserService

EXCLUDED_PATHS = {"/auth/verify_profile", "/docs", "/openapi.json"}


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS" or request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Missing Authorization header",
                    "error_code": "TOKEN_MISSING",
                },
            )

        try:
            scheme, token = auth_header.split(" ")
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": "Invalid auth scheme",
                        "error_code": "INVALID_SCHEME",
                    },
                )
        except ValueError:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": "Malformed Authorization header",
                    "error_code": "MALFORMED_HEADER",
                },
            )

        try:
            decoded_token = auth.verify_id_token(token)
            user_object = {
                "firebase_uid": decoded_token["uid"],
                "email": decoded_token.get("email"),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
            }

            user_service = UserService(request.app.state.db)
            user: User = user_service.get_or_create_user(user_object)

            request.state.current_user = user
        except ExpiredIdTokenError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token expired", "error_code": "TOKEN_EXPIRED"},
            )
        except RevokedIdTokenError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Token revoked", "error_code": "TOKEN_REVOKED"},
            )
        except InvalidIdTokenError:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid token", "error_code": "TOKEN_INVALID"},
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
