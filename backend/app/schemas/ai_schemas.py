from typing import Literal, Optional
import uuid

from pydantic import BaseModel, Field


class StateAnalysis(BaseModel):
    is_user_ready: bool = Field(
        description="Can the user physically/mentally perform an exercise right now?"
    )
    is_exercise_useful: bool = Field(
        description="Is an exercise better than just talking right now?"
    )
    has_enough_info: bool = Field(
        description="True ONLY if the user has provided enough context to select a SPECIFIC exercise. If the user is vague (e.g., 'I feel bad'), set to False so we can ask clarifying questions first."
    )
    needs_research: bool = Field(
        description="Do we need to search the web to understand a term or situation?"
    )


# Literal definiert categorien,wählt die KI etwas anders, wird ein Fehler geworfen.
CategoryType = Literal[
    "current_situation",
    "memory",
    "belief",
    "pattern",
    "goal",
    "strengths",
    "safe_place",
]


class MemoryItem(BaseModel):
    id: str | None = Field(
        default=None, exclude=True
    )  # mit exclude = True ignoriert die ki das Feld
    category: CategoryType = Field(
        description=(
            "current_situation: Current status of job/education, relationships, family, pets,conflicts, health, mood and acute and upcoming life events."
            "memory: Significant past events and biographical facts that shaped the user (e.g., childhood, trauma, past relationship milestones, holidays, partys, or major life changes)\n"
            "belief: Deep, internal negative core beliefs and convictions about oneself or the world (The 'Why').\n"
            "pattern: Recurring, observable behaviors or emotional reactions in specific situations, mostly negative (The 'How').\n"
            "goal: Wishes, future plans, or personal development goals.\n"
            "strengths: Internal personal skills, positive character traits, learned abilities, or notable personal achievements (e.g., resilience, leadership, fitness).\n"
            "safe_place: The mental or real comfort zone/safe place of the user."
        )
    )

    content: str = Field(
        description="Max 20-30 words. Fact-based, concise, to the point. Avoid metaphors or fluffy language."
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="ONLY for belief, pattern, goal, strengths: Short context why this was identified. Leave empty (None) for current_situation, memory, safe_place.",
    )


class ArchivistOutput(BaseModel):
    items: list[MemoryItem] = Field(
        description="A list containing all newly extracted insights from the conversation."
    )
