from fastapi import HTTPException
from sqlalchemy import and_, delete, or_, select
from app.models.models import User, UserProperty
from sqlalchemy.exc import SQLAlchemyError
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_service import VECTOR_SERVICE
from app.core.onboarding_utils import save_safe_place, save_strengths, update_user

logger = logging.getLogger(__name__)


class UserService:
    async def register_user(self, db, new_user):

        try:
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def login_user(self, db, user_mail):
        query = select(User).where(User.mail == user_mail)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        return user

    async def get_one_user(self, db, user_id: str):
        query = select(User).where(User.id == str(user_id))
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        return user

    async def save_onboarding_data(self, db, onboarding_data, user):
        try:
            await save_strengths(db, onboarding_data, user)
            await save_safe_place(db, onboarding_data, user)
            await update_user(db, onboarding_data, user)
            await db.commit()
            return {
                "message": "Onboarding successfully completed!",
                "status": "success",
            }
        except HTTPException as http_exc:
            for item in db.new:
                if isinstance(item, UserProperty):
                    logger.warning(
                        f"Onboarding error: Deleting vector memory for ID {item.id}."
                    )
                    await VECTOR_SERVICE.delete_memory(str(item.id))
            await db.rollback()
            raise http_exc  # Fehlermeldung ans Frontend

        except Exception as e:
            logger.exception(f"Unexpected system error during onboarding: {e}")
            for item in db.new:
                if isinstance(item, UserProperty):
                    await VECTOR_SERVICE.delete_memory(str(item.id))
            await db.rollback()
            raise HTTPException(  # Fehlermeldung ans Frontend
                status_code=400,
                detail="An unexpected database error occurred. Please try again.",
            )

    async def delete_user(self, db: AsyncSession, user_id):

        try:
            await db.execute(
                delete(UserProperty).where(UserProperty.user_id == user_id)
            )
            await db.execute(delete(User).where(User.id == user_id))
            await db.commit()
            return True
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Failed ti delete user from sql {user_id}: {e}", exc_info=True
            )
            raise e


USER_SERVICE = UserService()
