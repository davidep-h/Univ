from datetime import datetime
from typing import Annotated, Optional
from sqlmodel import SQLModel, Field

class Event(SQLModel, table=True):
    """Modello che rappresenta un evento nel database."""
    id: Optional[int] = Field(default=None, primary_key=True)
    title: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    date: datetime
    location: Annotated[str, Field(min_length=1)]