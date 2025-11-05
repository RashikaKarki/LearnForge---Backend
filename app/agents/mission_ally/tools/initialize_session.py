from datetime import datetime

from google.adk.tools import FunctionTool, ToolContext

from app.models.mission import Mission
from app.models.user import User, UserEnrolledMission


def initialize_session(tool_context: ToolContext) -> str:
    """
    Tool to initialize the learning session with User and UserEnrolledMission.
    These should be passed in via context from the caller.

    Extracts mission details from UserEnrolledMission and determines the starting checkpoint
    based on completed checkpoints.

    For testing: Creates dummy User and UserEnrolledMission if not provided.
    """
    # Get User and UserEnrolledMission from context, or create dummies for testing
    user_profile = tool_context.state.get("user_profile")
    enrolled_mission = tool_context.state.get("enrolled_mission")

    if not user_profile:
        # Create dummy User for testing
        user_profile = User(
            id="dummy-user-123",
            firebase_uid="dummy-firebase-uid-123",
            name="Alex Johnson",
            email="alex.johnson@example.com",
            picture=None,
            enrolled_missions=[],
            learning_style=["examples", "step-by-step", "visual"],
            created_at=datetime.today(),
            updated_at=datetime.today(),
        )

    if not enrolled_mission:
        # Create dummy UserEnrolledMission for testing
        enrolled_mission = UserEnrolledMission(
            mission_id="dummy-mission-123",
            mission_title="Introduction to Data Science",
            mission_short_description="Learn data science fundamentals through hands-on practice",
            mission_skills=["Python", "Data Analysis", "Visualization"],
            progress=0.0,
            byte_size_checkpoints=[
                "Data Analysis Basics",
                "Data Visualization Techniques",
                "Machine Learning Fundamentals",
                "Final Project: Analyzing Real-World Data",
            ],
            completed_checkpoints=[],
            enrolled_at=datetime.today(),
            last_accessed_at=datetime.today(),
            completed=False,
            updated_at=datetime.today(),
        )

    # Use dictionary-style assignment
    tool_context.state["user_profile"] = user_profile

    # Create Mission from UserEnrolledMission data
    mission = Mission(
        id=enrolled_mission.mission_id,
        title=enrolled_mission.mission_title,
        short_description=enrolled_mission.mission_short_description,
        description=enrolled_mission.mission_short_description,
        creator_id=user_profile.id,
        level="Beginner",
        topics_to_cover=[],
        learning_goal="",
        byte_size_checkpoints=enrolled_mission.byte_size_checkpoints,
        skills=enrolled_mission.mission_skills or [],
        is_public=True,
    )

    tool_context.state["mission_details"] = mission
    tool_context.state["enrolled_mission"] = enrolled_mission

    # Determine starting checkpoint index based on completed checkpoints
    all_checkpoints = enrolled_mission.byte_size_checkpoints
    completed = enrolled_mission.completed_checkpoints or []

    # Find the first incomplete checkpoint
    starting_index = 0
    for idx, checkpoint in enumerate(all_checkpoints):
        if checkpoint not in completed:
            starting_index = idx
            break
    else:
        # All checkpoints completed
        starting_index = len(all_checkpoints)
        tool_context.state["current_checkpoint_index"] = -1
        tool_context.state["current_checkpoint_goal"] = "Ended"
        return f"Session initialized for {user_profile.name}. All checkpoints completed for mission: {mission.title}"

    # Initialize checkpoint tracking
    tool_context.state["current_checkpoint_index"] = starting_index
    tool_context.state["current_checkpoint_goal"] = all_checkpoints[starting_index]
    tool_context.state["completed_checkpoints"] = completed

    return f"Session initialized for {user_profile.name} with mission: {mission.title}. Starting at checkpoint {starting_index + 1}/{len(all_checkpoints)}: {all_checkpoints[starting_index]}"


initialize_session_tool = FunctionTool(func=initialize_session)
