import os
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional
from http import HTTPStatus

# ---------------------------------------------------------------------------
# JWT / auth configuration
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "changeme-use-a-long-random-secret-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI(title="Users Microservice", version="1.0.0")

# Mock "auth" users (username -> pre-computed bcrypt password hash)
# Hashes were generated with passlib CryptContext(schemes=["bcrypt"]).
# admin123  ->  $2b$12$rxxKLw3cRqzao22GEUdrWOp0J2NfA1Gx9tf15Pg3Pha.8bYnvimyu
# password1 ->  $2b$12$wt2USPujg/EDzOCmuazpZeVGsBCZMemkBeNNv0SugZT3bwYzxw78e
MOCK_AUTH_USERS: dict[str, dict] = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$rxxKLw3cRqzao22GEUdrWOp0J2NfA1Gx9tf15Pg3Pha.8bYnvimyu",
    },
    "user1": {
        "username": "user1",
        "hashed_password": "$2b$12$wt2USPujg/EDzOCmuazpZeVGsBCZMemkBeNNv0SugZT3bwYzxw78e",
    },
}


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

class Token(BaseModel):
    access_token: str
    token_type: str


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _authenticate_user(username: str, password: str) -> Optional[dict]:
    user = MOCK_AUTH_USERS.get(username)
    if not user or not _verify_password(password, user["hashed_password"]):
        return None
    return user


def _create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception
    if username not in MOCK_AUTH_USERS:
        raise credentials_exception
    return username


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class User(BaseModel):
    id: int
    name: str
    email: str
    username: str
    phone: Optional[str] = None
    website: Optional[str] = None

MOCK_USERS: dict[int, User] = {
    1: User(id=1, name="Alice Johnson", email="alice@example.com", username="alicej", phone="555-1234", website="alice.dev"),
    2: User(id=2, name="Bob Smith", email="bob@example.com", username="bobs", phone="555-5678", website="bobsmith.io"),
    3: User(id=3, name="Carol Williams", email="carol@example.com", username="carolw", phone="555-9012", website="carol.net"),
    4: User(id=4, name="David Brown", email="david@example.com", username="davidb", phone="555-3456", website="david.com"),
    5: User(id=5, name="Eva Martinez", email="eva@example.com", username="evam", phone="555-7890", website="evamartinez.org"),
}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"message": "Users Microservice is running"}


# Auth endpoints

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = _authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = _create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/auth/me")
def get_me(current_user: str = Depends(get_current_user)):
    return {"username": current_user}


# User endpoints (protected)

@app.get("/users", response_model=List[User])
def get_users(current_user: str = Depends(get_current_user)):
    return list(MOCK_USERS.values())


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, current_user: str = Depends(get_current_user)):
    user = MOCK_USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User with id {user_id} not found")
    return user


class UserCreate(BaseModel):
    name: str
    email: str
    username: str
    phone: Optional[str] = None
    website: Optional[str] = None


@app.post("/users", response_model=User, status_code=HTTPStatus.CREATED)
def create_user(user_data: UserCreate, current_user: str = Depends(get_current_user)):
    new_id = max(MOCK_USERS.keys(), default=0) + 1
    new_user = User(id=new_id, **user_data.model_dump())
    MOCK_USERS[new_id] = new_user
    return new_user
