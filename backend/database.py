import os
from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv

load_dotenv()

# NeonDB URL will be provided via environment variables
# Local SQLite default for robustness
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./zetamize.db")

engine_args = {}
if "sqlite" in DATABASE_URL:
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    engine_args["pool_pre_ping"] = True
    engine_args["pool_recycle"] = 300

engine = create_engine(DATABASE_URL, echo=True, **engine_args)

def create_db_and_tables():
    from models import SQLModel
    # Ensure all models are registered by importing them here
    import models 
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
