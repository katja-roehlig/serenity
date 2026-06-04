from datetime import datetime, timezone
from xml.dom import UserDataHandler

from sqlalchemy import and_, delete, or_, select

from app.models.models import UserProperty
from app.schemas.api_schemas import UserProfile
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class UserPropertyService:

    async def get_user_safe_place(self, db, user_id):
        query = select(UserProperty).where(
            UserProperty.user_id == user_id,
            UserProperty.category == "safe_place",
            UserProperty.reasoning.contains("Onboarding"),
        )
        try:
            result = await db.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:  # allgemeine Aussage, da kein Einfluss auf Runtime
            logger.error(
                f"Database Error: Failed to find safe_place for user {user_id}: {e}",
                exc_info=True,
            )
            return []

    async def get_user_situation(self, db, user_id):
        actual_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query = (
            select(UserProperty)
            .where(
                UserProperty.user_id == user_id,
                UserProperty.category == "current_stiuation",
                UserProperty.expires_at >= actual_date,
            )
            .order_by(UserProperty.created_at.desc())
            .limit(5)
        )
        try:
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:  # allgemeine Aussage, da kein Einfluss auf Runtime
            logger.error(
                f"Database Error: Failed to find current_situations for user {user_id}: {e}",
                exc_info=True,
            )
            return []

    async def get_all_active_user_data(self, db, user_id):
        query = (
            select(UserProperty).where(
                UserProperty.user_id == user_id, UserProperty.status == "active"
            )
        ).order_by(UserProperty.category)
        try:
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(
                f"Database connection error for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def get_all_user_data(self, db, user_id):
        query = select(UserProperty).where(UserProperty.user_id == user_id)
        try:
            result = await db.execute(query)
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(
                f"Database connection error for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def add_data(self, db, user_property: UserProfile):
        db.add(user_property)
        try:
            await db.commit()
        except SQLAlchemyError:
            await db.rollback()
            raise

    async def update_data(self, db, content, metadata):
        data_to_update = await db.get(UserProperty, metadata.get("id"))
        if not data_to_update:
            return None

        data_to_update.counter = metadata.get("counter")
        data_to_update.content = content
        data_to_update.reasoning = metadata.get("reasoning")
        data_to_update.status = metadata.get("status")
        if metadata.get("status") == "active":
            data_to_update.expires_at = None
        try:
            await db.commit()
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def find_expired_data(self, user_id, db):
        try:
            actual_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            expired_data = select(UserProperty).where(
                and_(
                    UserProperty.user_id == user_id,
                    UserProperty.expires_at < actual_date,
                    UserProperty.counter < 8,
                )
            )
            result = await db.execute(expired_data)
            expired_data = result.scalars().all()
            return expired_data
        except Exception as e:
            logger.error(
                f"Database Error: Failed to find expired data for user {user_id}: {e}",
                exc_info=True,
            )
            return []

    async def delete_data_by_id(self, data_id, db, raise_on_error: bool = False):
        data_to_delete = delete(UserProperty).where(UserProperty.id == data_id)
        try:
            await db.execute(data_to_delete)
            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            logger.error(
                f"Database Error: Failed to delete property {data_id}: {e}, exc_info=True",
                exc_info=True,
            )
            if raise_on_error:  # in der dashboard route muss user informiert werden
                raise
            return False  # wenn der archivist_agent arbeitet, soll keine info zum user gehen!

    async def find_data_by_user_and_id(self, user_id, data_id, db):
        query = select(UserProperty).where(
            UserProperty.user_id == user_id, UserProperty.id == data_id
        )
        try:
            result = await db.execute(query)
            data = result.scalar_one_or_none()
            return data
        except SQLAlchemyError as e:
            logger.error(
                f"Database error by checking user_id {user_id} an data_id {data_id}",
                exc_info=True,
            )
            raise e


USER_PROPERTY_SERVICE = UserPropertyService()
