from app.ai.archivist_agent import ArchivistState, create_archivist_agent
from app.models.models import User
from app.services.user_property_service import USER_PROPERTY_SERVICE
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import RemoveMessage
import logging

logger = logging.getLogger(__name__)


async def activate_archivist_agent(
    db: AsyncSession, current_user: User, total_messages: list
):
    logger.info(f"--- ARCHIVIST TRIGGERED --- Message count: {len(total_messages)}")
    try:
        archivist_agent = create_archivist_agent(db)
        archivist_input: ArchivistState = {
            "messages": total_messages,
            "user_id": str(current_user.id),
            "found_items": [],
        }
        await archivist_agent.ainvoke(archivist_input)
        logger.info("--- ARCHIVIST FINISHED SUCCESSFULLY ---")
        return True
    except Exception as e:
        logger.error(f"Archivist error in background execution: {e}", exc_info=True)


async def trim_chat_history(
    serenity_core_agent, config: RunnableConfig, old_messages: list
):
    overlap = 3
    remove_messages = [
        RemoveMessage(id=message.id) for message in old_messages[:-overlap]
    ]
    state_update = {"messages": remove_messages}
    try:
        await serenity_core_agent.aupdate_state(config, state_update)
        logger.info(f"Successfully trimmed deleted chat_history.")
    except Exception as e:
        logger.error(f"Failed to trim chat history: {e}", exc_info=True)


async def get_user_resources(db, current_user):
    user_safe_place = await USER_PROPERTY_SERVICE.get_user_safe_place(
        db, current_user.id
    )
    user_situation = await USER_PROPERTY_SERVICE.get_user_situation(db, current_user.id)
    user_data = {
        "nickname": current_user.nickname,
        "age": current_user.age,
        "gender": current_user.gender,
        "situation": user_situation,
        "safe_place": user_safe_place,
    }
    return user_data
