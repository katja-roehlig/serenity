from contextlib import asynccontextmanager
import os
from typing import cast
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
import logging

# from app.ai.ai_handler import get_ai_response
from app.core.database import engine, Base, get_db
from app.models.models import Exercise, User
from app.core.auth_utils import (
    hash_password,
    login_check,
    create_access_token,
    decode_acces_token,
)
from app.schemas.api_schemas import (
    ChatItem,
    DashboardDataList,
    ExerciseCreate,
    ExerciseRead,
    ReturnedLoginData,
    UserBasic,
    UserCreate,
    UserOnboarding,
    UserRead,
)
from langchain_core.messages import HumanMessage
from langgraph.types import Overwrite
from langchain_core.runnables import RunnableConfig
from app.ai.serenity_core_agent import AgentState, create_serenity_core_agent
from app.services.user_service import USER_SERVICE
from app.services.exercise_service import EXERCISE_SERVICE
from sqlalchemy.exc import SQLAlchemyError
from app.services.vector_service import VECTOR_SERVICE
from app.core.chat_route_utils import (
    activate_archivist_agent,
    get_user_resources,
)
from app.ai.archivist_agent import ArchivistState, create_archivist_agent
from app.services.user_property_service import USER_PROPERTY_SERVICE
from exceptions import VectorError
from app.core.observer import langfuse_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alles hier drin passiert beim START der App
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Alles nach dem yield passiert beim STOPPEN (optional)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
load_dotenv()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# token wird aus dem header gefischt und entschlüsselt, bis wieder die user_id als string dasteht
# jetzt wird geguckt, ob dieser user noch existiert in der User table
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
):
    user_id = decode_acces_token(token)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültiges Token"
        )
    user = await USER_SERVICE.get_one_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User existiert nicht mehr"
        )
    return user


@app.get("/exercise")
async def show_exercises(db: AsyncSession = Depends(get_db)):
    exercises = await EXERCISE_SERVICE.get_all_exercises(db)
    return exercises


@app.post("/exercise", response_model=ExerciseRead)
async def add_exercises(user_input: ExerciseCreate, db: AsyncSession = Depends(get_db)):
    new_exercise = Exercise(
        title=user_input.title,
        goal=user_input.goal,
        expertise=user_input.expertise,
        emotions=user_input.emotions,
        instructions=user_input.instructions,
        media=user_input.media,
    )
    try:
        new_exercise = await EXERCISE_SERVICE.add_exercise(db, new_exercise)
        return new_exercise
    except (SQLAlchemyError, VectorError) as e:
        logger.error("Error while adding an exercise:", e)
        raise HTTPException(
            status_code=500, detail=f"Database error during saving, {e}"
        )


@app.delete("/exercise/{exercise_id}")
async def delete_exercise(exercise_id: int, db: AsyncSession = Depends(get_db)):
    try:
        result = await EXERCISE_SERVICE.delete_exercise(db, exercise_id)
        if result is None:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return result
    except HTTPException:
        raise
    except (SQLAlchemyError, VectorError) as e:
        raise HTTPException(
            status_code=500, detail=f"Technical error during deletion. {e}"
        )


@app.get("/exercise/{exercise_id}", response_model=ExerciseRead)
async def get_exercise_by_id(exercise_id: int, db: AsyncSession = Depends(get_db)):
    try:
        exercise = await EXERCISE_SERVICE.get_exercise_by_id(db, exercise_id)
        if exercise is None:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return exercise
    except HTTPException:
        raise
    except (SQLAlchemyError, VectorError) as e:
        raise HTTPException(
            status_code=500, detail=f"Technical error during deletion. {e}"
        )


@app.put("/exercise/{exercise_id}", response_model=ExerciseRead)
async def update_exercise(
    editedEx: ExerciseCreate, exercise_id: int, db: AsyncSession = Depends(get_db)
):
    try:
        updated_exercise = await EXERCISE_SERVICE.update_exercise(
            db, exercise_id, editedEx
        )
        if updated_exercise is None:
            raise HTTPException(status_code=404, detail="Exercise not found")
        return updated_exercise
    except HTTPException:
        raise
    except (SQLAlchemyError, VectorError) as e:
        raise HTTPException(
            status_code=500, detail=f"Technical error during update. {e}"
        )


@app.post("/register", response_model=UserRead)
async def register_user(user_reg: UserCreate, db: AsyncSession = Depends(get_db)):
    # passwort verschlüsseln
    hashed_pwd = hash_password(user_reg.password)
    # neuen user anlegen
    new_user = User(
        mail=user_reg.mail, nickname=user_reg.nickname, hashed_password=hashed_pwd
    )
    # zur table user hinzufügen
    try:
        await USER_SERVICE.register_user(db, new_user)
        return new_user
    except SQLAlchemyError as e:
        logger.error(f"Failed to register a new user: {e}")
        return {"error": e}, 500


@app.post("/login", response_model=ReturnedLoginData)
async def login_user(
    user_log: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    user = await USER_SERVICE.login_user(db, user_log.username)
    # Achtung: username ist hier das Hauptidentifizierungsmerkmal, egal, ob das Mail, name telefonnumber ist - es heißt immer username!
    if not user:
        raise HTTPException(status_code=400, detail="Falsche Daten")

    if not login_check(str(user.hashed_password), user_log.password):
        raise HTTPException(status_code=400, detail="Falsche Daten")
    # has_onboarding = await USER_SERVICE.user_exists_in_user_properties(db, user.id)

    user_info = {"sub": str(user.id)}
    token = create_access_token(user_info)
    return {
        "access_token": token,
        "token_type": "bearer",
        "hasOnboarding": user.has_onboarding,
        "nickname": user.nickname,
    }


@app.get("/user/profile", response_model=UserBasic)
async def show_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/onboarding")
async def save_onboarding_data(
    onboarding_data: UserOnboarding,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success_data = await USER_SERVICE.save_onboarding_data(
        db, onboarding_data, current_user
    )
    return success_data


@app.post("/chat")
async def handle_chat(
    new_message: ChatItem,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Umformulieren, der vom Frontend kommenden new-message, so dass sie zu langchain passt
    current_user_message = HumanMessage(content=new_message.content)

    user_data = await get_user_resources(db, current_user)
    config: RunnableConfig = {
        "configurable": {"thread_id": str(current_user.id)},
        "callbacks": [langfuse_handler],
        "metadata": {
            "langfuse_user_id": str(current_user.id),
            "user_name": current_user.nickname,
            "agent_version": "Version_1",
        },
    }
    serenity_core_agent = create_serenity_core_agent(db)
    message_limit = 8
    overlap = 4
    # hier wird der Archivist_Agent aktiviert!
    chat_state = serenity_core_agent.get_state(config)
    old_messages = chat_state.values.get("messages", [])
    total_messages = list(old_messages) + [current_user_message]
    serenity_input_messages = [current_user_message]
    if len(total_messages) >= message_limit:
        try:
            await activate_archivist_agent(db, current_user, total_messages)
            print("--- ARCHIVIST HAS FINISHED ---")
            trimmed_message_list = total_messages[-overlap:]
            await serenity_core_agent.aupdate_state(
                config, {"messages": Overwrite(trimmed_message_list)}
            )
            print("--- SPEICHER WURDE ERFOLGREICH GEKÜRZT ---")
            serenity_input_messages = []

        except Exception as e:
            logger.error(
                f"Archivist Agent failed, messages  will not be trimmed", exc_info=True
            )
    # dem agenten die bisherigen nachrichten mitgeben
    serenity_input: AgentState = {
        "messages": serenity_input_messages,
        "user_id": str(current_user.id),
        "user_data": user_data,
        # "message_trim": message_trim,
    }
    ai_response: AgentState = cast(
        AgentState, await serenity_core_agent.ainvoke(serenity_input, config)
    )
    serenity_text = ai_response["messages"][-1].content  # nur die letzte nachricht
    try:
        chat_state = serenity_core_agent.get_state(config)
        checkpointer_messages = chat_state.values.get("messages", [])
        logger.info(f"--- CHECKPOINTER DIAGNOSIS FOR USER {current_user.id} ---")
        logger.info(f"Total messages in Checkpointer RAM: {len(checkpointer_messages)}")

    except Exception as e:
        logger.error(f"Failed to read from checkpointer during diagnosis: {e}")
    return {"role": "assistant", "content": serenity_text}


@app.get("/dashboard", response_model=DashboardDataList)
async def show_user_data(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    try:
        result = await USER_PROPERTY_SERVICE.get_all_active_user_data(
            db, current_user.id
        )
        dashboard_data = prepare_data_for_frontend(result)
        return dashboard_data
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="Database currently unavailable.")


def prepare_data_for_frontend(result):
    dashboard_data = {
        "current_situation": [],
        "memory": [],
        "safe_place": [],
        "strengths": [],
        "goal": [],
        "belief": [],
        "pattern": [],
    }
    for element in result:
        if element.category in dashboard_data:
            dashboard_data[element.category].append(
                {
                    "id": element.id,
                    "content": element.content,
                    "reasoning": element.reasoning,
                    "created_at": element.created_at,
                    "expires_at": element.expires_at,
                }
            )
    return dashboard_data


@app.delete("/dashboard/delete/{item_id}")
async def delete_dashboard_items(
    item_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        is_users_data = await USER_PROPERTY_SERVICE.find_data_by_user_and_id(
            user_id=current_user.id, data_id=item_id, db=db
        )
        if is_users_data is None:
            raise HTTPException(
                status_code=404, detail="No item found with for this user"
            )
    except SQLAlchemyError:
        raise HTTPException(
            status_code=500, detail="Database connection failed. Please try again."
        )
    success = await VECTOR_SERVICE.delete_memory(item_id)
    if not success:
        raise HTTPException(
            status_code=500, detail="Vector Service temporaly not available."
        )
    try:
        await USER_PROPERTY_SERVICE.delete_data_by_id(
            data_id=item_id, db=db, raise_on_error=True
        )
        return {"message": "successfully deleted"}
    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Failed to delete item in database. Please try again.",
        )


@app.delete("/settings/user")
async def delete_user(
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    user_data = await USER_PROPERTY_SERVICE.get_all_user_data(
        db=db, user_id=current_user.id
    )
    item_ids = [item.id for item in user_data]
    try:
        success = await VECTOR_SERVICE.delete_memory(item_ids)
        if not success:
            raise Exception("Could not delete data from vector DB")
        await USER_SERVICE.delete_user(
            db=db,
            user_id=current_user.id,
        )
        chroma_cleanup = await VECTOR_SERVICE.delete_all_by_user_id(
            str(current_user.id)
        )
        if not chroma_cleanup:
            raise Exception("Could not wipe user_id metadata from vector DB")

    except (SQLAlchemyError, VectorError, ValueError) as error:
        await db.rollback()
        logger.error(
            f"Failed to delete user profile {current_user.id}: {error}", exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Technical error during profile deletion. {error}"
        )


# only test-functions
@app.get("/vectordata/{user_id}")
async def test_vector_db(user_id: str):
    if os.getenv("ENVIRONMENT") != "development":
        raise HTTPException(status_code=403, detail="Forbidden in production")

    memories = await VECTOR_SERVICE.get_memories_to_develop(user_id=user_id)
    return {"status": "In der Vektor-DB gefunden:", "data": memories}


@app.get("/clean-vectordata/{user_id}")
async def clean_vector_db(user_id: str):
    if os.getenv("ENVIRONMENT") != "development":
        raise HTTPException(status_code=403, detail="Forbidden in production")
    await VECTOR_SERVICE.delete_all_user_memories(user_id=user_id)
    return {
        "status": f"Alle Onboarding-Geisterdaten für User {user_id} wurden gelöscht!"
    }
