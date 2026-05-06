from contextlib import asynccontextmanager
from typing import cast
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.ai_handler import get_ai_response
from app.core.database import engine, Base, get_db
from app.models.models import Exercise, User
from app.core.auth_utils import (
    hash_password,
    login_check,
    create_access_token,
    decode_acces_token,
)
from app.schemas.schemas import (
    ChatItem,
    ExerciseCreate,
    ExerciseRead,
    ReturnedLoginData,
    UserCreate,
    UserOnboarding,
    UserRead,
)
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from app.ai.agent import AgentState, create_serenity_core_agent
from app.services.user_service import UserService, UserPropertyService
from app.services.exercise_service import EXERCISE_SERVICE
from sqlalchemy.exc import SQLAlchemyError
from exceptions import VectorError


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
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
USER_SERVICE = UserService()
USER_PROPERTY_SERVICE = UserPropertyService()


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
        content=user_input.content,
        instructions=user_input.instructions,
        media=user_input.media,
    )
    try:
        new_exercise = await EXERCISE_SERVICE.add_exercise(db, new_exercise)
        return new_exercise
    except (SQLAlchemyError, VectorError) as e:
        print("ERROR: ", e)
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
        print(e)
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


@app.get("/users/Profile", response_model=UserRead)
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
    conversation: list[ChatItem],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    langchain_messages = [
        (
            HumanMessage(content=item.content)
            if item.role == "user"
            else AIMessage(content=item.content)
        )
        for item in conversation
    ]
    user_strengths, user_safe_place = await USER_PROPERTY_SERVICE.get_user_resources(
        db, current_user.id
    )
    user_data = {
        "nickname": current_user.nickname,
        "age": current_user.age,
        "gender": current_user.gender,
        "strengths": user_strengths,
        "safe_place": user_safe_place,
    }

    config: RunnableConfig = {"configurable": {"thread_id": str(current_user.id)}}
    agent = create_serenity_core_agent(db, user_data)
    # dem agenten die bisherigen nachrichten mitgeben
    info_for_agent: AgentState = {"messages": langchain_messages}
    ai_response = cast(AgentState, await agent.ainvoke(info_for_agent, config))
    serenity_text = ai_response["messages"][-1].content  # nur die letzte nachricht

    return {"role": "assistant", "content": serenity_text}
