from fastapi import HTTPException
from sqlalchemy import and_, delete, or_, select
from app.models.models import UserProperty, User
from sqlalchemy.exc import SQLAlchemyError
import logging
from app.services.vector_service import VECTOR_SERVICE
from app.core.onboarding_utils import save_safe_place, save_strengths, update_user

logger = logging.getLogger(__name__)


class UserService:
    async def register_user(self, db, new_user):
        db.add(new_user)
        try:
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except SQLAlchemyError as e:
            raise e

    async def login_user(self, db, user_mail):
        query = select(User).where(User.mail == user_mail)
        # hier wird jetzt wirklich gesucht
        result = await db.execute(query)
        # und jetzt die Ergebnisse bestimmt
        user = result.scalar_one_or_none()
        return user

    async def get_one_user(self, db, user_id):
        query = select(User).where(User.id == int(user_id))
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
            raise http_exc  # Fehlermeldung ans Frontend weitergeben

        except Exception as e:
            logger.exception(f"Unexpected system error during onboarding: {e}")
            for item in db.new:
                if isinstance(item, UserProperty):
                    await VECTOR_SERVICE.delete_memory(str(item.id))
            await db.rollback()
            raise HTTPException(  # Fehlermeldung an user
                status_code=400,
                detail="An unexpected database error occurred. Please try again.",
            )


# class UserPropertyService:
#     async def get_user_resources(self, db, user_id):
#         actual_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

#         query = select(UserProperty).where(
#             UserProperty.user_id == user_id,
#             or_(
#                 UserProperty.category == "safe_place",
#                 UserProperty.reasoning.contains("Onboarding"),
#                 and_(
#                     UserProperty.category == "current_situation",
#                     UserProperty.expires_at >= actual_date,
#                 )
#                 .order_by(UserProperty.created_at.desc())
#                 .limit(5),
#             ),
#         )
#         result = await db.execute(query)
#         elements = result.scalars().all()
#         user_situation = [
#             element.content
#             for element in elements
#             if element.category == "current_situation"
#         ]
#         user_safe_place = [
#             element.content for element in elements if element.category == "safe_place"
#         ]
#         return user_situation, user_safe_place

#     async def add_data(self, db, user_property: UserProfile):
#         db.add(user_property)
#         try:
#             await db.commit()
#         except SQLAlchemyError as e:
#             await db.rollback()
#             raise e

#     async def update_data(self, db, content, metadata):
#         data_to_update = await db.get(UserProperty, metadata.get("id"))
#         if not data_to_update:
#             return None

#         data_to_update.counter = metadata.get("counter")
#         data_to_update.content = content
#         data_to_update.reasoning = metadata.get("reasoning")
#         data_to_update.status = metadata.get("status")
#         if metadata.get("status") == "active":
#             data_to_update.expires_at = None
#         try:
#             await db.commit()
#         except SQLAlchemyError as e:
#             await db.rollback()
#             raise e

#     async def find_expired_data(self, user_id, db):
#         try:
#             actual_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
#             expired_data = select(UserProperty).where(
#                 and_(
#                     UserProperty.user_id == user_id,
#                     UserProperty.expires_at < actual_date,
#                     UserProperty.counter < 8,
#                 )
#             )
#             result = await db.execute(expired_data)
#             expired_data = result.scalars().all()
#             return expired_data
#         except Exception as e:
#             logger.error(
#                 f"Database Error: Failed to find expired data for user {user_id}: {e}",
#                 exc_info=True,
#             )
#             return []

#     async def delete_data_by_id(self, data_id, db):
#         data_to_delete = delete(UserProperty).where(UserProperty.id == data_id)
#         try:
#             await db.execute(data_to_delete)
#             await db.commit()
#             return True
#         except Exception as e:
#             await db.rollback()
#             logger.error(
#                 f"Database Error: Failed to delete property {data_id}: {e}, exc_info=True",
#                 exc_info=True,
#             )
#             return False


# USER_PROPERTY_SERVICE = UserPropertyService()
USER_SERVICE = UserService()
