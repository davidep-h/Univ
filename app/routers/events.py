from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import Session, select
from datetime import datetime
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration
from app.data.db import engine

router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=list[Event])
def get_events():
    """Restituisce la lista di tutti gli eventi."""
    with Session(engine) as session:
        events = session.exec(select(Event)).all()
        return events

@router.get("/{id}", response_model=Event)
def get_event(id: int):
    """Restituisce l'evento con l'id indicato."""
    with Session(engine) as session:
        event = session.get(Event, id)
        if not event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        return event
    
@router.post("", response_model=Event, status_code=201)
def create_event(event: Event):
    """Crea un nuovo evento."""
    with Session(engine) as session:
        session.add(event)
        session.commit()
        session.refresh(event)
        return event
    
@router.put("/{id}", response_model=Event)
def update_event(id: int, event_update: Event):
    """Aggiorna un evento esistente."""
    with Session(engine) as session:
        db_event = session.get(Event, id)
        if not db_event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        
        db_event.title = event_update.title
        db_event.description = event_update.description
        db_event.location = event_update.location
        db_event.date = event_update.date
        
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return db_event

@router.post("/{id}/register", status_code=200)
def register_for_event(id: int, user_data: User, response: Response):
    """Registra un utente all'evento."""
    with Session(engine) as session:
        event = session.get(Event, id)
        if not event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        
        db_user = session.get(User, user_data.username)
        if not db_user:
            db_user = User(username=user_data.username, name=user_data.name, email=user_data.email)
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            response.status_code = status.HTTP_201_CREATED
        
        reg_statement = select(Registration).where(
            (Registration.event_id == id) & (Registration.username == db_user.username)
        )
        existing_registration = session.exec(reg_statement).first()
        
        if not existing_registration:
            new_registration = Registration(username=db_user.username, event_id=id)
            session.add(new_registration)
            session.commit()
            
        return {"message": "Registrazione completata con successo"}
    
@router.delete("", status_code=200)
def delete_all_events():
    """Elimina tutti gli eventi."""
    with Session(engine) as session:
        for reg in session.exec(select(Registration)).all():
            session.delete(reg)
        for evento in session.exec(select(Event)).all():
            session.delete(evento)
        session.commit()
        return {"message": "Tutti gli eventi eliminati."}
    
@router.delete("/{id}", status_code=200)
def delete_event_by_id(id: int):
    """Elimina un evento specifico."""
    with Session(engine) as session:
        db_event = session.get(Event, id)
        if not db_event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
            
        for reg in session.exec(select(Registration).where(Registration.event_id == id)).all():
            session.delete(reg)
            
        session.delete(db_event)
        session.commit()
        return {"message": "Evento eliminato."}
