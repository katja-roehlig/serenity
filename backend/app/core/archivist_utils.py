from datetime import datetime, timedelta, timezone
from importlib import metadata
import re
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
    user_name: str,
    db: AsyncSession,
):
    metadata["status"] = "active"
    embedding = await VECTOR_SERVICE.create_embedding(content)
    result = await VECTOR_SERVICE.search_memory(metadata, embedding, status="active")
    # für alle Kategorien gucken, ob es die Info schon gibt
    if result:
        doc, score = result[0]
        print(f"LIFE-DATA: OLD: {doc.page_content} - SCORE: {score} - NEW: {content}")
        if score <= 0.9:
            # Wenn ja und ktegorien safe_place und memory, nix tun
            if metadata["category"] == "memory" or metadata["category"] == "safe_place":
                return
            # wenn Kategorie current_situation content überschreiben in Vektor und SQL, in SQL Ablaufdatum verlängern!
            old_content = doc.page_content
            success = await VECTOR_SERVICE.update_memory(content, embedding, metadata)
            if success:
                try:
                    metadata["expires_at"] = (
                        datetime.now(timezone.utc) + timedelta(weeks=3)
                    ).strftime("%Y-%m-%d")
                    await USER_PROPERTY_SERVICE.update_data(db, content, metadata)
                    return
                except Exception as e:
                    # alten content wieder herstellen!
                    logger.error(f"SQLite Error within updating current_situation: {e}")
                    original_embedding = await VECTOR_SERVICE.create_embedding(
                        old_content
                    )
                    await VECTOR_SERVICE.update_memory(
                        old_content, original_embedding, metadata
                    )
                    raise
    if VECTOR_SERVICE.add_memory(content, embedding, metadata):
        try:
            if metadata["category"] == "current_situation":
                metadata["expires_at"] = (
                    datetime.now(timezone.utc) + timedelta(weeks=3)
                ).strftime("%Y-%m-%d")
            await save_to_db(content, metadata, user_name, db)
        except Exception as e:
            logger.error(f"SQLite Error with 'memory' or 'safe_place'  {e}")
            await VECTOR_SERVICE.delete_memory(str(metadata["id"]))
            raise


# info.category in ["belief", "pattern", "strengths", "goal"]:
async def handle_supposed_data(
    content: str, reasoning: str, metadata: dict, user_name: str, db: AsyncSession
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
        print(f"ACTIVE-RESULT: OLD:{doc.page_content} - score: {score} - NEW:{content}")
        if score <= 0.9:
            return
    await handle_hidden_search(
        content, reasoning, metadata, user_name, embedding, expiration_date, db
    )


async def handle_hidden_search(
    content: str,
    reasoning: str,
    metadata: dict,
    user_name: str,
    embedding: list[float],
    expiration_date: str,
    db: AsyncSession,
):
    hidden_result = await VECTOR_SERVICE.search_memory(
        metadata, embedding, status="hidden"
    )
    if hidden_result:
        doc, score = hidden_result[0]
        print(f"HIDDEN-RESULT: OLD:{doc.page_content} - score: {score} - NEW:{content}")
        if score <= 0.9:
            original_metadata = doc.metadata.copy()
            updated_metadata = update_metadata(doc, reasoning)
            existing_content = doc.page_content
            success = await VECTOR_SERVICE.update_memory(
                content, embedding, updated_metadata
            )
            if success:
                try:
                    await USER_PROPERTY_SERVICE.update_data(
                        db, content, updated_metadata
                    )
                    return
                except Exception as e:
                    logger.error(
                        f"SQLite Error within updating hidden memory items: {e}"
                    )
                    original_embedding = await VECTOR_SERVICE.create_embedding(
                        existing_content
                    )
                    await VECTOR_SERVICE.update_memory(
                        existing_content, original_embedding, original_metadata
                    )
                    raise
    new_metadata = create_new_metadata(metadata, reasoning)
    try:
        VECTOR_SERVICE.add_memory(content, embedding, new_metadata)
        metadata["expires_at"] = expiration_date
        await save_to_db(content, metadata, user_name, db)
    except Exception as e:
        logger.error(f"SQLite Error with hidden memory items: {e}")
        await VECTOR_SERVICE.delete_memory(str(metadata["id"]))
        raise


def create_new_metadata(metadata: dict, reasoning: str):
    metadata["status"] = "hidden"
    metadata["counter"] = 1
    metadata["reasoning"] = [reasoning]
    return metadata


def update_metadata(doc: Document, new_reasoning: str):
    updating_metadata = doc.metadata
    if updating_metadata["category"] in ["belief", "pattern"]:
        limit = 3
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


async def save_to_db(content: str, metadata: dict, user_name: str, db):
    final_content = content
    reasoning = metadata.get("reasoning")
    final_reasoning = []
    if user_name.strip():
        pattern = r"\b(der\s+|die\s+|den\s+|dem\s+|des\s+|das\s+)?(users|nutzers|user|nutzer)\b"
        final_content = re.sub(pattern, user_name, final_content, flags=re.IGNORECASE)
        if reasoning:
            for reason in reasoning:
                new_reason = re.sub(pattern, user_name, reason, flags=re.IGNORECASE)
                final_reasoning.append(new_reason)
        logger.info(f"User name was successfully replaced: {user_name}")
    else:
        logger.warning("No Username available. Content stays in original version.")
    user_property = UserProperty(
        id=metadata["id"],
        user_id=metadata["user_id"],
        category=metadata["category"],
        content=final_content,
        created_at=metadata["created_at"],
        expires_at=metadata.get("expires_at"),
        reasoning=final_reasoning,
        status=metadata["status"],
        counter=metadata.get("counter"),
    )

    await USER_PROPERTY_SERVICE.add_data(db, user_property)
    logger.info(f"Erfolgreich in SQLite gespeichert für User {metadata['user_id']}")
