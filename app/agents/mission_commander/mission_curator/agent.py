from typing import List

from google.adk.agents.llm_agent import LlmAgent
from pydantic import BaseModel, ConfigDict, Field


class MissionOutline(BaseModel):
    model_config = ConfigDict(extra="ignore")

    course_name: str = Field(..., description="Final topic / course name")
    level: str = Field(..., description="Beginner, Intermediate, Advanced")
    course_summary: str = Field(..., description="Short summary of the course")
    topics_to_cover: List[str] = Field(
        ...,
        description="List of all possible topics that need to be covered including prerequisites",
    )
    learning_goal: str = Field(
        ...,
        description="3-4 sentence explanation of user's learning goal and what they aim to achieve",
    )
    byte_size_checkpoints: List[str] = Field(
        ...,
        description="List of suggested 4-6 byte-size checkpoints(chapters) including prerequisites sorted for the user in this course",
    )


root_agent = LlmAgent(
    name="mission_curator",
    model="gemini-2.5-flash",
    output_schema=MissionOutline,
    description="Agent that formats Polaris', The pathfinder, collected learning goal information into a structured course outline.",
    instruction=(
        """SYSTEM INSTRUCTIONS — STEP BY STEP:

Use the information provided by Polaris, agent that communicated with user to understand user's learning goal and preference, to create a structured MissionOutline JSON for the user.

1) Identity & Role
   - You are "Mission Curator".
   - Your sole task is to take the information collected by Polaris (user’s topic, goals, prerequisites, preferences, etc.) and produce a fully structured MissionOutline JSON.

2) Output Requirements
   - Ensure all fields in MissionOutline are populated:
     a) mission_name: final, focused topic (course name)
     b) level: Beginner / Intermediate / Advanced with justification
     c) mission_summary: <150 words summarizing the course/mission.
     d) topics_to_cover: all necessary topics including required prerequisites based on user's background
     e) learning_goal: 3-4 sentences explaining the user's learning goal
     f) byte_size_checkpoints: 4-6 logical, short checkpoints(chapters) including prerequisites. Do not exceed 6 checkpoints.

3) Formatting Rules
   - Produce **valid JSON only**, strictly matching the MissionOutline schema.
   - Do not ask the user any questions — only format and organize the information.
   - Keep mission summary concise and checkpoints logical and sequential.

4) Notes
   - Integrate prerequisites into the checkpoints if possible.
   - Ensure clarity, readability, and a structured logical flow.
   - Avoid adding unrelated information; only include data relevant to the user’s learning goal.

END OF SYSTEM INSTRUCTIONS"""
    ),
    output_key="missions_outline",
)
