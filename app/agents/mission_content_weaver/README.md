# Mission Content Weaver Agent

Generates detailed, byte-sized educational content for mission checkpoints with quizzes and sources.

## Architecture

`SequentialAgent` with two sub-agents:
1. **Generator**: Creates content, quizzes, and sources
2. **Formatter**: Validates and formats output

## Input

Session state parameters:
- `current_checkpoint_name`: Checkpoint name (string)
- `missions_outline`: Mission outline and user preferences (dict)
- `checkpoint_order`: Checkpoint sequence number (int)

## Output

Returns `CheckpointCreate` with:
- `title`: Checkpoint name
- `content`: Markdown-formatted content (300-500 words)
- `order`: Sequence number
- `sources`: `{"Source Name": "https://url"}` (2-4 entries)
- `quiz_questions`: List of `QuizQuestion` objects (2-4 items)

## Usage

### Basic Usage

```python
from app.agents.mission_content_weaver.agent import root_agent

# Configure session
ctx.session.state["current_checkpoint_name"] = "Introduction to Python"
ctx.session.state["missions_outline"] = mission_outline_data
ctx.session.state["checkpoint_order"] = 1

# Run agent
async for event in root_agent.run_async(ctx):
    yield event

# Get output
checkpoint_create = ctx.session.state["formatted_content"]
```

### Save to Database

```python
from app.services.checkpoint_service import CheckpointService

checkpoint = checkpoint_service.create_checkpoint(
    mission_id="mission123",
    data=checkpoint_create
)
```

### Loop Through Multiple Checkpoints

```python
byte_size_checkpoints = ["Intro to Python", "Variables", "Functions"]

for index, checkpoint_name in enumerate(byte_size_checkpoints):
    # Set context
    ctx.session.state["current_checkpoint_name"] = checkpoint_name
    ctx.session.state["checkpoint_order"] = index + 1
    
    # Generate content
    async for event in content_weaver.run_async(ctx):
        yield event
    
    # Save
    checkpoint_create = ctx.session.state["formatted_content"]
    checkpoint_service.create_checkpoint(mission_id, checkpoint_create)
```

### Access Output Fields

```python
checkpoint_create = ctx.session.state["formatted_content"]

# Access fields
print(checkpoint_create.title)           # "Introduction to Python"
print(checkpoint_create.content)         # Markdown content
print(checkpoint_create.order)           # 1

# Access sources (dict)
for source_name, url in checkpoint_create.sources.items():
    print(f"{source_name}: {url}")
# Output:
# Python Docs: https://docs.python.org
# Real Python: https://realpython.com

# Access quiz questions
for quiz in checkpoint_create.quiz_questions:
    print(quiz.question)                 # Question text
    print(quiz.options)                  # {"a": "...", "b": "...", ...}
    print(quiz.right_option_key)         # "a"
    print(quiz.explanation)              # Explanation text
```

### Convert to Dict for API Response

```python
# Convert to dict for JSON response
checkpoint_dict = checkpoint_create.model_dump()

# Or with specific fields
response = {
    "title": checkpoint_create.title,
    "content": checkpoint_create.content,
    "sources": checkpoint_create.sources,
    "quiz_count": len(checkpoint_create.quiz_questions)
}
```

## Models

### QuizQuestion
```python
class QuizQuestion(BaseModel):
    question: str
    options: dict[str, str]              # {"a": "opt1", "b": "opt2", "c": "opt3", "d": "opt4"}
    right_option_key: str                # "a" | "b" | "c" | "d"
    explanation: str
```

### CheckpointCreate
```python
class CheckpointCreate(BaseModel):
    title: str
    content: str
    order: int
    sources: dict[str, str] | None       # {"Source Name": "https://url"}
    quiz_questions: list[QuizQuestion] | None
```

## Validation

- **Content**: 300-500 words, Markdown formatted
- **Quiz**: 2-4 questions, 4 options each (a-d), lowercase keys
- **Sources**: 2-4 entries, descriptive names as keys

## Example Output

```python
CheckpointCreate(
    title="Introduction to Python",
    content="## What is Python?\n\nPython is a high-level...",
    order=1,
    sources={
        "Python Official Documentation": "https://docs.python.org/3/tutorial/",
        "Real Python Basics": "https://realpython.com/learning-paths/python3-introduction/",
        "W3Schools Python": "https://www.w3schools.com/python/"
    },
    quiz_questions=[
        QuizQuestion(
            question="What is Python primarily used for?",
            options={
                "a": "Web development and data science",
                "b": "Only mobile app development",
                "c": "Only game development",
                "d": "Operating system development"
            },
            right_option_key="a",
            explanation="Python is widely used for web development, data science, automation, and more."
        )
    ]
)
```

