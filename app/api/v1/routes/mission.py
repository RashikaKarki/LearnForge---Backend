"""Mission endpoints for retrieving and updating missions."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies.auth import get_current_user
from app.initializers.firestore import get_db
from app.models.mission import Mission, MissionCreate, MissionUpdate
from app.models.user import User
from app.services.mission_service import MissionService

router = APIRouter()


@router.post("/enrollment", status_code=status.HTTP_201_CREATED)
async def create_mission_with_enrollment(
    mission_data: MissionCreate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new mission and automatically enroll the creator.

    Args:
        mission_data: Mission creation data
        current_user: Authenticated user (auto-enrolled as creator)

    Returns:
        Dictionary with mission and enrollment objects

    Raises:
        500: If mission or enrollment creation fails
    """
    mission_service = MissionService(db)

    # Override creator_id with authenticated user's ID
    mission_data.creator_id = current_user.id

    mission, enrollment, enrollment_session_log = mission_service.create_mission_with_enrollment(
        mission_data, current_user.id
    )

    return {
        "mission": mission,
        "enrollment": enrollment,
        "enrollment_session_log": enrollment_session_log,
    }


@router.get("/{mission_id}", response_model=Mission)
async def get_mission(
    mission_id: str,
    db=Depends(get_db),
):
    """
    Get a mission by ID.

    Args:
        mission_id: The ID of the mission to retrieve

    Returns:
        Mission object with all details

    Raises:
        404: Mission not found
    """
    mission_service = MissionService(db)
    return mission_service.get_mission(mission_id)


@router.patch("/{mission_id}", response_model=Mission)
async def update_mission(
    mission_id: str,
    mission_update: MissionUpdate,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a mission. Only the creator can update their mission.

    Args:
        mission_id: The ID of the mission to update
        mission_update: Fields to update
        current_user: Authenticated user (must be mission creator)

    Returns:
        Updated Mission object

    Raises:
        404: Mission not found
        403: User is not the creator of this mission
    """
    mission_service = MissionService(db)

    # Get the mission to check ownership
    mission = mission_service.get_mission(mission_id)

    # Verify the user is the creator
    if mission.creator_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the mission creator can update this mission",
        )

    # Update the mission
    return mission_service.update_mission(mission_id, mission_update)
