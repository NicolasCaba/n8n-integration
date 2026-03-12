from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from http import HTTPStatus

app = FastAPI(title="Users Microservice", version="1.0.0")

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


@app.get("/")
def root():
    return {"message": "Users Microservice is running"}


@app.get("/users", response_model=List[User])
def get_users():
    return list(MOCK_USERS.values())


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
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
def create_user(user_data: UserCreate):
    new_id = max(MOCK_USERS.keys(), default=0) + 1
    new_user = User(id=new_id, **user_data.model_dump())
    MOCK_USERS[new_id] = new_user
    return new_user
