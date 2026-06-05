from datetime import datetime, timedelta, timezone
from functools import partial
import os
from typing import List, Sequence, TypedDict, cast
import uuid
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from app.schemas.ai_schemas import MemoryItem, ArchivistOutput
from app.core.archivist_utils import (
    handle_life_data,
    handle_supposed_data,
)
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from langchain_core.utils.utils import convert_to_secret_str
from app.services.user_property_service import USER_PROPERTY_SERVICE
from app.services.vector_service import VECTOR_SERVICE

logger = logging.getLogger(__name__)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Attention: OPENAI_API_KEY was not found in .env file!")

analyze_model = ChatOpenAI(
    temperature=0.0, model="gpt-4.1-mini", api_key=convert_to_secret_str(OPENAI_API_KEY)
)


class ArchivistState(TypedDict):
    messages: Sequence[BaseMessage]
    user_id: str
    user_name: str
    found_items: List[MemoryItem]


async def analyze_messages(state: ArchivistState):
    print("--- NODE: ANALYZE MESSAGES ---")

    system_prompt = f"""
    Du bist der hochpräzise biografische Analyst und Chronist für eine App zur Persönlichkeitsentwicklung. 
    Deine Aufgabe ist es, die Lebensdaten des Users sachlich zu strukturieren und seine inneren Baustellen für die Weiterentwicklung zu kartografieren.

    STRATEGIE FÜR VOLLSTÄNDIGKEIT:
    1. Lies den Chatverlauf. Nutze die Definitionen der Kategorien aus dem Pydantic-Schema.
    2. Gehe den Text im Geiste für jede der 7 Kategorien einzeln durch. Beginne mit der ersten und gucke, ob du Infos findest, nimm dann die zweite Lategorie, dann die dritte und so weiter. 
    Wenn du Beweise für eine Kategorie findest, erstelle einen Eintrag. Wenn nicht, überspringe sie.
    3. Brich die Analyse nicht ab, sobald du 1-2 Einträge hast. Häufig verstecken sich in den Nachrichten Informationen viele verschiedene Kategorien.
    4. Strikte Thementrennung (Atomare Einträge): Wenn der User von zwei verschiedenen Themen erzählt, erstelle zwei separate Einträge. Wichtig für ChromaDB!
    5. Sprache: Schreibe die Felder 'content' und 'reasoning' immer auf Deutsch und ich der 1.Person Singular (Ich-Perspektive).

    Falls die Nachrichten absolut keine relevanten Informationen enthalten, gib eine leere Liste zurück.
    """

    messages = [SystemMessage(content=system_prompt)] + list(state["messages"])

    structured_llm = analyze_model.with_structured_output(ArchivistOutput)
    # ai_result hat die Form: ArchivistOutput(items=[MemoryItem(...), MemoryItem(...)])
    ai_result = cast(ArchivistOutput, await structured_llm.ainvoke(messages))
    return {"found_items": ai_result.items}


async def save_information(state: ArchivistState, db: AsyncSession):
    print("--- NODE: SAVE INFORMATION ---")
    user_id = state["user_id"]
    new_infos = state["found_items"]
    print(f"NEW INFOS: {new_infos}")
    user_name = state.get("user_name", "")
    for info in new_infos:
        metadata = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "category": info.category,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        content = info.content
        reasoning = str(info.reasoning) if info.reasoning else ""
        if info.category in ["current_situation", "memory", "safe_place"]:
            await handle_life_data(content, metadata, user_name, db)
        elif info.category in ["belief", "pattern", "strengths", "goal"]:
            await handle_supposed_data(content, reasoning, metadata, user_name, db)
        else:
            logger.warning(f"Unknown category: {info.category}")
    return {}


async def clean_expired_information(state: ArchivistState, db: AsyncSession):
    print("--- NODE: CLEAN EXPIRED INFORMATION ---")
    user_id = state["user_id"]
    expired_data = await USER_PROPERTY_SERVICE.find_expired_data(user_id, db)
    if not expired_data:
        logger.info(f"No expired data found for user {user_id}.")
        return {}
    for item in expired_data:
        data_id = item.id
        success = await VECTOR_SERVICE.delete_memory(data_id)
        if not success:
            logger.warning(
                f"Failed to delete entry {data_id} from VectorDB. Skipping SQL deletion."
            )
            continue

        db_success = await USER_PROPERTY_SERVICE.delete_data_by_id(data_id, db)
        if not db_success:
            logger.warning(f"Failed to delete entry {data_id} from user_properties.")
            continue
        logger.info(f"Successfully cleaned up entry {data_id} from all storages.")

    return {}


def create_archivist_agent(db: AsyncSession):
    # Graph wird initialisiert
    workflow = StateGraph(ArchivistState)

    # Nodes zum Graphen hinzufügen, mit partial werden die argumente hinzugefügt - workflow.add_node("name", function)
    workflow.add_node("analyze_messages", analyze_messages)
    workflow.add_node("save_information", partial(save_information, db=db))
    workflow.add_node(
        "clean_expired_information", partial(clean_expired_information, db=db)
    )

    workflow.set_entry_point("analyze_messages")

    workflow.add_edge("analyze_messages", "save_information")
    workflow.add_edge("save_information", "clean_expired_information")
    workflow.add_edge("clean_expired_information", END)

    return workflow.compile()
