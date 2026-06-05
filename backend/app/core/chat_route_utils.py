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


async def get_user_resources(db, current_user):
    result_safe_place = (
        await USER_PROPERTY_SERVICE.get_user_safe_place(db, current_user.id) or []
    )
    result_situation = (
        await USER_PROPERTY_SERVICE.get_user_situation(db, current_user.id) or []
    )
    user_safe_place = [result.content for result in result_safe_place]
    user_situation = [result.content for result in result_situation]
    situation_ids = [
        result.id for result in result_situation
    ]  # Das macht er nicht... warum auch immer!
    safe_place_id = [result.id for result in result_safe_place]

    user_data = {
        "nickname": current_user.nickname,
        "age": current_user.age,
        "gender": current_user.gender,
        "situation": user_situation,
        "safe_place": user_safe_place,
        "excluded_ids": situation_ids + safe_place_id,
    }
    return user_data
