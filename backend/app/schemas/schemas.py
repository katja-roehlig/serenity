from pydantic import BaseModel, EmailStr, ConfigDict
from pydantic.alias_generators import to_camel


class NewBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, from_attributes=True
    )


# diese schemas werden auch oft dto (DataTransferObjekt) oder pojo genannt
# gibt der user beim erstellen(POST) ein
class ExerciseCreate(NewBaseModel):
    title: str
    goal: str
    expertise: str
    emotions: str
    instructions: str
    media: str | None = None


# wird mitgeschickt, wenn das FE die daten abruft
class ExerciseRead(ExerciseCreate):
    id: int

    class Config:
        from_attributes = True


class UserCreate(NewBaseModel):
    mail: EmailStr
    password: str
    nickname: str


class UserRead(NewBaseModel):
    id: int
    mail: EmailStr
    nickname: str

    class Config:
        from_attributes = True


class ReturnedLoginData(NewBaseModel):
    access_token: str
    token_type: str
    has_onboarding: bool
    nickname: str


class UserOnboarding(NewBaseModel):
    age: int
    gender: str
    strengths: list[str]
    safe_place: str


class ChatItem(NewBaseModel):
    id: str
    role: str
    content: str


# class ChatContent(BaseModel):
#     conversations: list[ChatItem]
