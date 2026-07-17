from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel import select

from app.data.db import SessionDep
from app.models.registration import Registration

router = APIRouter(prefix="/registrations", tags=["Registrations"])

@router.get("", response_model=list[Registration])
def get_registrations(session: SessionDep):
    return list(session.exec(select(Registration)).all())

@router.delete("", status_code=status.HTTP_200_OK)
def delete_registration(
    username: Annotated[str, Query(description="Username dell'iscritto")],
    event_id: Annotated[int, Query(description="ID dell'evento")],
    session: SessionDep
):
    statement = select(Registration).where(
        Registration.username == username,
        Registration.event_id == event_id
    )
    registration = session.exec(statement).first()

    if not registration:
        raise HTTPException(status_code=404, detail="Registrazione non trovata")
    
    session.delete(registration)
    session.commit()

    return {
        "message": f"Registrazione dell'utente {username} all'evento {event_id} eliminata con successo."
    }
