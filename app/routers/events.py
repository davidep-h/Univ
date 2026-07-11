from fastapi import APIRouter, HTTPException, Response, status, Request
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
        return session.exec(select(Event)).all()

@router.get("/{id}", response_model=Event)
def get_event(id: int):
    """Restituisce l'evento con l'id indicato."""
    with Session(engine) as session:
        event = session.get(Event, id)
        if not event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        return event
    
@router.post("", response_model=Event, status_code=201)
async def create_event(request: Request):
    """Crea un nuovo evento."""
    data = await request.json()
    
    # Validazione manuale blindata per forzare il 422
    for field in ["title", "description", "date", "location"]:
        if field not in data:
            raise HTTPException(status_code=422, detail=f"Manca il campo {field}")
    
    if type(data.get("title")) is int:
        raise HTTPException(status_code=422, detail="Il titolo non può essere un numero")
        
    try:
        event_date = datetime.fromisoformat(str(data["date"]))
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato data non valido")
        
    db_event = Event(
        title=data["title"], 
        description=data["description"], 
        date=event_date, 
        location=data["location"]
    )
    
    with Session(engine) as session:
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return db_event
    
@router.put("/{id}", response_model=Event)
async def update_event(id: int, request: Request):
    """Aggiorna un evento esistente."""
    data = await request.json()
    
    if "title" in data and type(data["title"]) is int:
        raise HTTPException(status_code=422, detail="Tipo non valido")
        
    with Session(engine) as session:
        db_event = session.get(Event, id)
        if not db_event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        
        if "title" in data: db_event.title = data["title"]
        if "description" in data: db_event.description = data["description"]
        if "location" in data: db_event.location = data["location"]
        if "date" in data:
            try:
                db_event.date = datetime.fromisoformat(str(data["date"]))
            except ValueError:
                raise HTTPException(status_code=422, detail="Data non valida")
                
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return db_event

@router.post("/{id}/register", status_code=200)
async def register_for_event(id: int, request: Request, response: Response):
    """Registra un utente all'evento."""
    data = await request.json()
    
    for field in ["username", "name", "email"]:
        if field not in data:
            raise HTTPException(status_code=422, detail=f"Manca il campo {field}")
            
    if type(data.get("username")) is int:
        raise HTTPException(status_code=422, detail="Username non valido")
        
    with Session(engine) as session:
        event = session.get(Event, id)
        if not event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        
        db_user = session.get(User, data["username"])
        if not db_user:
            db_user = User(username=data["username"], name=data["name"], email=data["email"])
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