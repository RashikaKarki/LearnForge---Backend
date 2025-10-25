from datetime import timedelta
from time import time

from fastapi import APIRouter, HTTPException, Request, Response, status
from firebase_admin import auth
from pydantic import BaseModel

router = APIRouter()


class CreateSessionRequest(BaseModel):
    """Request body for creating a session cookie"""

    id_token: str


class SessionResponse(BaseModel):
    """Response for session operations"""

    message: str
    uid: str | None = None


# Session configuration
SESSION_COOKIE_NAME = "session"
SESSION_DURATION_DAYS = 2
SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * SESSION_DURATION_DAYS


@router.post("/create-session", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(request: CreateSessionRequest, response: Response):
    """Exchange Firebase ID token for session cookie"""
    try:
        decoded_token = auth.verify_id_token(request.id_token)

        # Require recent sign-in (within last 5 minutes)
        if decoded_token.get("auth_time", 0) < (time() - 5 * 60):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Recent sign-in required to create session",
            )

        session_cookie = auth.create_session_cookie(
            request.id_token, expires_in=timedelta(days=SESSION_DURATION_DAYS)
        )

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_cookie,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=SESSION_MAX_AGE_SECONDS,
            path="/",
        )

        return SessionResponse(message="Session created successfully", uid=decoded_token["uid"])

    except auth.InvalidIdTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token") from e
    except auth.ExpiredIdTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ID token has expired") from e
    except Exception as e:
        print("I am here")
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}",
        ) from e


@router.post("/logout", response_model=SessionResponse)
async def logout(request: Request, response: Response):
    """Logout and clear session cookie"""
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)

    if session_cookie:
        try:
            decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
            auth.revoke_refresh_tokens(decoded_claims["uid"])
        except Exception:
            pass

    response.delete_cookie(
        key=SESSION_COOKIE_NAME, path="/", httponly=True, secure=True, samesite="lax"
    )

    return SessionResponse(message="Logged out successfully", uid=None)


@router.post("/refresh-session", response_model=SessionResponse)
async def refresh_session(request: Request, response: Response):
    """Refresh session cookie to extend expiration"""
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No session cookie found"
        )

    try:
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)

        new_session_cookie = auth.create_session_cookie(
            session_cookie, expires_in=timedelta(days=SESSION_DURATION_DAYS)
        )

        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=new_session_cookie,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=SESSION_MAX_AGE_SECONDS,
            path="/",
        )

        return SessionResponse(message="Session refreshed successfully", uid=decoded_claims["uid"])

    except auth.ExpiredSessionCookieError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has expired") from e
    except auth.RevokedSessionCookieError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked"
        ) from e
    except auth.InvalidSessionCookieError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session cookie"
        ) from e


@router.get("/session-status", response_model=SessionResponse)
async def get_session_status(request: Request):
    """Check if current session is valid"""
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)

    if not session_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="No session cookie found"
        )

    try:
        decoded_claims = auth.verify_session_cookie(session_cookie, check_revoked=True)
        return SessionResponse(message="Session is valid", uid=decoded_claims["uid"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session"
        ) from e
