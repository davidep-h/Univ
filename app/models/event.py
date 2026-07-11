from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class Event(SQLModel, table=True):
    """Modello che rappresenta un evento nel database."""
    id: Optional[int]=Field(default=None, primary_key=True) #assegna automaticamente un numero intero progressivo ogni volta che si crea un nuovo evento
    title: str
    description: str
    date: datetime
    location: str 