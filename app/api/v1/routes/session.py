"""Session management endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.initializers.firestore import get_db
from app.models.session_log import SessionLogCreate, SessionResponse
from app.models.user import User
from app.services.session_log_service import SessionLogService


router = APIRouter()


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Create a new WebSocket session for the authenticated user.
    """
    session_service = SessionLogService(db)

    # Create session for authenticated user
    session_data = SessionLogCreate(user_id=current_user.id)
    session = session_service.create_session(session_data)

    # Return formatted response
    return SessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        status=session.status,
        created_at=session.created_at,
    )


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Get details of a specific session.

    Args:
        session_id: The unique session identifier

    Returns:
        SessionResponse: Session details

    Raises:
        404: If session not found
        403: If session doesn't belong to the current user
    """
    session_service = SessionLogService(db)
    session = session_service.get_session(session_id)

    # Verify session belongs to current user
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to access this session.",
        )

    return SessionResponse(
        session_id=session.id,
        user_id=session.user_id,
        status=session.status,
        created_at=session.created_at,
    )
