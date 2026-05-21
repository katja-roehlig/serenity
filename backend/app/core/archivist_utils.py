from datetime import datetime, timedelta, timezone
from importlib import metadata
from tkinter import S
from langchain_core.documents import Document
from app.services.vector_service import VECTOR_SERVICE
from app.schemas.ai_schemas import MemoryItem
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import UserProperty
from app.services.user_property_service import USER_PROPERTY_SERVICE

logger = logging.getLogger(__name__)


async def handle_life_data(
    content: str,
    metadata: dict,
    db: AsyncSession,
):
    metadata["status"] = "active"
    if metadata["category"] == "current_situation":
        metadata["expires_at"] = (
            datetime.now(timezone.utc) + timedelta(weeks=3)
        ).strftime("%Y-%m-%d")
    embedding = await VECTOR_SERVICE.create_embedding(content)
    result = await VECTOR_SERVICE.search_memory(metadata, embedding, status="active")
    if result:
        doc, score = result[0]
        if score <= 0.2:
            if metadata["category"] == "current_situation":
                metadata["id"] = doc.metadata.get("id")
                await save_to_db(content, metadata, db)
            return
    if VECTOR_SERVICE.add_memory(content, embedding, metadata):
        try:
            await save_to_db(content, metadata, db)
        except Exception as e:
            logger.error(f"SQLite Error with 'memory' or 'safe_place'  {e}")
            await VECTOR_SERVICE.delete_memory(str(metadata["id"]))


# info.category in ["belief", "pattern", "strengths", "goal"]:
async def handle_supposed_data(
    content: str, reasoning: str, metadata: dict, db: AsyncSession
):
    expiration_date = (datetime.now(timezone.utc) + timedelta(weeks=22)).strftime(
        "%Y-%m-%d"
    )
    embedding = await VECTOR_SERVICE.create_embedding(content)
    active_result = await VECTOR_SERVICE.search_memory(
        metadata, embedding, status="active"
    )
    if active_result:
        doc, score = active_result[0]
        if score <= 0.2:
            return
    await handle_hidden_search(
        content, reasoning, metadata, embedding, expiration_date, db
    )


async def handle_hidden_search(
    content: str,
    reasoning: str,
    metadata: dict,
    embedding: list[float],
    expiration_date: str,
    db: AsyncSession,
):
    hidden_result = await VECTOR_SERVICE.search_memory(
        metadata, embedding, status="hidden"
    )
    if hidden_result:
        doc, score = hidden_result[0]
        if score <= 0.2:
            original_metadata = doc.metadata.copy()
            updated_metadata = update_metadata(doc, reasoning)
            existing_content = doc.page_content
            success = await VECTOR_SERVICE.update_memory(
                existing_content, embedding, updated_metadata
            )
            if success:
                try:
                    await USER_PROPERTY_SERVICE.update_data(
                        db, content, updated_metadata
                    )
                    return
                except Exception as e:
                    logger.error(f"SQLite Error within updating memory items: {e}")
                    original_embedding = await VECTOR_SERVICE.create_embedding(
                        existing_content
                    )
                    await VECTOR_SERVICE.update_memory(
                        existing_content, original_embedding, original_metadata
                    )
    new_metadata = create_new_metadata(metadata, reasoning)
    VECTOR_SERVICE.add_memory(content, embedding, new_metadata)
    metadata["expires_at"] = expiration_date
    try:
        await save_to_db(content, metadata, db)
    except Exception as e:
        logger.error(f"SQLite Error with hidden memory items: {e}")
        await VECTOR_SERVICE.delete_memory(str(metadata["id"]))


def create_new_metadata(metadata: dict, reasoning: str):
    metadata["status"] = "hidden"
    metadata["counter"] = 1
    metadata["reasoning"] = [reasoning]
    return metadata


def update_metadata(doc: Document, new_reasoning: str):
    updating_metadata = doc.metadata
    if updating_metadata["category"] in ["belief", "pattern"]:
        limit = 10
    else:
        limit = 3
    counter = updating_metadata.get("counter", 0) + 1
    updating_metadata["counter"] = counter
    reasoning_list = updating_metadata.get("reasoning", [])
    reasoning_list.append(new_reasoning)
    updating_metadata["reasoning"] = reasoning_list
    if counter >= limit:
        updating_metadata["status"] = "active"
    else:
        updating_metadata["status"] = "hidden"
    return updating_metadata


async def save_to_db(content: str, metadata: dict, db):
    user_property = UserProperty(
        id=metadata["id"],
        user_id=metadata["user_id"],
        category=metadata["category"],
        content=content,
        created_at=metadata["created_at"],
        expires_at=metadata.get("expires_at"),
        reasoning=metadata.get("reasoning"),
        status=metadata["status"],
        counter=metadata.get("counter"),
    )

    await USER_PROPERTY_SERVICE.add_data(db, user_property)
    logger.info(f"Erfolgreich in SQLite gespeichert für User {metadata['user_id']}")
