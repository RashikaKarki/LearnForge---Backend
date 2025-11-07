import json

from google.adk.tools import ToolContext
from google.generativeai import GenerativeModel

from app.models.mission import MissionCreate


def fetch_mission_details(tool_context: ToolContext) -> str:
    """Creates a structured mission from Pathfinder's collected learning goal information."""

    # Get the pathfinder output from state
    pathfinder_output = tool_context.state.get("generated_outline_with_user_preferences", "")
    creator_id = tool_context.state.get("creator_id", "")

    # Initialize the LLM
    model = GenerativeModel("gemini-2.5-flash")

    response_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "short_description": {"type": "string"},
            "description": {"type": "string"},
            "creator_id": {"type": "string"},
            "level": {"type": "string", "enum": ["Beginner", "Intermediate", "Advanced"]},
            "topics_to_cover": {"type": "array", "items": {"type": "string"}},
            "learning_goal": {"type": "string"},
            "byte_size_checkpoints": {"type": "array", "items": {"type": "string"}},
            "skills": {"type": "array", "items": {"type": "string"}},
            "learning_style": {"type": "array", "items": {"type": "string"}},
            "is_public": {"type": "boolean"},
        },
        "required": [
            "title",
            "short_description",
            "description",
            "creator_id",
            "level",
            "topics_to_cover",
            "learning_goal",
            "byte_size_checkpoints",
            "skills",
            "learning_style",
            "is_public",
        ],
    }

    # Create the prompt
    prompt = f"""SYSTEM INSTRUCTIONS — STEP BY STEP:

Use the information provided by Polaris to create a structured MissionCreate JSON for the user.

PATHFINDER OUTPUT:
{pathfinder_output}

CREATOR ID: {creator_id}

1) Identity & Role
   - You are "Mission Curator".
   - Your sole task is to take the information collected by Polaris (user's topic, goals, prerequisites, preferences, etc.) and produce a fully structured MissionCreate JSON.

2) Input Context
   - User's creator ID: {creator_id}
   - Use this creator_id value for the creator_id field in your output

3) Output Requirements - MissionCreate Schema
   - title: Final, focused topic/course name
   - short_description: 1-2 sentence summary of the mission (concise)
   - description: Detailed description of the mission (2-3 paragraphs)
   - creator_id: Use the {creator_id} value provided above
   - level: Must be exactly one of: "Beginner", "Intermediate", "Advanced"
   - topics_to_cover: List of all necessary topics including prerequisites based on user's background
   - learning_goal: 3-4 sentences explaining the user's learning goal and what they aim to achieve
   - byte_size_checkpoints: List of 4-6 checkpoint names in logical order (including prerequisites)
   - skills: List of key skills the user will learn (e.g., ["Python", "Data Analysis", "Machine Learning"])
   - learning_style: Use user's preferred learning styles (e.g., ["examples", "metaphors", "analogies", "step-by-step"])
   - is_public: Set to true (default)

4) Formatting Rules
   - Produce **valid JSON only**, strictly matching the MissionCreate schema
   - Do NOT ask the user any questions — only format and organize the information
   - Keep descriptions concise and checkpoints logical and sequential
   - Ensure 4-6 checkpoints (no more, no less)
   - byte_size_checkpoints must be a list of strings (checkpoint names only)

5) Important Notes
   - Integrate prerequisites into the checkpoints if possible
   - Ensure clarity, readability, and a structured logical flow
   - Avoid adding unrelated information; only include data relevant to the user's learning goal
   - Extract key skills from the topics and user's learning goal

Example byte_size_checkpoints format:
[
  "Introduction to Python Basics",
  "Variables and Data Types",
  "Control Flow and Functions",
  "Working with Data Structures",
  "File Handling and Modules",
  "Final Project: Building a Simple Application"
]

Return ONLY the JSON object, no markdown formatting, no extra text.
"""

    # Generate the response with Pydantic schema
    response = model.generate_content(
        prompt,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": response_schema,
            "temperature": 0.7,
        },
    )

    mission_data = json.loads(response.text)
    validated_mission = MissionCreate(**mission_data)

    return validated_mission.model_dump(mode="json")
