from datetime import datetime, timezone
from xml.dom import UserDataHandler

from sqlalchemy import and_, delete, or_, select

from app.models.models import UserProperty
from app.schemas.api_schemas import UserProfile
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class UserPropertyService:
    """Service for managing UserProperty records.

    Provides methods to query, add, update and delete user properties in the
    database. All methods are asynchronous and expect an async database
    session/connection object as used in the application.
    """

    async def get_user_safe_place(self, db, user_id):
        """Retrieve safe place properties for a user.

        Args:
            db: Async database session/connection supporting execute().
            user_id (int | str): Identifier of the user to search for.

        Returns:
            list[UserProperty]: List of UserProperty objects with category == 'safe_place'.

        Raises:
            None: Returns empty list on SQLAlchemyError.
        """
        query = select(UserProperty).where(
            UserProperty.user_id == user_id,
            UserProperty.category == "safe_place",
        )
        try:
            result = await db.execute(query)
            safe_place = list(result.scalars().all())
            print(f"SAFE PLACE: {safe_place}")
            return safe_place
        except SQLAlchemyError as e:
            logger.error(
                f"Database Error: Failed to find safe_place for user {user_id}: {e}",
                exc_info=True,
            )
            return []

    async def get_user_situation(self, db, user_id):
        """Retrieve current situation properties for a user with non-expired records.
        Args:
            db: Async database session/connection supporting execute().
            user_id (int | str): Identifier of the user to search for.
        Returns:
            list[UserProperty]: List of UserProperty objects with category == 'current_situation'.
        Raises:
            None: Returns empty list on SQLAlchemyError.
        """

        actual_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        query = (
            select(UserProperty)
            .where(
                UserProperty.user_id == user_id,
                UserProperty.category == "current_situation",
                UserProperty.expires_at >= actual_date,
            )
            .order_by(UserProperty.created_at.desc())
            .limit(5)
        )
        try:
            result = await db.execute(query)
            situations = result.scalars().all()
            return situations
        except SQLAlchemyError as e:
            logger.error(
                f"Database Error: Failed to find current_situations for user {user_id}: {e}",
                exc_info=True,
            )
            return []

    async def get_all_active_user_data(self, db, user_id):
        """Retrieve all active properties for a user to show in the dashboard.
        Args:
            db: Async database session/connection supporting execute().
            user_id (int | str): Identifier of the user to search for.
        Returns:
            list[UserProperty]: List of UserProperty objects with status == 'active'.
        Raises:
            SQLAlchemyError: Propagates database connection related errors after logging.
        """
        query = (
            select(UserProperty).where(
                UserProperty.user_id == user_id, UserProperty.status == "active"
            )
        ).order_by(UserProperty.category)
        try:
            result = await db.execute(query)
            active_user_data = result.scalars().all()
            return active_user_data
        except SQLAlchemyError as e:
            logger.error(
                f"Database connection error for user {user_id}: {e}",
                exc_info=True,
            )
            raise

    async def get_all_user_data(self, db, user_id):
        """Retrieve all properties for a user.
        Args:
            db: Async database session/connection supporting execute().
            user_id (int | str): Identifier of the user to search for.
        Returns:
            list[UserProperty]: List of all UserProperty objects for the user.
        Raises:
            SQLAlchemyError: If a database execution error occurs.
        """
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
        """Add a new UserProperty record to the database.
        Args:
            db: Async database session/connection supporting add() and commit().
            user_property (UserProfile): UserProfile object to add.
        Raises:
            Exception: If commit fails after rollback.
        """
        db.add(user_property)
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Database or processing error: Failed to commit new user property: {e}",
                exc_info=True,
            )
            raise

    async def update_data(self, db, content, metadata):
        """Update an existing UserProperty record.
        Args:
            db: Async database session/connection supporting get() and commit().
            content (str): New content for the property.
            metadata (dict): Metadata containing fields to update, including 'id'.
        Raises:
            Exception: If update or commit fails after rollback.
        """
        try:
            # Data-Object aus DB laden
            data_to_update = await db.get(UserProperty, metadata.get("id"))
            if not data_to_update:
                return None
            # Felder updaten
            data_to_update.counter = metadata.get("counter")
            data_to_update.content = content
            data_to_update.reasoning = metadata.get("reasoning")
            data_to_update.status = metadata.get("status")
            if metadata.get("status") == "active":
                data_to_update.expires_at = None
            # Änderungen schreiben
            await db.commit()
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Database or processing Error: Failed to update UserProperty with ID {metadata.get('id')}: {e}",
                exc_info=True,
            )
            raise e

    async def find_expired_data(self, user_id, db):
        """Find expired UserProperty records for a user.
        Args:
            user_id (int | str): Identifier of the user who owns the properties.
            db: Async database session/connection supporting execute().
        Returns:
            list[UserProperty]: List of expired UserProperty objects.
        Raises:
            None: Returns empty list on error.
        """
        try:
            actual_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            expired_data = select(UserProperty).where(
                and_(
                    UserProperty.user_id == user_id,
                    UserProperty.expires_at < actual_date,
                    or_(UserProperty.counter < 8, UserProperty.counter == None),
                )
            )
            result = await db.execute(expired_data)
            expired_data = result.scalars().all()
            return expired_data
        except Exception as e:
            logger.error(
                f"Database or Processing error: Failed to find expired data for user {user_id}: {e}",
                exc_info=True,
            )
            return []

    async def delete_data_by_id(self, data_id, db, raise_on_error: bool = False):
        """Delete a UserProperty by its id.
        Args:
            data_id (int | str): Identifier of the UserProperty to delete.
            db: Async database session/connection supporting execute() and commit().
            raise_on_error (bool): If True, re-raises exceptions after rollback and logging; otherwise returns False on error.
        Returns:
            bool: True if deletion and commit succeeded, False on error when raise_on_error is False.
        Raises:
            Exception: Propagates exceptions if raise_on_error is True.
        """
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
        """Find a UserProperty by user_id and data_id.
        Args:
            user_id (int | str): Identifier of the user who owns the property.
            data_id (int | str): Identifier of the property to retrieve.
            db: Async database session/connection supporting execute().
        Returns:
            UserProperty | None: The matching UserProperty or None if not found.
        Raises:
            SQLAlchemyError: Propagates database errors after logging.
        """
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
