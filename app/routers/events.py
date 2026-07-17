from typing import Annotated
from fastapi import APIRouter, HTTPException, Path, status
from pydantic import BaseModel, StrictStr, EmailStr
from datetime import datetime
from sqlmodel import select

from app.data.db import SessionDep
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration

router = APIRouter(prefix="/events", tags=["Events"])

# Modelli rigidi per forzare l'errore 422 nei test
class EventCreate(BaseModel):
    title: StrictStr
    description: StrictStr
    date: datetime
    location: StrictStr

class UserRegistration(BaseModel):
    username: StrictStr
    name: StrictStr
    email: EmailStr

@router.get("", response_model=list[Event])
def get_events(session: SessionDep):
    """Restituisce la lista di tutti gli eventi."""
    return list(session.exec(select(Event)).all())

@router.get("/{id}", response_model=Event)
def get_event(id: Annotated[int, Path(ge=1)], session: SessionDep):
    """Restituisce i dettagli di un singolo evento."""
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    return event
    
@router.post("", response_model=Event, status_code=status.HTTP_201_CREATED)
def create_event(event_in: EventCreate, session: SessionDep):
    """Crea un nuovo evento con validazione rigida."""
    db_event = Event(**event_in.model_dump())
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event
    
@router.put("/{id}", response_model=Event)
def update_event(id: Annotated[int, Path(ge=1)], event_in: EventCreate, session: SessionDep):
    """Aggiorna un evento esistente."""
    db_event = session.get(Event, id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
        
    update_data = event_in.model_dump(exclude_unset=True)
    db_event.sqlmodel_update(update_data)
        
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event

@router.post("/{id}/register", status_code=status.HTTP_201_CREATED, response_model=Registration)
def register_for_event(
    id: Annotated[int, Path(ge=1)], 
    user_in: UserRegistration, 
    session: SessionDep
):
    """Registra un utente a un evento, creando l'utente se non esiste."""
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
        
    db_user = session.get(User, user_in.username)
    if not db_user:
        db_user = User(username=user_in.username, name=user_in.name, email=user_in.email)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
    reg_statement = select(Registration).where(
        (Registration.event_id == id) & (Registration.username == db_user.username)
    )
    existing_registration = session.exec(reg_statement).first()
        
    if existing_registration:
        raise HTTPException(status_code=409, detail="Utente già registrato a questo evento")
            
    new_registration = Registration(username=db_user.username, event_id=id)
    session.add(new_registration)
    session.commit()
    session.refresh(new_registration)
    
    # I test pretendono che ritorni l'oggetto Registration
    return new_registration
    
@router.delete("", status_code=200)
def delete_all_events(session: SessionDep):
    """Elimina tutti gli eventi e le relative registrazioni in cascata."""
    for reg in session.exec(select(Registration)).all():
        session.delete(reg)
    for evento in session.exec(select(Event)).all():
        session.delete(evento)
    session.commit()
    return {"message": "Tutti gli eventi eliminati."}
    
@router.delete("/{id}", status_code=200)
def delete_event_by_id(id: Annotated[int, Path(ge=1)], session: SessionDep):
    """Elimina un singolo evento."""
    db_event = session.get(Event, id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
            
    for reg in session.exec(select(Registration).where(Registration.event_id == id)).all():
        session.delete(reg)
            
    session.delete(db_event)
    session.commit()
    return {"message": "Evento eliminato."}