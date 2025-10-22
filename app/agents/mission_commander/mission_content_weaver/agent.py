from typing import AsyncGenerator

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.tools import google_search

_mission_content_generator_agent = LlmAgent(
    name="content_weaver_generator",
    model="gemini-2.5-flash",
    tools=[google_search],
    description=(
        "Generates detailed content for each mission/chapter including quizzes and sources, "
        "and can use Google Search to find references, validate facts, and suggest links."
    ),
    instruction=(
        """You are the Content Generator (Content Weaver Generator).

        You are responsible for creating detailed, byte-sized content for each checkpoint(chapter) based on the provided outline and user preferences.

        Focus solely on given checkpoint. Do NOT create content for other checkpoints but use user learning goals and preferences to design the content.

        Mission Checkpoint Name: {current_checkpoint_name}
        User Learning Goals & Preferences: {generated_outline_with_user_preferences}

        Tasks:
        1) Generate content in markdown for the checkpoint. Do not change the checkpoint_name.
        2) Generate 2-4 structured quiz questions per checkpoint.
        3) Identify relevant sources and include links.
        4) Use Google Search tool to verify information, find references, and ensure content is accurate.
        5) Do NOT ask the user any questions — just create content, quizzes, and sources.
        6) Keep each checkpoint byte-sized and focused (aim for 300-500 words of core content).
        7) Avoid adding irrelevant information and verify all facts.

        Quiz structure:
        - question: clear, concise question text
        - options: dictionary with exactly 4 keys ('a', 'b', 'c', 'd') and string values
        - right_option_key: one of 'a', 'b', 'c', or 'd'
        - explanation: detailed explanation of why the correct answer is right

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
        - Include 2-4 credible sources per mission
        - Use full URLs (e.g., https://example.com/article)
        - Prefer official documentation, educational sites, and reputable sources
        - Avoid unreliable or outdated sources
        """
    ),
    output_key="generated_content",
)

_mission_content_formatter_agent = LlmAgent(
    name="content_weaver_formatter",
    model="gemini-2.5-flash-lite",
    description=(
        "Formats mission checkpoint content into a user-ready format with quizzes and sources"
    ),
    instruction=(
        """You are the Content Formatter (Content Weaver Formatter).

Here is the input content to format:
{generated_content}

Input Description: validated mission content from the generator including:
- mission_name: string (don't modify this)
- content: markdown-formatted text
- quiz_questions: list of question dictionaries
- sources_links: list of source URLs

Your Tasks:
1) Produce a final MissionContent object that matches the schema exactly.
2) Do NOT generate new content or modify mission_name.
3) Ensure Markdown formatting is clean and readable:
   - Use ## for main section headings
   - Use ### for subsections
   - Use bullet points (-) for lists
   - Use code blocks (```) for code examples
   - Use **bold** for emphasis on key terms
4) CRITICAL - Format quiz questions correctly as dictionaries:
   - Each quiz dictionary MUST have exactly these 4 keys: "question", "options", "right_option_key", "explanation"
   - "options" MUST be a dictionary with exactly 4 keys: "a", "b", "c", "d" (lowercase)
   - "right_option_key" MUST be one of: "a", "b", "c", or "d" (lowercase string)
   - Do NOT use lists for options - only dictionaries
   - Do NOT use uppercase letters or numbers for option keys
   - Include 2-4 quiz questions per mission
5) Format sources:
   - Include full, valid URLs
   - Only use sources provided by generator
   - Remove any duplicate URLs
6) Keep content byte-sized, concise, and well-organized
7) Output ONLY the JSON object - no extra text

QUIZ FORMAT VERIFICATION CHECKLIST:
Before outputting, verify each quiz question has:
✓ "question" key with string value
✓ "options" key with dictionary containing exactly keys "a", "b", "c", "d" (lowercase)
✓ "right_option_key" key with value "a", "b", "c", or "d" (lowercase string)
✓ "explanation" key with string value

EXAMPLE CORRECT QUIZ STRUCTURE:
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

Output must strictly follow the json schema with fields:
- mission_checkpoint_name: string
- content: string (markdown formatted)
- sources_links: list of strings (URLs)
- quiz_questions: list of dictionaries (each with question, options, right_option_key, explanation)

Only return json.
"""
    ),
    output_key="formatted_content",
)


class ContentWeaverCustomAgent(BaseAgent):
    """
    Custom agent that processes each mission sequentially, yielding events
    for each mission as it completes.
    """

    generator: LlmAgent
    formatter: LlmAgent

    def __init__(
        self,
        name: str = "content_weaver",
        description: str = "Generates, validates, and formats detailed mission/chapter content sequentially, yielding each mission as it completes.",
    ):
        generator = _mission_content_generator_agent
        formatter = _mission_content_formatter_agent

        sub_agents_list = [generator, formatter]

        super().__init__(
            name=name,
            description=description,
            generator=generator,
            formatter=formatter,
            sub_agents=sub_agents_list,
        )

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        missions_outline = ctx.session.state.get("missions_outline", {})
        byte_size_checkpoints = missions_outline.get("byte_size_checkpoints", [])

        if not byte_size_checkpoints:
            raise ValueError(
                "No missions found in missions_outline. Ensure Mission Curator has run successfully."
            )

        ctx.session.state["total_checkpoints"] = len(byte_size_checkpoints)
        for checkpoint_index, checkpoint_name in enumerate(byte_size_checkpoints):
            ctx.session.state["current_checkpoint_name"] = checkpoint_name
            ctx.session.state["current_checkpoint_index"] = checkpoint_index + 1

            # Generate content
            async for event in self.generator.run_async(ctx):
                yield event

            generated_content = ctx.session.state.get("generated_content")
            if generated_content:
                # Format content
                async for event in self.formatter.run_async(ctx):
                    yield event

            formatted_content = ctx.session.state.get("formatted_content")
            if formatted_content:
                ctx.session.state[f"checkpoint_{checkpoint_index + 1}_content"] = (
                    formatted_content
                )

        ctx.session.state["content_generation_complete"] = True


root_agent = ContentWeaverCustomAgent(
    name="content_weaver",
    description="Generates, validates, and formats mission checkpoint content sequentially, yielding each mission as it completes.",
)
