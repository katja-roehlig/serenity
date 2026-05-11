import chromadb
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")


class VectorService:
    def __init__(
        self,
    ):  # client, embeddings, vector_store hier nicht in den argumenten, weil sie konstant sind

        self.client = chromadb.PersistentClient(os.path.join("data", "chroma_db"))
        self.embeddings = OpenAIEmbeddings(
            api_key=API_KEY, model="text-embedding-3-small"
        )
        self.vector_store = Chroma(
            client=self.client,
            embedding_function=self.embeddings,
            collection_name="exercises_collection",
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
        result = await self.vector_store.asimilarity_search(query, k=k)
        if not result:
            return None
        print("Ergebnis Vektorsuche: ", result)
        exercise_id = result[0].metadata.get("id")
        return exercise_id

    def get_retriever(self):
        # Wir erstellen ein Werkzeug, das die Suche für den Agenten übernimmt.
        # Er ist quasi unserer Assistent und spezialist für chroma.
        # search_kwargs={"k": 1} bedeutet: Er soll immer nur das beste Ergebnis finden.
        return self.vector_store.as_retriever(search_kwargs={"k": 1})


VECTOR_SERVICE = VectorService()
