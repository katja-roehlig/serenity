from datetime import datetime, timedelta, timezone
from functools import partial
import os
from typing import List, Sequence, TypedDict, cast
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
    found_items: List[MemoryItem]


async def analyze_messages(state: ArchivistState):
    print("--- NODE: ANALYZE MESSAGES ---")
    system_prompt = f"""
    Du bist ein empathischer, hochpräziser psychologischer Analyst für eine App zur Persönlichkeitsentwicklung. 
    Analysiere diese Nachrichten des Users. 
    Nutze die Definitionen der Kategorien aus dem übergebenen Pydantic-Schema, um relevante Langzeit-Erkenntnisse zu extrahieren.

    WICHTIGE REGELN:
    1.  Relevanz: Erstelle nur Einträge für Kategorien, wenn du im Text klare Beweise dafür findest. 
        Wenn die Nachrichten belanglos waren, nichts Neues oder nur eine Übung enthalten, gib eine leere Liste zurück.
    2.  Sprache & Stil: Schreibe die Felder 'content' und 'reasoning' auf Deutsch. 
        Halte den 'content' extrem knackig auf maximal 20-30 Wörter begrenzt, faktenbasiert und ohne Floskeln. Nenne konkrete Namen, falls erwähnt.

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
    for info in new_infos:
        metadata = {
            "id": info.id,
            "user_id": user_id,
            "category": info.category,
            "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        }
        content = info.content
        reasoning = str(info.reasoning) if info.reasoning else ""
        if info.category in ["current_situation", "memory", "safe_place"]:
            await handle_life_data(content, metadata, db)
        elif info.category in ["belief", "pattern", "strengths", "goal"]:
            await handle_supposed_data(content, reasoning, metadata, db)
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
