from typing import Annotated
from sqlmodel import SQLModel, Field
from pydantic import EmailStr


class User(SQLModel, table=True):
    """Modello che rappresenta un utente nel database."""
    username: Annotated[str,Field(min_length=1,primary_key=True)]
    name: Annotated[str, Field(min_length=1)]
    email: EmailStr