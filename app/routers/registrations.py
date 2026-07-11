from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import Session, select
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration
from app.data.db import engine

# Il prefisso "/registrations" viene applicato in automatico a tutte le rotte
router = APIRouter(prefix="/registrations", tags=["Registrations"])

@router.get("", response_model=list[Registration])
def get_registrations():
    """Restituisce la lista di tutte le registrazioni esistenti nel database."""
    with Session(engine) as session:
        registrations=session.exec(select(Registration)).all()
        return registrations

@router.delete("", status_code=200)
def delete_registration(username: str, event_id: int):
    """Elimina una singola registrazione. Richiede 'username' ed 'event_id' come query parameters."""
    with Session(engine) as session:
        statement=select(Registration).where(
            (Registration.username==username) & (Registration.event_id==event_id)
        )
        registration=session.exec(statement).first()

        if not registration:
            raise HTTPException(status_code=404, detail="Registrazione non trovata")
        
        session.delete(registration)
        session.commit()

        return {"message": f"Registrazione dell'utente {username} all'evento {event_id} eliminata con successo."}
