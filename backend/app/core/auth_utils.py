import os
from dotenv import load_dotenv
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWSError, jwt
from datetime import datetime, timedelta, timezone

load_dotenv()
SECRET_KEY = os.getenv("MY_SECRET_JWT_KEY")
if not SECRET_KEY:
    raise RuntimeError("Attention: MY_SECRET_KEY was not found in .env file!")


# im Mixer wird die Methode gespeichert, mit der das password verschlüsselt wird
pwd_mixer = PasswordHasher()


# Hier wirds verschlüsselt
def hash_password(password: str):
    return pwd_mixer.hash(password)


# Prüft ob beim Login das Passwort und die Verschlüsselung zusammenpassen
def login_check(
    hashed_password: str,
    plain_password: str,
):
    try:
        return pwd_mixer.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def create_access_token(data: dict):
    user_info = data.copy()
    # zeitpunkt andem die user-session ungültig wird festlegen
    expire_time = datetime.now(timezone.utc) + timedelta(days=30)
    # in die user info wird der Expire_Zeitpunkt dazugeschrieben
    user_info.update({"exp": expire_time})
    # jetzt wird das jwt token erstellt
    token = jwt.encode(user_info, str(SECRET_KEY), algorithm="HS256")
    return token


def decode_acces_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(token, str(SECRET_KEY), algorithms=["HS256"])
        user_id = decoded_token.get("sub")
        if not user_id:
            return None
        return user_id
    except JWSError:
        return None
