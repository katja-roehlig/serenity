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
    ):  # client, embeddings, vector_store hier nicht in den argumenten, weil sie konstant sind

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
        full_text = f"Goal: {goal}, Expertise: {expertise}, Emotions: {emotions}"
        await self.vector_store.aadd_texts(
            texts=[full_text], metadatas=[{"id": exercise_id}], ids=[str(exercise_id)]
        )

    async def delete_exercise(self, exercise_id):
        await self.vector_store.adelete(ids=[str(exercise_id)])

    def get_count(self):
        # Schaut wieviele Einträge in der db liegen
        return self.vector_store._collection.count()

    async def search_exercise(self, query: str, k: int = 1):
        result = await self.vector_store.asimilarity_search_with_score(query, k=k)
        if not result:
            return None
        text, score = result[0]
        print(f"VEKTORSUCHE - ÜBUNG: {text.metadata.get('id')}: Score: {score}")
        if score > 0.8:
            print(f"Score zu hoch: {score}")
            return None
        exercise_id = text.metadata.get("id")
        return exercise_id

    def get_retriever(self):
        # Wir erstellen ein Werkzeug, das die Suche für den Agenten übernimmt.
        # Er ist quasi unserer Assistent und spezialist für chroma.
        # search_kwargs={"k": 1} bedeutet: Er soll immer nur das beste Ergebnis finden.
        return self.vector_store.as_retriever(search_kwargs={"k": 1})

    # Methoden für den memory_store ab hier
    async def create_embedding(self, content):
        embedding = await self.embeddings.aembed_query(content)
        return embedding

    def add_memory(
        self,
        content: str,
        embedding: list[float],
        metadata: dict,
    ):
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
                logger.exception(f"Memory Store Error: Failed to add data")
        return False

    async def search_memory(self, metadata: dict, embedding: list[float], status: str):
        search_filter = {
            "user_id": metadata["user_id"],
            "category": metadata["category"],
            "status": status,
        }
        try:
            result = await run_in_executor(
                None,
                self.memory_store.similarity_search_by_vector_with_relevance_scores,
                embedding=embedding,
                k=1,
                filter=search_filter,
            )
            return result
        except Exception as e:
            logger.exception("Memory Store Error: Failed do similarity search")
        return False

    async def delete_memory(self, ids: Union[str, List[str]]):
        if isinstance(ids, str):
            ids_to_delete = [ids]
        else:
            ids_to_delete = ids
        try:
            await self.memory_store.adelete(ids=ids_to_delete)
            logger.info("User Data successfully deleted from VectorDB: {memory_id}")
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
        success = await self.delete_memory(metadata["id"])
        if success:
            return self.add_memory(content, embedding, metadata)
        return False

    async def get_user_memories_for_serenity(self, user_id: str, text: str):
        search_filter = {"$and": [{"user_id": user_id}, {"status": "active"}]}
        result = await self.memory_store.asimilarity_search_with_score(
            query=text, k=10, filter=search_filter
        )
        return result if result else []

    async def get_memories_to_develop(
        self, user_id
    ):  # nur zur Überprüfung, was gespeichert ist in der developer-route
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None, lambda: self.memory_store.get(where={"user_id": user_id})
        )
        return results

    async def delete_all_user_memories(self, user_id: int):
        import asyncio

        loop = asyncio.get_running_loop()

        # LangChain Chroma erlaubt es, über 'where' gezielt nach Metadaten zu löschen
        await loop.run_in_executor(
            None, lambda: self.memory_store.delete(where={"user_id": user_id})
        )


VECTOR_SERVICE = VectorService()
