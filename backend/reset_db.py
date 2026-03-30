from sqlmodel import SQLModel, create_engine
from database import engine
from models import User, Client, Employee, Transaction, Milestone, RecurringExpense

def reset_db():
    print("Dropping all tables...")
    SQLModel.metadata.drop_all(engine)
    print("Creating all tables...")
    SQLModel.metadata.create_all(engine)
    print("Database reset successfully.")

if __name__ == "__main__":
    reset_db()
