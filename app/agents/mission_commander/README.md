````markdown
# Mission Commander Agent

Orchestrates the complete learning journey from goal clarification to mission creation through coordinated sub-agents.

## Architecture

`LlmAgent` orchestrator with two sequential sub-agents:
1. **Pathfinder (Polaris)**: Clarifies user's learning goal through guided conversation
2. **Mission Curator**: Converts collected information into structured mission outline

## Sub-Agents

### 1. Pathfinder (Polaris)
**Role**: Interactive guide that helps users define focused learning goals

**Capabilities**:
- Socratic questioning to clarify learning objectives
- Google Search integration for topic research
- Prior experience assessment
- Prerequisite gap identification
- Learning style preference collection

**Collects**:
- Topic name and depth level
- Learning goals (3-5 measurable outcomes)
- Prerequisites and prior experience
- Topics to cover (main + prerequisite)
- Learning style preferences

**Output Key**: `generated_outline_with_user_preferences`

### 2. Mission Curator
**Role**: Formats Pathfinder's collected data into structured mission schema

**Output**: `MissionCreate` with:
- `title`, `short_description`, `description`
- `creator_id` (from session context)
- `level`: `"Beginner"` | `"Intermediate"` | `"Advanced"`
- `topics_to_cover`: List of all topics including prerequisites
- `learning_goal`: 3-4 sentence summary
- `byte_size_checkpoints`: 4-6 checkpoint names in logical order
- `skills`: List of key skills to be learned
- `is_public`: Boolean (default: true)

**Output Key**: `mission_create`

## Flow

```
User → Orchestrator (auto-start) 
     → Pathfinder (goal clarification)
     → Mission Curator (mission structure)
     → MissionCreate output
```

## Input

Session state parameters:
- `creator_id`: User ID of mission creator (string)

## Output

Returns `MissionCreate` ready for database persistence.

## Usage

### Basic Usage

```python
from app.agents.mission_commander.agent import root_agent

# Configure session
ctx.session.state["creator_id"] = "user123"

# Run orchestrator (auto-starts with Pathfinder)
async for event in root_agent.run_async(ctx):
    yield event

# Get final mission structure
mission_create = ctx.session.state["mission_create"]
```

### Save to Database

```python
from app.services.mission_service import MissionService

# Get mission data from session
mission_create = ctx.session.state["mission_create"]

# Create mission in database
mission = mission_service.create_mission(mission_create)
print(f"Mission created with ID: {mission.id}")
```

### Access Pathfinder Data

```python
# Access Pathfinder's collected information
user_preferences = ctx.session.state["generated_outline_with_user_preferences"]

print(user_preferences["topic_name"])
print(user_preferences["depth_level"])
print(user_preferences["learning_goals"])
print(user_preferences["prerequisites_required"])
print(user_preferences["user_prior_experience"])
print(user_preferences["topics_to_cover"])
print(user_preferences["learning_style_preferences"])
```

### Access Mission Curator Output

```python
mission_create = ctx.session.state["mission_create"]

# Access fields
print(mission_create.title)                    # "Python for Data Science"
print(mission_create.short_description)        # "Learn Python fundamentals..."
print(mission_create.level)                    # "Beginner"
print(mission_create.topics_to_cover)          # ["Variables", "Functions", ...]
print(mission_create.learning_goal)            # "Master Python fundamentals..."
print(mission_create.byte_size_checkpoints)    # ["Intro to Python", ...]
print(mission_create.skills)                   # ["Python", "Data Analysis"]
```

### Complete End-to-End Example

```python
from app.agents.mission_commander.agent import root_agent
from app.services.mission_service import MissionService

async def create_personalized_mission(user_id: str):
    # Initialize context
    ctx = create_context()
    ctx.session.state["creator_id"] = user_id
    
    # Run mission commander (orchestrates Pathfinder → Curator)
    async for event in root_agent.run_async(ctx):
        # Stream events to user (conversation with Pathfinder)
        yield event
    
    # Get structured mission
    mission_create = ctx.session.state["mission_create"]
    
    # Validate checkpoint count (4-6 required)
    checkpoint_count = len(mission_create.byte_size_checkpoints)
    assert 4 <= checkpoint_count <= 6, f"Invalid checkpoint count: {checkpoint_count}"
    
    # Save to database
    mission_service = MissionService(db)
    mission = mission_service.create_mission(mission_create)
    
    return mission
```

## Automatic Transfers

The orchestrator handles transitions automatically:

1. **Session Start**: Auto-transfers to Pathfinder
2. **Goal Confirmed**: Auto-transfers to Mission Curator when user confirms

**Completion Signals** (triggers auto-transfer):
- User says: "yes", "looks good", "correct", "proceed", "let's go"
- Pathfinder signals: "GOAL_CONFIRMED"
- User confirms learning goal summary

## Orchestrator Behavior

**Does**:
- Automatically starts Pathfinder on new sessions
- Detects Pathfinder completion signals
- Transfers to Mission Curator without user interaction
- Stays silent during agent operations

**Does NOT**:
- Engage in conversation with user
- Ask permission for transfers
- Create learning content
- Interrupt agent conversations

## Models

### MissionCreate Schema
```python
class MissionCreate(BaseModel):
    title: str
    short_description: str
    description: str
    creator_id: str
    level: Literal["Beginner", "Intermediate", "Advanced"]
    topics_to_cover: list[str]
    learning_goal: str
    byte_size_checkpoints: list[str]  # min_length=4, max_length=6
    skills: list[str] | None = []
    is_public: bool = True
```

### Pathfinder Output Format
```python
{
    "topic_name": str,
    "depth_level": "Beginner" | "Intermediate" | "Advanced",
    "depth_justification": str,
    "learning_goals": list[str],
    "prerequisites_required": list[str],
    "user_prior_experience": str,
    "topics_to_cover": list[str],
    "prerequisite_topics": list[str],
    "learning_style_preferences": list[str],
    "confirmed": bool
}
```

## Validation

### Mission Curator Validation
- **Checkpoints**: Exactly 4-6 items
- **Level**: Must be one of three literal values
- **Topics**: Must include prerequisites if user lacks them
- **Skills**: Extracted from topics and goals

### Pathfinder Validation
- **Topic Focus**: Single, specific topic (not multiple broad topics)
- **Prerequisites**: Verified through follow-up questions
- **Confirmation**: Required before completion

## Example Session Flow

```
User: "I want to learn Python"
Pathfinder: "Great! What's your main motivation for learning Python?"

User: "I want to analyze data"
Pathfinder: "Do you have any programming experience?"

User: "No, I'm a complete beginner"
Pathfinder: "What specific data analysis tasks interest you most?"

User: "Working with spreadsheets and creating visualizations"
Pathfinder: [Summarizes and confirms]

User: "Yes, that's correct"
Orchestrator: [Auto-transfers to Mission Curator]

Mission Curator: [Creates MissionCreate structure]
```

## Example Output

```python
MissionCreate(
    title="Python for Data Analysis",
    short_description="Learn Python fundamentals and apply them to data analysis tasks.",
    description="This mission will guide you through Python basics...",
    creator_id="user123",
    level="Beginner",
    topics_to_cover=[
        "Python Basics",
        "Variables and Data Types",
        "Control Flow",
        "Functions",
        "Working with Pandas",
        "Data Visualization"
    ],
    learning_goal="Master Python fundamentals to analyze spreadsheet data and create meaningful visualizations using popular libraries like Pandas and Matplotlib.",
    byte_size_checkpoints=[
        "Introduction to Python Programming",
        "Variables, Data Types, and Basic Operations",
        "Control Flow and Functions",
        "Introduction to Pandas for Data Analysis",
        "Data Visualization with Matplotlib",
        "Final Project: Analyzing Real-World Data"
    ],
    skills=["Python", "Data Analysis", "Pandas", "Data Visualization"],
    is_public=True
)
```

## Integration with Content Weaver

After Mission Commander creates the mission structure, use Mission Content Weaver to generate checkpoint content:

```python
from app.agents.mission_content_weaver.agent import root_agent as content_weaver

# After mission creation
mission_create = ctx.session.state["mission_create"]

# Loop through checkpoints
for index, checkpoint_name in enumerate(mission_create.byte_size_checkpoints):
    # Set context
    ctx.session.state["current_checkpoint_name"] = checkpoint_name
    ctx.session.state["missions_outline"] = ctx.session.state["generated_outline_with_user_preferences"]
    ctx.session.state["checkpoint_order"] = index + 1
    
    # Generate content
    async for event in content_weaver.run_async(ctx):
        yield event
    
    # Save checkpoint
    checkpoint_create = ctx.session.state["formatted_content"]
    checkpoint_service.create_checkpoint(mission.id, checkpoint_create)
```

## Error Handling

```python
from pydantic import ValidationError

try:
    mission = mission_service.create_mission(mission_create)
except ValidationError as e:
    # Handle validation errors
    for error in e.errors():
        print(f"Field: {error['loc']}, Error: {error['msg']}")
except HTTPException as e:
    # Handle service errors
    print(f"HTTP {e.status_code}: {e.detail}")
```

## Best Practices

1. **Always Set Creator ID**: Required for mission ownership
2. **Trust the Orchestrator**: Let it handle agent transitions automatically
3. **Stream Events**: Provide real-time feedback during Pathfinder conversation
4. **Validate Output**: Check checkpoint count and required fields before saving
5. **Preserve Session State**: Keep Pathfinder data for Content Weaver integration
6. **Handle Prerequisites**: Let Pathfinder pivot if user needs foundational topics first


````