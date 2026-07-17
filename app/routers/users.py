from typing import Annotated
from fastapi import APIRouter, HTTPException, Path, status
from pydantic import BaseModel, StrictStr, EmailStr
from sqlmodel import select

from app.data.db import SessionDep
from app.models.registration import Registration
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

# Modello rigido per forzare il 422 se passano un intero come username
class UserCreate(BaseModel):
    username: StrictStr
    name: StrictStr
    email: EmailStr

@router.get("/")
def get_all_users(session: SessionDep) -> list[User]:
    """Restituisce la lista di tutti gli utenti registrati."""
    return list(session.exec(select(User)).all())


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_user(user_in: UserCreate, session: SessionDep):
    """Crea un nuovo utente nel sistema."""
    existing = session.get(User, user_in.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    
    db_user = User(**user_in.model_dump())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@router.get("/{username}")
def get_user_by_username(
    username: Annotated[str, Path(description="L'username dell'utente")],
    session: SessionDep,
) -> User:
    """Restituisce i dettagli di un singolo utente."""
    user = session.get(User, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{username}")
def delete_user(
    username: Annotated[str, Path(description="L'username da eliminare")],
    session: SessionDep,
):
    """Elimina l'utente e disiscrive a cascata le sue registrazioni."""
    user = session.get(User, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    registrations = session.exec(
        select(Registration).where(Registration.username == username)
    ).all()
    for reg in registrations:
        session.delete(reg)
        
    session.delete(user)
    session.commit()
    return {"message": "User deleted"}


@router.delete("/")
def delete_all_users(session: SessionDep):
    """Elimina tutti gli utenti dal database."""
    registrations = session.exec(select(Registration)).all()
    for reg in registrations:
        session.delete(reg)
        
    users = session.exec(select(User)).all()
    for user in users:
        session.delete(user)
        
    session.commit()
    return {"message": "All users deleted"}