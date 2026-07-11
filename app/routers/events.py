from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import Session, select
from app.models.event import Event
from app.models.user import User
from app.models.registration import Registration
from app.data.db import engine


router = APIRouter(prefix="/events", tags=["Events"])

@router.get("", response_model=list[Event])
def get_events():
    """Restituisce la lista di tutti gli eventi nel database"""
    with Session(engine) as session:
        events = session.exec(select(Event)).all()
        return events

@router.put("/events/{id}", response_model=Event)
def update_event(id: int, event_update: Event):
    """Aggiorna i dati di un evento esistente."""
    with Session(engine) as session:
        # 1. Cerchiamo l'evento nel database
        db_event = session.get(Event, id)

        # 2. Se non esiste, restituiamo 404
        if not db_event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        
        # 3. Aggiorniamo i campi in modo diretto, compresa la data
        db_event.title = event_update.title
        db_event.description = event_update.description
        db_event.location = event_update.location
        db_event.date = event_update.date
        
        # 4. Salviamo le modifiche
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return db_event


@router.post("/events/{id}/register")
def register_for_event(id: int, user_data: User, response: Response):
    """
    Registra un utente all'evento con l'id indicato.
    Se l'utente non esiste ancora, viene creato automaticamente.
    """
    with Session(engine) as session:
        # 1. Verifichiamo che l'evento esista (404 se manca)
        event = session.get(Event, id)
        if not event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        
        # 2. Cerchiamo l'utente nel database nel modo più diretto possibile
        db_user = session.get(User, user_data.username)
        
        # 3. Se l'utente non esiste, lo creiamo usando i dati ricevuti
        if not db_user:
            db_user = User(
                username=user_data.username, 
                name=user_data.name, 
                email=user_data.email
            )
            session.add(db_user)
            session.commit()
            session.refresh(db_user)
            response.status_code = status.HTTP_201_CREATED
        else:
            response.status_code = status.HTTP_200_OK
        
        # 4. Controlliamo che la registrazione non esista già usando lo username corretto
        reg_statement = select(Registration).where(
            (Registration.event_id == id) & (Registration.username == db_user.username)
        )
        existing_registration = session.exec(reg_statement).first()
        
        # 5. Se non è ancora registrato, creiamo il collegamento nella tabella pivot
        if not existing_registration:
            new_registration = Registration(username=db_user.username, event_id=id)
            session.add(new_registration)
            session.commit()
            
        return {"message": "Registrazione completata con successo"}
    
@router.delete("/events", status_code = 200)
def delete_all_events():
    """ Elimina tutti gli eventi dal database."""
    with Session(engine) as session:
        registrazioni = session.exec(select(Registration)).all()
        for reg in registrazioni:
            session.delete(reg)
        
        
        eventi = session.exec(select(Event)).all()
        for evento in eventi:
            session.delete(evento)
            
        
        session.commit()
        return {"message": "Tutti gli eventi e le registrazioni sono stati eliminati con successo."}
    
@router.delete("/events/{id}", status_code = 200)
def delete_event_by_id(id:int):
    """Elimina un evento specifico dal database in base al suo ID."""
    with Session(engine) as session:
        db_event = session.get(Event, id)
        if not db_event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
            
        statement = select(Registration).where(Registration.event_id == id)
        registrations = session.exec(statement).all()
        
        for reg in registrations:
            session.delete(reg)
            
        session.delete(db_event)
        session.commit()
        return {"message": f"Evento con ID {id} e le sue registrazioni eliminati."}
