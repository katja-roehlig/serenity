from typing import Literal, Optional
import uuid

from pydantic import BaseModel, Field


class StateAnalysis(BaseModel):

    is_user_overwhelmed_or_stuck: bool = Field(
        description="True ONLY if the user is in acute distress: either spinning in circles (loops), panicking, dissociating, or stating they feel completely helpless. FALSE if they are just describing a problem or sending their first messages."
    )

    is_exercise_needed: bool = Field(
        description="True ONLY if the user's nervous system is in an active alarm state and continuing a normal text conversation provides no immediate relief. FALSE if they are actively telling a story."
    )
    has_user_background: bool = Field(
        description="True ONLY if we know: 1) the core problem, 2) the user's goal, AND 3) how they reacted to the chatbot's previous guidance. ALWAYS False on the first turn."
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
            "current_situation: IMPORTANT! Real-life facts about the user's present right now (e.g., job, upcoming events, conflicts, mood). Never skip these facts!\n"
            "memory: IMPORTANT! Real-life biographical facts and events from the user's past (e.g., childhood, events from months/years ago). Never skip these facts!\n"
            "belief: Deep, negative core beliefs (The 'Why'). The CONTENT field must strictly be a short, abstract meta-headline without names, roles, or story details.\n"
            "pattern: Recurring, automated negative behaviors (The 'How'). The CONTENT field must strictly be a short, generalized psychological concept without story details.\n"
            "goal: Wishes, future plans, or personal development goals.\n"
            "strengths: Internal personal skills, positive character traits, learned abilities, or notable personal achievements.\n"
            "safe_place: Mental or real comfort zones where the user feels secure."
        )
    )
    content: str = Field(
        description="Max 10-25 words. Fact-based, concise, to the point. Avoid metaphors or fluffy language."
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="ONLY for belief, pattern, goal, strengths: Short context (10-20words) why this was identified, here is the place for more details. Leave empty (None) for current_situation, memory, safe_place.",
    )


class ArchivistOutput(BaseModel):
    items: list[MemoryItem] = Field(
        description="A list containing all newly extracted insights from the conversation."
    )
