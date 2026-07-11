from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import Session, select
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration
from app.data.db import engine

# Il prefisso "/users" viene applicato in automatico a tutte le rotte
router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=list[User])
def get_users():
    """ Restituisce la lista di tutti gli utenti esistenti nel database. """
    with Session(engine) as session:
        users=session.exec(select(User)).all()
        return users

@router.post("", response_model=User, status_code=201)
def create_user(user: User):
    """Crea un nuovo utente nel database."""
    with Session(engine) as session:
        db_user=session.get(User, user.username)

        if db_user:
            raise HTTPException(status_code=400, detail="Username già esistente")
        
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

@router.get("/{username}", response_model=User)
def get_user(username: str):
    """Restituisce i dettagli di un singolo utente in base al suo username."""
    with Session(engine) as session:
        user=session.get(User, username)

        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        return user

@router.delete("/{username}", status_code=200)
def delete_user(username: str):
    """Elimina un utente specifico dal database in base al suo username."""
    with Session(engine) as session:
        db_user=session.get(User, username)

        if not db_user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        
        statement=select(Registration).where(Registration.username==username)
        registrations=session.exec(statement).all()

        for reg in registrations:
            session.delete(reg)
        
        session.delete(db_user)
        session.commit()
        return {"message": f"Utente '{username}' e le sue registrazioni eliminati con successo."}
    
@router.delete("", status_code=200)
def delete_all_users():
    """Elimina tutti gli utenti dal database e tutte le relative registrazioni agli eventi."""
    with Session(engine) as session:
        registrazioni=session.exec(select(Registration)).all()
        for reg in registrazioni:
            session.delete(reg)

        utenti=session.exec(select(User)).all()
        for utente in utenti:
            session.delete(utente)

        session.commit()
        return{"message": "Tutti gli utenti e le registrazioni sono stati eliminati con successo."}