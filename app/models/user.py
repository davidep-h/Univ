from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    """Modello che rappresenta un utente nel database."""
    username: str = Field(primary_key=True)
    name: str
    email: str