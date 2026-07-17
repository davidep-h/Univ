from typing import Annotated
from fastapi import APIRouter, HTTPException, Response, status, Path
from pydantic import EmailStr
from sqlmodel import select, SQLModel

from app.data.db import SessionDep
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration

router = APIRouter(prefix="/events", tags=["Events"])

class UserRegistration(SQLModel):
    username: str
    name: str
    email: EmailStr

@router.get("", response_model=list[Event])
def get_events(session: SessionDep):
    return list(session.exec(select(Event)).all())

@router.get("/{id}", response_model=Event)
def get_event(id: Annotated[int, Path(ge=1)], session: SessionDep):
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
    return event
    
@router.post("", response_model=Event, status_code=201)
def create_event(event_in: Event, session: SessionDep):
    session.add(event_in)
    session.commit()
    session.refresh(event_in)
    return event_in
    
@router.put("/{id}", response_model=Event)
def update_event(id: Annotated[int, Path(ge=1)], event_in: Event, session: SessionDep):
    db_event = session.get(Event, id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
        
    update_data = event_in.model_dump(exclude_unset=True, exclude={"id"})
    db_event.sqlmodel_update(update_data)
        
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event

@router.post("/{id}/register", status_code=200)
def register_for_event(
    id: Annotated[int, Path(ge=1)], 
    user_in: UserRegistration, 
    response: Response,
    session: SessionDep
):
    event = session.get(Event, id)
    if not event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
        
    db_user = session.get(User, user_in.username)
    if not db_user:
        db_user = User(username=user_in.username, name=user_in.name, email=user_in.email)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        response.status_code = status.HTTP_201_CREATED
    else:
        response.status_code = status.HTTP_200_OK
        
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
def delete_all_events(session: SessionDep):
    for reg in session.exec(select(Registration)).all():
        session.delete(reg)
    for evento in session.exec(select(Event)).all():
        session.delete(evento)
    session.commit()
    return {"message": "Tutti gli eventi eliminati."}
    
@router.delete("/{id}", status_code=200)
def delete_event_by_id(id: Annotated[int, Path(ge=1)], session: SessionDep):
    db_event = session.get(Event, id)
    if not db_event:
        raise HTTPException(status_code=404, detail="Evento non trovato")
            
    for reg in session.exec(select(Registration).where(Registration.event_id == id)).all():
        session.delete(reg)
            
    session.delete(db_event)
    session.commit()
    return {"message": "Evento eliminato."}