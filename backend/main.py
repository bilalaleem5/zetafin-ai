from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List
import uvicorn
import traceback
import os
from datetime import datetime

from database import engine, get_session, create_db_and_tables
from models import User, Client, Employee, Transaction, Milestone, RecurringExpense
from schemas import (
    UserCreate, UserRead, Token, 
    ClientCreate, ClientRead, 
    EmployeeCreate, EmployeeRead, 
    TransactionCreate, TransactionRead,
    MilestoneCreate, MilestoneRead,
    RecurringExpenseCreate, RecurringExpenseRead,
    BalanceUpdate
)
from auth import (
    get_password_hash, verify_password, 
    create_access_token, get_current_user
)
from whatsapp import parse_whatsapp_message
from services import process_automation_for_user
from datetime import datetime, timedelta

app = FastAPI(title="ZetaMize API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
async def root():
    return {"message": "Welcome to ZetaMize API"}

# --- AUTH ---
@app.post("/register", response_model=UserRead)
def register_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = session.exec(select(User).where(User.email == user.email)).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        email=user.email,
        password_hash=hashed_password,
        business_name=user.business_name,
        industry=user.industry,
        currency=user.currency,
        whatsapp_number=user.whatsapp_number
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    return new_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = session.exec(select(User).where(User.email == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.patch("/users/me/balance")
def update_bank_balance(update: BalanceUpdate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    current_user.bank_balance = update.balance
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user

# --- CLIENTS ---
@app.post("/clients/", response_model=ClientRead)
def create_client(client: ClientCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_client = Client(**client.dict(), user_id=current_user.id)
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client

@app.get("/clients/", response_model=List[ClientRead])
def read_clients(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    clients = session.exec(select(Client).where(Client.user_id == current_user.id)).all()
    return clients

@app.patch("/clients/{client_id}", response_model=ClientRead)
def update_client(client_id: int, client_update: ClientCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == current_user.id)).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    update_data = client_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_client, key, value)
    
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    return db_client

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == current_user.id)).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    # Also delete associated milestones and transactions to maintain integrity
    session.delete(db_client)
    session.commit()
    return {"ok": True}

# --- MILESTONES ---
@app.post("/clients/{client_id}/milestones/", response_model=MilestoneRead)
def create_milestone(client_id: int, milestone: MilestoneCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == current_user.id)).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    db_milestone = Milestone(**milestone.dict(), client_id=client_id, user_id=current_user.id)
    session.add(db_milestone)
    session.commit()
    session.refresh(db_milestone)
    return db_milestone

@app.get("/clients/{client_id}/milestones/", response_model=List[MilestoneRead])
def read_milestones(client_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    milestones = session.exec(select(Milestone).where(Milestone.client_id == client_id, Milestone.user_id == current_user.id)).all()
    return milestones

@app.patch("/milestones/{milestone_id}", response_model=MilestoneRead)
def update_milestone(milestone_id: int, milestone_update: MilestoneCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_milestone = session.exec(select(Milestone).where(Milestone.id == milestone_id, Milestone.user_id == current_user.id)).first()
    if not db_milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    
    update_data = milestone_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_milestone, key, value)
    
    session.add(db_milestone)
    session.commit()
    session.refresh(db_milestone)
    return db_milestone

@app.delete("/milestones/{milestone_id}")
def delete_milestone(milestone_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_milestone = session.exec(select(Milestone).where(Milestone.id == milestone_id, Milestone.user_id == current_user.id)).first()
    if not db_milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    session.delete(db_milestone)
    session.commit()
    return {"ok": True}

@app.post("/milestones/{milestone_id}/receive", response_model=TransactionRead)
def receive_milestone_payment(milestone_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    print(f"DEBUG: Receiving payment for milestone {milestone_id}")
    milestone = session.exec(select(Milestone).where(Milestone.id == milestone_id, Milestone.user_id == current_user.id)).first()
    if not milestone:
        print(f"DEBUG: Milestone {milestone_id} not found for user {current_user.id}")
        raise HTTPException(status_code=404, detail="Milestone not found")
    if milestone.status == "Paid":
        raise HTTPException(status_code=400, detail="Milestone already paid")
    
    milestone.status = "Paid"
    session.add(milestone)
    
    # Create income transaction
    new_tx = Transaction(
        user_id=current_user.id,
        client_id=milestone.client_id,
        milestone_id=milestone.id,
        amount=milestone.amount,
        type="income",
        category="Client Revenue",
        description=f"Payment for milestone: {milestone.title}",
        date=datetime.utcnow()
    )
    session.add(new_tx)
    try:
        session.commit()
    except Exception as e:
        print(f"DEBUG: Transaction failed: {e}")
        traceback.print_exc()
        session.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed")
    
    session.refresh(new_tx)
    print(f"DEBUG: Successfully logged transaction {new_tx.id}")
    return new_tx

# --- RECURRING EXPENSES ---
from schemas import RecurringExpenseCreate, RecurringExpenseRead

@app.post("/recurring-expenses", response_model=RecurringExpenseRead)
def create_recurring_expense(expense: RecurringExpenseCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_expense = RecurringExpense(**expense.dict(), user_id=current_user.id)
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense

@app.get("/recurring-expenses", response_model=List[RecurringExpenseRead])
def read_recurring_expenses(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return session.exec(select(RecurringExpense).where(RecurringExpense.user_id == current_user.id)).all()

@app.patch("/recurring-expenses/{expense_id}", response_model=RecurringExpenseRead)
def update_recurring_expense(expense_id: int, expense_update: RecurringExpenseCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_expense = session.exec(select(RecurringExpense).where(RecurringExpense.id == expense_id, RecurringExpense.user_id == current_user.id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    
    update_data = expense_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_expense, key, value)
    
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    return db_expense

@app.delete("/recurring-expenses/{expense_id}")
def delete_recurring_expense(expense_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_expense = session.exec(select(RecurringExpense).where(RecurringExpense.id == expense_id, RecurringExpense.user_id == current_user.id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    session.delete(db_expense)
    session.commit()
    return {"ok": True}

# --- EMPLOYEES ---
@app.post("/employees/", response_model=EmployeeRead)
def create_employee(employee: EmployeeCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_employee = Employee(**employee.dict(), user_id=current_user.id)
    session.add(db_employee)
    session.commit()
    session.refresh(db_employee)
    print(f"DEBUG: Created employee {db_employee.id}")
    return db_employee

@app.get("/employees/", response_model=List[EmployeeRead])
def read_employees(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    employees = session.exec(select(Employee).where(Employee.user_id == current_user.id)).all()
    return employees

@app.patch("/employees/{employee_id}", response_model=EmployeeRead)
def update_employee(employee_id: int, employee_update: EmployeeCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_employee = session.exec(select(Employee).where(Employee.id == employee_id, Employee.user_id == current_user.id)).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    update_data = employee_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_employee, key, value)
    
    session.add(db_employee)
    session.commit()
    session.refresh(db_employee)
    return db_employee

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_employee = session.exec(select(Employee).where(Employee.id == employee_id, Employee.user_id == current_user.id)).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    session.delete(db_employee)
    session.commit()
    return {"ok": True}

@app.post("/employees/{employee_id}/pay", response_model=TransactionRead)
def pay_employee_salary(employee_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    employee = session.exec(select(Employee).where(Employee.id == employee_id, Employee.user_id == current_user.id)).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Create expense transaction
    today = datetime.utcnow()
    month_year = today.strftime("%B %Y")
    new_tx = Transaction(
        user_id=current_user.id,
        employee_id=employee.id,
        amount=employee.salary,
        type="expense",
        category="Salaries",
        description=f"Salary Payment - {employee.name} ({month_year})",
        date=today
    )
    session.add(new_tx)
    session.commit()
    session.refresh(new_tx)
    return new_tx

# --- TRANSACTIONS ---
@app.post("/transactions/", response_model=TransactionRead)
def create_transaction(transaction: TransactionCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_transaction = Transaction(**transaction.dict(), user_id=current_user.id)
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    print(f"DEBUG: Created transaction {db_transaction.id}")
    return db_transaction

@app.get("/transactions/", response_model=List[TransactionRead])
def read_transactions(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    transactions = session.exec(select(Transaction).where(Transaction.user_id == current_user.id)).all()
    return transactions

@app.patch("/transactions/{transaction_id}", response_model=TransactionRead)
def update_transaction(transaction_id: int, transaction_update: TransactionCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_transaction = session.exec(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    update_data = transaction_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    return db_transaction

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_transaction = session.exec(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    session.delete(db_transaction)
    session.commit()
    return {"ok": True}

@app.get("/dashboard-stats")
def get_dashboard_stats(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Trigger automation on dashboard load
    process_automation_for_user(session, current_user)
    
    now = datetime.utcnow()
    start_of_month = datetime(now.year, now.month, 1)
    
    # All transactions for history and trends
    all_transactions = session.exec(select(Transaction).where(Transaction.user_id == current_user.id)).all()
    
    # This month's data
    def ensure_dt(d):
        if isinstance(d, str):
            try: return datetime.fromisoformat(d.replace('Z', '+00:00'))
            except: return datetime.utcnow() # Fallback
        return d

    this_month_txs = [t for t in all_transactions if ensure_dt(t.date) >= start_of_month]
    total_income = sum(t.amount for t in this_month_txs if t.type == "income")
    total_expense = sum(t.amount for t in this_month_txs if t.type == "expense")
    net_position = total_income - total_expense
    
    # 1. CASH RUNWAY CALCULATION
    # Average burn from last 30 days
    last_30_days = now - timedelta(days=30)
    expenses_30d = sum(t.amount for t in all_transactions if t.type == "expense" and ensure_dt(t.date) >= last_30_days)
    daily_burn = expenses_30d / 30 if expenses_30d > 0 else 0
    runway_weeks = (current_user.bank_balance / (daily_burn * 7)) if daily_burn > 0 else 52 # Default to 52 weeks if no burn
    
    # 2. 6-MONTH TREND DATA
    trends = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=i*30)
        m_start = datetime(month_date.year, month_date.month, 1)
        if m_start.month == 12:
            m_next = datetime(m_start.year + 1, 1, 1)
        else:
            m_next = datetime(m_start.year, m_start.month + 1, 1)
        
        m_txs = [t for t in all_transactions if m_start <= ensure_dt(t.date) < m_next]
        m_inc = sum(t.amount for t in m_txs if t.type == "income")
        m_exp = sum(t.amount for t in m_txs if t.type == "expense")
        trends.append({
            "name": m_start.strftime("%b"),
            "income": m_inc,
            "expense": m_exp,
            "net": m_inc - m_exp
        })
        
    # 3. UPCOMING OBLIGATIONS (Next 30 Days)
    next_30_days = now + timedelta(days=30)
    pending_milestones = session.exec(select(Milestone).where(
        Milestone.user_id == current_user.id, 
        Milestone.status != "Paid",
        Milestone.due_date <= next_30_days
    )).all()
    
    recurring = session.exec(select(RecurringExpense).where(
        RecurringExpense.user_id == current_user.id,
        RecurringExpense.is_active == True,
        RecurringExpense.next_due_date <= next_30_days
    )).all()
    
    employees = session.exec(select(Employee).where(Employee.user_id == current_user.id)).all()
    # Check if salaries already paid this month
    paid_emp_ids = [t.employee_id for t in this_month_txs if t.type == "expense" and t.employee_id]
    unpaid_employees = [e for e in employees if e.id not in paid_emp_ids]
    
    obligations = []
    for m in pending_milestones: 
        obligations.append({"title": m.title, "amount": m.amount, "date": m.due_date, "type": "receivable"})
    for r in recurring:
        obligations.append({"title": r.title, "amount": r.amount, "date": r.next_due_date, "type": "payable"})
    for e in unpaid_employees:
        # Salary is due end of month
        sal_date = datetime(now.year, now.month, 28) # simpler logic
        obligations.append({"title": f"Salary: {e.name}", "amount": e.salary, "date": sal_date, "type": "payable"})
    
    # Sort obligations by date
    obligations.sort(key=lambda x: x["date"])

    return {
        "net_position": net_position,
        "total_income": total_income,
        "total_expense": total_expense,
        "currency": current_user.currency,
        "period_name": now.strftime("%B %Y"),
        "bank_balance": current_user.bank_balance,
        "runway_weeks": round(runway_weeks, 1),
        "trends": trends,
        "obligations": obligations[:5], # Top 5 nearest
        "paid_employee_ids": list(set(paid_emp_ids))
    }

# --- WHATSAPP WEBHOOK ---
@app.get("/webhook")
async def verify_webhook(request: Request):
    # Meta WhatsApp Cloud API verification
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")
    
    VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "zetamize_secret_token")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        from fastapi.responses import Response
        return Response(content=challenge)
    return HTTPException(status_code=403, detail="Verification failed")

@app.post("/webhook")
async def handle_whatsapp_message(request: Request, session: Session = Depends(get_session)):
    body = await request.json()
    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        message_data = value.get("messages", [{}])[0]
        
        sender_number = message_data.get("from")
        message_text = message_data.get("text", {}).get("body", "")
        
        if not sender_number or not message_text:
            return {"status": "ignored"}
            
        user = session.exec(select(User).where(User.whatsapp_number == sender_number)).first()
        if not user:
            return {"status": "user_not_found"}
            
        result = parse_whatsapp_message(message_text, user, session)
        
        if result:
            if "query_result" in result:
                pass
            elif "type" in result:
                new_transaction = Transaction(
                    user_id=user.id,
                    amount=result["amount"],
                    category=result["category"],
                    description=result["description"],
                    type=result["type"],
                    client_id=result.get("client_id"),
                    employee_id=result.get("employee_id")
                )
                session.add(new_transaction)
                session.commit()
        
        return {"status": "success"}
    except Exception as e:
        print(f"Error processing WhatsApp message: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)