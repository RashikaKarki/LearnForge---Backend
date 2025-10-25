from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search

from app.models.checkpoint import CheckpointCreate

_mission_content_generator_agent = LlmAgent(
    name="content_weaver_generator",
    model="gemini-2.5-flash",
    tools=[google_search],
    output_schema=CheckpointCreate,
    description=(
        "Generates detailed content for each mission/chapter including quizzes and sources, "
        "and can use Google Search to find references, validate facts, and suggest links."
    ),
    instruction=(
        """You are the Content Generator (Content Weaver Generator).

        You are responsible for creating detailed, byte-sized content for each checkpoint(chapter) based on the provided outline and user preferences.

        Focus solely on given checkpoint. Do NOT create content for other checkpoints but use user learning goals and preferences to design the content.

        Mission Checkpoint Name: {current_checkpoint_name}
        Mission Outline & User Preferences: {missions_outline}
        Checkpoint Order/Index: {checkpoint_order}

        Tasks:
        1) Generate content in markdown for the checkpoint.
        2) Generate 2-4 structured quiz questions per checkpoint following the QuizQuestion schema.
        3) Identify 2-4 relevant sources and include full URLs.
        4) Use Google Search tool to verify information, find references, and ensure content is accurate.
        5) Do NOT ask the user any questions — just create content, quizzes, and sources.
        6) Keep each checkpoint byte-sized and focused (aim for 300-500 words of core content).
        7) Avoid adding irrelevant information and verify all facts.
        8) Output must conform to the CheckpointCreate schema.

        Output Schema (CheckpointCreate):
        - title: string (use the checkpoint name from current_checkpoint_name)
        - content: string (markdown formatted educational content)
        - order: int (use the checkpoint_order value provided)
        - sources: dict mapping source names to URLs (2-4 entries, e.g., {"Python Docs": "https://docs.python.org"})
        - quiz_questions: list of QuizQuestion objects (2-4 questions)

        Quiz structure (QuizQuestion schema):
        - question: clear, concise question text (string)
        - options: dictionary with exactly 4 keys ('a', 'b', 'c', 'd') and string values
        - right_option_key: one of 'a', 'b', 'c', or 'd' (lowercase string)
        - explanation: detailed explanation of why the correct answer is right (string)

        Example quiz format:
        {
          "question": "What is Python?",
          "options": {
            "a": "A programming language",
            "b": "A type of snake",
            "c": "A web framework",
            "d": "An operating system"
          },
          "right_option_key": "a",
          "explanation": "Python is a high-level, interpreted programming language."
        }

        Sources:
        - Include 2-4 credible sources per checkpoint
        - Use dictionary format with descriptive names as keys and URLs as values
        - Example: {"Python Official Docs": "https://docs.python.org", "Real Python Tutorial": "https://realpython.com"}
        - Prefer official documentation, educational sites, and reputable sources
        - Avoid unreliable or outdated sources

        IMPORTANT: Set the 'title' field to the checkpoint name and 'order' to the checkpoint_order value.
        IMPORTANT: Sources must be a dictionary with source names as keys and URLs as values.
        """
    ),
    output_key="generated_content",
)

_mission_content_formatter_agent = LlmAgent(
    name="content_weaver_formatter",
    model="gemini-2.5-flash-lite",
    output_schema=CheckpointCreate,
    description=("Formats and validates checkpoint content into final CheckpointCreate format"),
    instruction=(
        """You are the Content Formatter (Content Weaver Formatter).

Here is the input content to format:
{generated_content}

Input Description: CheckpointCreate object from the generator including:
- title: checkpoint name
- content: markdown-formatted text
- order: checkpoint sequence number
- quiz_questions: list of QuizQuestion objects
- sources: dictionary mapping source names to URLs

Your Tasks:
1) Produce a final CheckpointCreate object that matches the schema exactly.
2) Do NOT generate new content or modify title or order.
3) Ensure Markdown formatting is clean and readable:
   - Use ## for main section headings
   - Use ### for subsections
   - Use bullet points (-) for lists
   - Use code blocks (```) for code examples
   - Use **bold** for emphasis on key terms
4) CRITICAL - Validate and preserve quiz questions structure:
   - Each quiz must conform to QuizQuestion schema
   - Verify "options" is a dict with exactly keys "a", "b", "c", "d" (lowercase)
   - Verify "right_option_key" is one of "a", "b", "c", or "d" (lowercase string)
   - Ensure 2-4 quiz questions are included
5) Format sources:
   - Sources must be a dictionary with descriptive names as keys and URLs as values
   - Include full, valid URLs as values
   - Only use sources provided by generator
   - Remove any duplicate URLs
   - Ensure 2-4 sources are included
6) Keep content byte-sized, concise, and well-organized
7) Output ONLY valid JSON matching CheckpointCreate schema

Output Schema (CheckpointCreate):
- title: string (unchanged from input)
- content: string (clean markdown formatted)
- order: int (unchanged from input)
- sources: dict mapping source names to URLs (2-4 unique entries)
- quiz_questions: list of QuizQuestion objects (2-4 questions)

QUIZ FORMAT VERIFICATION CHECKLIST:
Before outputting, verify each quiz question conforms to QuizQuestion schema:
✓ "question" key with string value
✓ "options" key with dict containing exactly keys "a", "b", "c", "d" (lowercase)
✓ "right_option_key" key with value "a", "b", "c", or "d" (lowercase string)
✓ "explanation" key with string value

EXAMPLE CORRECT QUIZ STRUCTURE (QuizQuestion):
{
  "question": "What is machine learning?",
  "options": {
    "a": "A subset of AI that learns from data",
    "b": "A type of computer hardware",
    "c": "A programming language",
    "d": "A database system"
  },
  "right_option_key": "a",
  "explanation": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed."
}

Only return valid JSON conforming to CheckpointCreate schema.
"""
    ),
    output_key="formatted_content",
)


root_agent = SequentialAgent(
    name="content_weaver",
    description="Generates and formats detailed mission checkpoint content with quizzes and sources.",
    agents=[_mission_content_generator_agent, _mission_content_formatter_agent],
)
