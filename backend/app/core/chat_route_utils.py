from app.ai.archivist_agent import ArchivistState, create_archivist_agent
from app.models.models import User
from app.services.user_property_service import USER_PROPERTY_SERVICE
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import RemoveMessage
import logging

logger = logging.getLogger(__name__)


# config: RunnableConfig
async def activate_archivist_agent(
    db: AsyncSession,
    current_user: User,
    total_messages: list,
):
    """Activate the archivist agent with the current user's messages.

    Args:
        db (AsyncSession): The asynchronous database session.
        current_user (User): The user whose messages are being processed.
        total_messages (list): The list of messages to send to the archivist agent.

    Returns:
        bool: True when the archivist agent completes successfully.

    Raises:
        Exception: Re-raises any exception encountered during agent execution.
    """
    logger.info(f"--- ARCHIVIST TRIGGERED --- Message count: {len(total_messages)}")
    try:
        archivist_agent = create_archivist_agent(db)
        archivist_input: ArchivistState = {
            "messages": total_messages,
            "user_id": str(current_user.id),
            "user_name": str(current_user.nickname),
            "found_items": [],
        }
        await archivist_agent.ainvoke(archivist_input)
        logger.info("--- ARCHIVIST FINISHED SUCCESSFULLY ---")
        return True
    except Exception as e:
        logger.error(f"Archivist error in background execution: {e}", exc_info=True)
        raise


async def get_user_resources(db, current_user) -> dict:
    """Retrieve and format user resource information.
    Args:
        db (AsyncSession): The asynchronous database session.
        current_user (User): The current user whose resources are retrieved.

    Returns:
        dict: A dictionary containing user metadata, situation and safe place lists,
            and excluded resource ids.
    """
    result_safe_place = await USER_PROPERTY_SERVICE.get_user_safe_place(
        db, current_user.id
    )
    print(f"SAFEPLACE: {result_safe_place}")
    result_situation = await USER_PROPERTY_SERVICE.get_user_situation(
        db, current_user.id
    )
    print(f"SITUATION: {result_situation}")
    user_safe_place = [result.content for result in result_safe_place]
    user_situation = [result.content for result in result_situation]
    situation_ids = [result.id for result in result_situation]
    safe_place_id = [result.id for result in result_safe_place]

    user_data = {
        "nickname": current_user.nickname,
        "age": current_user.age,
        "gender": current_user.gender,
        "situation": user_situation,
        "safe_place": user_safe_place,
        "excluded_ids": situation_ids + safe_place_id,
    }
    print(f"USERDATA: {user_data}")
    return user_data
