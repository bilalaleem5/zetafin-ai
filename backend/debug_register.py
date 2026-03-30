import traceback
import sys
import os

# Mock environment if needed
os.environ["DATABASE_URL"] = "sqlite:///./zetamize.db"

try:
    from main import app, register_user
    from schemas import UserCreate
    from database import get_session
    from sqlmodel import Session
    
    print("Attempting to register user...")
    user_data = UserCreate(
        email="debug_final@test.com", 
        password="Password123!", 
        business_name="Debug Biz", 
        industry="Tech", 
        whatsapp_number="1234567899"
    )
    
    # Get session manually
    session_gen = get_session()
    session = next(session_gen)
    
    result = register_user(user_data, session)
    print(f"SUCCESS: Created user {result.id}")
    
except Exception as e:
    print("FAILED with exception:")
    traceback.print_exc()
