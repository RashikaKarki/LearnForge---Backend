from fastapi import Request
# Ensure firebase is initialized (side-effect import)
from firebase_admin import auth
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

EXCLUDED_PATHS = {"/auth/verify_profile", "/docs", "/openapi.json"}


class FirebaseAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip excluded routes
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header.split("Bearer ")[1]
        try:
            decoded_token = auth.verify_id_token(token)
            request.state.user = decoded_token
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"detail": f"Invalid or expired token: {str(e)}"},
            )

        return await call_next(request)
