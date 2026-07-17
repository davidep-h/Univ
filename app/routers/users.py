from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, status
from sqlmodel import select

from app.data.db import SessionDep
from app.models.registration import Registration
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/")
def get_all_users(session: SessionDep) -> list[User]:
    """Returns the list of all registered users"""
    return list(session.exec(select(User)).all())


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={409: {"description": "Username already exists"}},
)
def add_user(user_in: User, session: SessionDep):
    """Adds a new user"""
    existing = session.get(User, user_in.username)
    if existing:
        raise HTTPException(status_code=409, detail="Username already exists")
    
    # Non serve model_validate perché user_in è già di tipo User
    session.add(user_in)
    session.commit()
    return "User added successfully"


@router.get("/{username}", responses={404: {"description": "User not found"}})
def get_user_by_username(
    username: Annotated[str, Path(description="The username of the user to retrieve")],
    session: SessionDep,
) -> User:
    """Returns the user with the given username"""
    user = session.get(User, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{username}", responses={404: {"description": "User not found"}})
def delete_user(
    username: Annotated[str, Path(description="Username dell'utente da eliminare")],
    session: SessionDep,
):
    """Elimina l'utente con il dato username e le relative registrazioni; 404 se non esiste."""
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
    """Elimina tutti gli utenti e tutte le relative registrazioni."""
    registrations = session.exec(select(Registration)).all()
    for reg in registrations:
        session.delete(reg)
        
    users = session.exec(select(User)).all()
    for user in users:
        session.delete(user)
        
    session.commit()
    return {"message": "All users deleted"}
