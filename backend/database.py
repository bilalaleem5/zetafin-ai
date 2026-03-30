import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

load_dotenv()

# NeonDB URL will be provided via environment variables
# Local SQLite default for robustness
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./zetamize.db")

engine = create_engine(DATABASE_URL, echo=True, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

def create_db_and_tables():
    from models import SQLModel
    # Ensure all models are registered by importing them here
    import models 
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
