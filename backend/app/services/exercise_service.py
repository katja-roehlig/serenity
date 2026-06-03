from sqlalchemy import select
from app.models.models import Exercise
from sqlalchemy.exc import SQLAlchemyError
from app.services.vector_service import VECTOR_SERVICE
from exceptions import VectorError
import logging

logger = logging.getLogger(__name__)


class ExerciseService:
    async def get_exercise_by_id(self, db, exercise_id):
        try:
            exercise = await db.get(Exercise, exercise_id)
            return exercise
        except SQLAlchemyError as e:
            logger.error(
                f"Database error while trying to get an exercise by id: {e}",
                exc_info=True,
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error while trying to get an exercise by id: {e}",
                exc_info=True,
            )
            return None

    async def add_exercise(self, db, exercise):
        db.add(exercise)
        try:
            await db.commit()
            await db.refresh(
                exercise
            )  # new exercise wird aktualisiert, mit id versehen und dann returnt
        except SQLAlchemyError as e:
            await db.rollback()
            raise e
        try:
            await VECTOR_SERVICE.put_exercise(
                exercise.goal, exercise.expertise, exercise.emotions, exercise.id
            )
            # print("Anzahl der Einträge: ", VECTOR_SERVICE.get_count())
            return exercise
        except VectorError as e:
            logger.error(f"Error adding to the vector database: {e}", exc_info=True)
            await self.delete_exercise(db, exercise.id)
            raise

    async def get_all_exercises(self, db):
        query = select(Exercise)
        try:
            result = await db.execute(query)
            exercises = result.scalars().all()
            return exercises
        except SQLAlchemyError as e:
            raise e

    async def delete_exercise(self, db, id):
        exercise_to_delete = await db.get(Exercise, id)
        if not exercise_to_delete:
            return None

        try:
            await VECTOR_SERVICE.delete_exercise(id)
        except VectorError as e:
            logger.error(
                f"Error deleting exercise from the vector database: {e}", exc_info=True
            )
            raise

        try:
            await db.delete(exercise_to_delete)
            await db.commit()
            return id
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error(f"Error deleting an exercise in SQL{e}", exc_info=True)
            raise e

    async def update_exercise(self, db, id, update_exercise):
        exercise_to_update = await db.get(Exercise, id)
        if not exercise_to_update:
            return None
        try:
            await VECTOR_SERVICE.put_exercise(
                update_exercise.goal,
                update_exercise.expertise,
                update_exercise.emotions,
                id,
            )
        except VectorError as e:
            logger.error(f"Error updating the vector database: {e}", exc_info=True)
            raise
        exercise_to_update.title = update_exercise.title
        exercise_to_update.goal = update_exercise.goal
        exercise_to_update.expertise = update_exercise.expertise
        exercise_to_update.emotions = update_exercise.emotions
        exercise_to_update.instructions = update_exercise.instructions
        exercise_to_update.media = update_exercise.media
        try:
            await db.commit()
            await db.refresh(exercise_to_update)
            return exercise_to_update
        except SQLAlchemyError as e:
            await db.rollback()
            raise e


EXERCISE_SERVICE = ExerciseService()
