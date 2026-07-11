from sqlmodel import Session, select 
from app.models.event import Event
from app.data.db import engine 
from app.config import config
from datetime import datetime
from app.models.user import User
from app.models.registration import Registration


# NB: do not add imports here!

from pathlib import Path
import os

# ...and here!!

if Path(__file__).parent == Path(os.getcwd()):
    config.root_dir = "."

# You can add imports from here...

from fastapi import FastAPI, HTTPException, Response, status
from app.routers import frontend
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.data.db import init_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # on start
    init_database()
    yield
    # on close


app = FastAPI(lifespan=lifespan)
app.mount(
    "/static",
    StaticFiles(directory=config.root_dir / "static"),
    name="static"
)
app.include_router(frontend.router)

@app.get("/events", response_model=list[Event])
def get_events():
    """Restituisce la lista di tutti gli eventi nel database"""
    with Session(engine) as session:
        events=session.exec(select(Event)).all()
        return events

@app.get("/events/{id}", response_model=Event)
def get_event(id: int):
    """Restituisce l'evento con l'id indicato."""
    with Session(engine) as session:
        event=session.get(Event, id)
        if not event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        return event
    
@app.post("/events", response_model=Event, status_code=201)
def create_event(event: Event):
    """ Crea un nuovo evento nel database."""
    date_str = str(event.date).replace("Z", "+00:00")
    vera_data = datetime.fromisoformat(date_str)
    
    db_event = Event(
        title=event.title,
        description=event.description,
        date=vera_data,
        location=event.location
    )
    
    with Session(engine) as session:
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return db_event
    
    
@app.put("/events/{id}", response_model=Event)
def update_event(id:int, event_update: Event):
    """ Aggiorna i dati di un evento esistente."""
    with Session(engine) as session:
        db_event=session.get(Event, id)

        if not db_event:
            raise HTTPException(status_code=404, detail="Evento non trovato")
        
        db_event.title=event_update.title
        db_event.description=event_update.description
        db_event.location=event_update.location
        
        date_str=str(event_update.date).replace("Z", "+00:00")
        db_event.date=datetime.fromisoformat(date_str)
        
        session.add(db_event)
        session.commit()
        session.refresh(db_event)
        return db_event


@app.post("/events/{id}/register")
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
    
@app.delete("/events", status_code = 200)
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
    
@app.delete("/events/{id}", status_code = 200)
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


@app.get("/users", response_model=list[User])
def get_users():
    """ Restituisce la lista di tutti gli utenti esistenti nel database. """
    with Session(engine) as session:
        users=session.exec(select(User)).all()
        return users


@app.post("/users", response_model=User, status_code=201)
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

@app.get("/users/{username}", response_model=User)
def get_user(username: str):
    """Restituisce i dettagli di un singolo utente in base al suo username."""
    with Session(engine) as session:
        user=session.get(User, username)

        if not user:
            raise HTTPException(status_code=404, detail="Utente non trovato")
        return user

@app.delete("/users/{username}", status_code=200)
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
    
@app.delete("/users", status_code=200)
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
        return{"message": "Tutti gli utenti e le registrazioni sono stati eliminati con successo. "}
    
@app.get("/registrations", response_model=list[Registration])
def get_registrations():
    """Restituisce la lista di tutte le registrazioni esistenti nel database."""
    with Session(engine) as session:
        registrations=session.exec(select(Registration)).all()
        return registrations

@app.delete("/registrations", status_code=200)
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
    

    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", reload=True)
