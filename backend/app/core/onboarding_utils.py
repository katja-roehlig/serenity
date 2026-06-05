from datetime import datetime, timezone
import logging
import uuid

from fastapi import HTTPException
from sqlalchemy import select

from app.models.models import User, UserProperty
from app.services.vector_service import VECTOR_SERVICE

logger = logging.getLogger(__name__)


async def update_user(db, onboarding_data, user):
    query = select(User).where(User.id == str(user.id))
    result = await db.execute(query)
    update_user = result.scalar_one_or_none()
    if not update_user:
        raise HTTPException(status_code=404, detail="User not found")
    update_user.age = onboarding_data.age
    update_user.gender = onboarding_data.gender
    update_user.has_onboarding = True


async def save_strengths(db, onboarding_data, user):
    for item in onboarding_data.strengths:
        item_id = str(uuid.uuid4())
        actual_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        reasoning = ["Onboarding"]
        metadata = {
            "id": item_id,
            "user_id": user.id,
            "category": "strengths",
            "created_at": actual_date,
            "status": "active",
            "reasoning": reasoning,
        }
        embedding = await VECTOR_SERVICE.create_embedding(item)
        success = VECTOR_SERVICE.add_memory(
            content=item, embedding=embedding, metadata=metadata
        )
        if not success:
            logger.error(
                f"VectorDB Error: Failed to save strength '{item}' for user_id {user.id}"
            )
            raise HTTPException(
                status_code=400,
                detail="The strengths could not be saved. Please try again",
            )
        user_strength = UserProperty(
            id=item_id,
            user_id=user.id,
            category="strengths",
            content=item,
            created_at=actual_date,
            reasoning=reasoning,
        )
        db.add(user_strength)


async def save_safe_place(db, onboarding_data, user):
    safe_place_id = str(uuid.uuid4())
    actual_date: str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    metadata = {
        "id": safe_place_id,
        "user_id": user.id,
        "category": "safe_place",
        "created_at": actual_date,
        "status": "active",
    }
    embedding = await VECTOR_SERVICE.create_embedding(onboarding_data.safe_place)
    success = VECTOR_SERVICE.add_memory(
        content=onboarding_data.safe_place, embedding=embedding, metadata=metadata
    )
    if not success:
        logger.error(
            f"VectorDB Error: Failed to save safe_place '{onboarding_data.safe_place}' for user_id {user.id}"
        )
        raise HTTPException(
            status_code=400,
            detail="The strengths could not be saved. Please try again",
        )
    user_place = UserProperty(
        id=safe_place_id,
        user_id=user.id,
        category="safe_place",
        content=onboarding_data.safe_place,
        created_at=actual_date,
    )
    db.add(user_place)
