from fastapi import APIRouter, HTTPException, status, Request
from sqlmodel import Session, select
from app.models.user import User
from app.models.registration import Registration
from app.data.db import engine

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("", response_model=list[User])
def get_users():
    """Restituisce la lista di tutti gli utenti esistenti nel database."""
    with Session(engine) as session:
        return session.exec(select(User)).all()

@router.post("", response_model=User, status_code=201)
async def create_user(request: Request):
    """Crea un nuovo utente nel database."""
    data = await request.json()
    
    for field in ["username", "name", "email"]:
        if field not in data:
            raise HTTPException(status_code=422, detail=f"Manca il campo obbligatorio: {field}")
            
    if type(data.get("username")) is not str:
        raise HTTPException(status_code=422, detail="L'username deve essere testo")
        
    with Session(engine) as session:
        if session.get(User, data.get("username")):
            raise HTTPException(status_code=400, detail="Username già esistente")
        
        new_user = User(**data)
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
        return new_user

@router.get("/{username}", response_model=User)
def get_user(username: str):
    """Restituisce i dettagli di un singolo utente in base al suo username."""
    with Session(engine) as session:
        user = session.get(User, username)
        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        return user

@router.delete("/{username}", status_code=200)
def delete_user(username: str):
    """Elimina un utente specifico dal database in base al suo username."""
    with Session(engine) as session:
        db_user = session.get(User, username)
        if not db_user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        
        for reg in session.exec(select(Registration).where(Registration.username == username)).all():
            session.delete(reg)
        
        session.delete(db_user)
        session.commit()
        return {"message": f"Utente eliminato con successo."}
    
@router.delete("", status_code=200)
def delete_all_users():
    """Elimina tutti gli utenti dal database e tutte le relative registrazioni agli eventi."""
    with Session(engine) as session:
        for reg in session.exec(select(Registration)).all():
            session.delete(reg)
        for utente in session.exec(select(User)).all():
            session.delete(utente)
        session.commit()
        return {"message": "Tutti gli utenti sono stati eliminati con successo."}
