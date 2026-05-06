from sqlalchemy import select
from app.models.models import Exercise
from sqlalchemy.exc import SQLAlchemyError
from app.services.vector_service import VECTOR_SERVICE
from exceptions import VectorError


class ExerciseService:
    async def get_exercise_by_id(self, db, exercise_id):
        try:
            exercise = await db.get(Exercise, exercise_id)
            return exercise
        except SQLAlchemyError as e:
            print(f"Database error: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None

    async def add_exercise(self, db, exercise):
        db.add(exercise)
        try:
            await db.commit()  # new_exercise wird in die db geschrieben
            await db.refresh(
                exercise
            )  # new exercise wird aktualisiert, mit id versehen und dann returnt
        except SQLAlchemyError as e:
            await db.rollback()
            raise e
        try:
            await VECTOR_SERVICE.put_exercise(
                exercise.title, exercise.content, exercise.id
            )  # der Vektor_service wird aufgerufen, um direkt die Übung in ChromaDB zu überführen.
            print("Anzahl der Einträge: ", VECTOR_SERVICE.get_count())
            return exercise
        except VectorError:
            print("Error adding to the vector database")
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
            print("Anzahl der Einträge: ", VECTOR_SERVICE.get_count())
        except VectorError:
            print("Error deleting from the vector database")
            raise

        try:
            await db.delete(exercise_to_delete)
            await db.commit()
            return id
        except SQLAlchemyError as e:
            await db.rollback()
            print("Error deleting in SQL")
            raise e

    async def update_exercise(self, db, id, update_exercise):
        exercise_to_update = await db.get(Exercise, id)
        if not exercise_to_update:
            return None
        try:
            await VECTOR_SERVICE.put_exercise(
                update_exercise.title, update_exercise.content, id
            )
            print("Anzahl der Einträge: ", VECTOR_SERVICE.get_count())
        except VectorError:
            print("Error updating the vector database")
            raise
        exercise_to_update.title = update_exercise.title
        exercise_to_update.content = update_exercise.content
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
