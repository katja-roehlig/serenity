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
    """Service class for user-related database operations.
    Methods provided include registration, login lookup, fetching a user,
    saving onboarding data, and deleting a user.
    """

    async def register_user(self, db, new_user):
        """Register a new user in the database.
        Args:
            db (AsyncSession): The asynchronous database session to use.
            new_user (User): The User model instance to add to the DB.
        Returns:
            User: The newly created and refreshed User instance.
        Raises:
            SQLAlchemyError: If a database error occurs during add/commit/refresh.
        """
        try:
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except SQLAlchemyError as e:
            await db.rollback()
            raise e

    async def login_user(self, db, user_mail):
        """Retrieve a user by email for login purposes.
        Args:
            db (AsyncSession): The asynchronous database session to use.
            user_mail (str): The email address of the user to find.
        Returns:
            User | None: The matching User instance or None if not found.
        """
        query = select(User).where(User.mail == user_mail)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        return user

    async def get_one_user(self, db, user_id: str):
        """Fetch a single user by their ID.
        Args:
            db (AsyncSession): The asynchronous database session to use.
            user_id (str): The ID of the user to retrieve.
        Returns:
            User | None: The User instance if found, otherwise None.
        """
        query = select(User).where(User.id == str(user_id))
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        return user

    async def save_onboarding_data(self, db, onboarding_data, user):
        """Save onboarding data for a user, invoking helper utilities.
        Args:
            db (AsyncSession): The asynchronous database session to use.
            onboarding_data (dict): The onboarding payload containing data to save.
            user (User): The user model instance to update.
        Returns:
            dict: A dictionary with a success message and status on success.
        Raises:
        HTTPException: Propagates HTTPExceptions or generic errors wrapped as 400.
        """
        saved_vector_ids = []
        try:
            await save_strengths(db, onboarding_data, user)
            await save_safe_place(db, onboarding_data, user)
            await update_user(db, onboarding_data, user)
            await db.commit()
            return {
                "message": "Onboarding successfully completed!",
                "status": "success",
            }
        except Exception as e:
            items_to_clean = list(db.new)
            await db.rollback()

            for item in items_to_clean:
                if isinstance(item, UserProperty):
                    logger.warning(
                        f"Onboarding error: Deleting vector memory for ID {item.id}."
                    )
                try:
                    await VECTOR_SERVICE.delete_memory(str(item.id))
                except Exception as v_err:
                    logger.critical(f"Failed to delete vector ID {item.id}: {v_err}")

            if isinstance(e, HTTPException):
                raise e
            else:
                logger.exception(f"Unexpected system error during onboarding: {e}")
                raise HTTPException(
                    status_code=400,
                    detail="Ein unerwarteter Datenbankfehler ist aufgetreten. Bitte versuche es noch einmal.",
                )

    async def delete_user(self, db: AsyncSession, user_id):
        """Delete a user and their properties from the database.
        Args:
            db (AsyncSession): The asynchronous database session to use.
            user_id (str): The ID of the user to delete.
        Returns:
            bool: True if deletion succeeded.
        Raises:
            Exception: Re-raises any exception encountered after rollback.
        """

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
