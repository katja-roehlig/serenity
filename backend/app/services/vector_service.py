import asyncio
from typing import List, Union
import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv
import logging
from langchain_core.utils.utils import convert_to_secret_str
from langchain_core.runnables.config import run_in_executor
import asyncio

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise RuntimeError("Attention: OPENAI_API_KEY was not found in .env file!")

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(
        self,
    ):
        """Initialize the VectorService with Chroma client and embeddings.
        Sets up the persistent Chroma client, OpenAI embeddings model, and two
        vector stores: one for exercises and one for user memory.
        Raises:
            RuntimeError: If OPENAI_API_KEY is not set in environment variables.
        """
        self.client = chromadb.PersistentClient(os.path.join("data", "chroma_db"))
        self.embeddings = OpenAIEmbeddings(
            api_key=convert_to_secret_str(OPENAI_API_KEY),
            model="text-embedding-3-small",
        )
        self.vector_store = Chroma(
            client=self.client,
            embedding_function=self.embeddings,
            collection_name="exercises_collection",
        )
        self.memory_store = Chroma(
            client=self.client,
            embedding_function=self.embeddings,
            collection_name="user_memory",
        )

    async def put_exercise(self, goal, expertise, emotions, exercise_id):
        """Add an exercise to the vector store.
        Args:
            goal: The goal associated with the exercise.
            expertise: The expertise level required for the exercise.
            emotions: The emotions targeted by the exercise.
            exercise_id: Unique identifier for the exercise.
        Returns:
            None
        """
        full_text = f"Goal: {goal}, Expertise: {expertise}, Emotions: {emotions}"
        await self.vector_store.aadd_texts(
            texts=[full_text], metadatas=[{"id": exercise_id}], ids=[str(exercise_id)]
        )

    async def delete_exercise(self, exercise_id):
        """Delete an exercise from the vector store.
        Args:
            exercise_id: Unique identifier of the exercise to delete.
        Returns:
            None
        """
        await self.vector_store.adelete(ids=[str(exercise_id)])

    def get_count(self):
        """Get the count of exercises in the vector store.
        Returns:
            int: The number of exercises stored in the collection.
        """
        return self.vector_store._collection.count()

    async def search_exercise(self, query: str, k: int = 1):
        """Search for exercises matching the query.

        Performs a similarity search and returns the best matching exercise ID
        if the similarity score is below the threshold.
        Args:
            query (str): The search query string.
            k (int): Number of top results to retrieve. Defaults to 1.
        Returns:
            str or None: The exercise ID of the best match, or None if no suitable
                exercise is found or the similarity score is too high (> 0.85).
        """
        result = await self.vector_store.asimilarity_search_with_score(query, k=k)
        if not result:
            return None
        text, score = result[0]
        print(f"VEKTORSUCHE - ÜBUNG: {text.metadata.get('id')}: Score: {score}")
        if score > 0.85:
            logger.info(f"Score too high for a suitable exercise : {score}")
            return None
        exercise_id = text.metadata.get("id")
        return exercise_id

        # def get_retriever(self):
        """Get a retriever tool for the agent to search exercises.
        Creates a LangChain retriever configured to return the single best
        matching result from the vector store.
        Returns:
            Retriever: A LangChain retriever object for exercise similarity search.
        """
        # Wir erstellen ein Werkzeug, das die Suche für den Agenten übernimmt.
        # Er ist quasi unserer Assistent und spezialist für chroma.
        # search_kwargs={"k": 1} bedeutet: Er soll immer nur das beste Ergebnis finden.
        # return self.vector_store.as_retriever(search_kwargs={"k": 1})

    # Methoden für den memory_store ab hier
    async def create_embedding(self, content):
        """Create an embedding for the given content.
        Args:
            content: The text content to embed.
        Returns:
            list[float]: The embedding vector.
        """
        embedding = await self.embeddings.aembed_query(content)
        return embedding

    def add_memory(
        self,
        content: str,
        embedding: list[float],
        metadata: dict,
    ):
        """Add user memory to the memory store.
        Attempts to add memory with retry logic (2 attempts total).
        Args:
            content (str): The memory content to store.
            embedding (list[float]): The embedding vector for the content.
            metadata (dict): Metadata dictionary containing at least an 'id' key.
        Returns:
            bool: True if the memory was successfully added.
        Raises:
            RuntimeError: If the add operation fails after 2 attempts.
        """
        for attempt in range(2):
            try:
                self.memory_store._collection.add(
                    documents=[content],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[metadata["id"]],
                )
                logger.info("User data successfully added")
                return True
            except Exception as e:
                logger.warning(f"Memory Store Error: Failed to add data two times")
                if (
                    attempt == 1
                ):  # Beim zweiten Fehlschlag (Index 1) werfen wir das Handtuch!
                    raise RuntimeError(
                        "ChromaDB add_memory failed after 2 attempts"
                    ) from e

    async def search_memory(self, metadata: dict, embedding: list[float], status: str):
        """Search user memories based on metadata and embedding similarity.
        Args:
            metadata (dict): Metadata dictionary containing 'user_id' and 'category'.
            embedding (list[float]): The embedding vector to search with.
            status (str): The status filter for memories (e.g., 'active').
        Returns:
            list: Search results with relevance scores.
        Raises:
            Exception: If the similarity search fails.
        """
        search_filter = {
            "$and": [
                {"user_id": {"$eq": str(metadata["user_id"])}},
                {"category": {"$eq": str(metadata["category"])}},
                {"status": {"$eq": str(status)}},
            ]
        }
        try:
            result = await run_in_executor(
                None,
                self.memory_store.similarity_search_by_vector_with_relevance_scores,
                embedding=embedding,
                k=1,
                filter=search_filter,  # type: ignore
            )
            return result
        except Exception as e:
            logger.exception("Memory Store Error: Failed do similarity search")
            raise

    async def delete_memory(self, ids: Union[str, List[str]]):
        """Delete memories from the memory store.
        Deletes one or more memories by ID. Handles cases where memories
        were already deleted gracefully.
        Args:
            ids (Union[str, List[str]]): A single ID string or list of ID strings to delete.
        Returns:
            bool: True if deletion was successful or the IDs were already deleted,
                False otherwise.
        """
        if isinstance(ids, str):
            ids_to_delete = [ids]
        else:
            ids_to_delete = ids
        try:
            await self.memory_store.adelete(ids=ids_to_delete)
            logger.info(
                f"User Data successfully deleted from VectorDB: {ids_to_delete}"
            )
            return True

        except Exception as e:
            error_msg = str(e).lower()
            # falls memory_id schon gelöscht wurde, muss es weiterlaufen, um sql zu löschen!
            if (
                "not found" in error_msg
                or "does not exist" in error_msg
                or "id not present" in error_msg
            ):
                logger.info(f"VectorDB: {ids_to_delete} was alreadyy deleted")
                return True
            logger.error(
                f"Memory Store Error: Failed to delete {ids_to_delete} from VectorDB. Error: {e}",
                exc_info=True,
            )
        return False

    async def update_memory(self, content, embedding, metadata):
        """Update a memory in the memory store.
        Deletes the old memory and adds the new one with updated content.
        Args:
            content: The updated memory content.
            embedding: The new embedding vector.
            metadata (dict): Updated metadata containing the memory 'id'.
        Returns:
            bool: True if the update was successful.
        Raises:
            RuntimeError: If the old memory could not be deleted.
        """
        success = await self.delete_memory(metadata["id"])
        if not success:
            logger.error(
                f"Critical: Update failed because old vector could not be deleted from db"
            )
            raise RuntimeError("VectorDB deletion failed during update process")
        return self.add_memory(content, embedding, metadata)

    async def get_user_memories_for_serenity(self, user_id: str, text: str):
        """Retrieve active user memories matching the search text.
        Args:
            user_id (str): The user's ID to filter memories.
            text (str): The search query text.
        Returns:
            list: A list of matching memories with relevance scores, or empty list if none found.
        """
        search_filter = {"$and": [{"user_id": user_id}, {"status": "active"}]}
        result = await self.memory_store.asimilarity_search_with_score(
            query=text, k=10, filter=search_filter
        )
        return result if result else []

    async def delete_all_by_user_id(self, user_id: str):
        """Delete all memories for a specific user.
        Args:
            user_id (str): The user's ID whose memories should be deleted.
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            # LangChain erlaubt das Filtern über das 'where'-Dictionary in den Metadaten
            await self.memory_store.adelete(where={"user_id": user_id})
            return True
        except Exception as e:
            logger.error(f"Fehler beim Löschen der user_id {user_id} aus Chroma: {e}")
            return False


VECTOR_SERVICE = VectorService()
