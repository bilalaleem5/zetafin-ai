from sqlmodel import Session, create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def sync():
    print(f"Syncing Database: {DATABASE_URL}")
    with engine.connect() as conn:
        # 1. Check/Add bank_balance to User
        try:
            conn.execute(text("ALTER TABLE user ADD bank_balance FLOAT DEFAULT 0.0"))
            conn.commit()
            print("Added bank_balance to user table.")
        except Exception:
            try:
                conn.execute(text("ALTER TABLE user ADD COLUMN bank_balance FLOAT DEFAULT 0.0"))
                conn.commit()
                print("Added bank_balance to user table (compat).")
            except: pass

        # 2. Check/Add recurring_id to Transaction
        try:
            conn.execute(text("ALTER TABLE transaction ADD COLUMN recurring_id INTEGER"))
            conn.commit()
            print("Added recurring_id to transaction table.")
        except Exception as e:
            print("recurring_id already exists or could not be added.")

        # Note: SQLModel create_db_and_tables handles NEW tables (AuditLog, Budget) automatically
        print("Schema sync attempt completed.")

if __name__ == "__main__":
    sync()
