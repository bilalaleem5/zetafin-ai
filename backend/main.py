from fastapi import FastAPI, Depends, HTTPException, status, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from typing import List
import uvicorn
import traceback
import os
import csv
import json
import httpx
from io import StringIO
from datetime import datetime

from database import engine, get_session, create_db_and_tables
from models import User, Client, Employee, Transaction, Milestone, RecurringExpense, Vendor, VendorBill, AuditLog, Budget
from ai_consultant import query_ai_insights, log_audit, get_ceo_summary
from schemas import (
    UserCreate, UserRead, Token, 
    ClientCreate, ClientRead, 
    EmployeeCreate, EmployeeRead, 
    TransactionCreate, TransactionRead,
    MilestoneCreate, MilestoneRead,
    RecurringExpenseCreate, RecurringExpenseRead,
    VendorCreate, VendorRead, VendorBillBase, VendorBillCreate, VendorBillRead,
    BalanceUpdate, AuditLogRead, BudgetRead, BudgetCreate
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
    old_data = db_client.model_dump()
    for key, value in update_data.items():
        setattr(db_client, key, value)
    
    session.add(db_client)
    session.commit()
    session.refresh(db_client)
    log_audit(session, current_user.id, "EDIT", "Client", db_client.id, old_val=old_data, new_val=db_client.model_dump())
    return db_client

@app.delete("/clients/{client_id}")
def delete_client(client_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_client = session.exec(select(Client).where(Client.id == client_id, Client.user_id == current_user.id)).first()
    if not db_client:
        raise HTTPException(status_code=404, detail="Client not found")
    # Also delete associated milestones and transactions to maintain integrity
    old_data = db_client.model_dump()
    session.delete(db_client)
    session.commit()
    log_audit(session, current_user.id, "DELETE", "Client", client_id, old_val=old_data)
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
    old_data = db_milestone.model_dump()
    for key, value in update_data.items():
        setattr(db_milestone, key, value)
    
    session.add(db_milestone)
    session.commit()
    session.refresh(db_milestone)
    log_audit(session, current_user.id, "EDIT", "Milestone", db_milestone.id, old_val=old_data, new_val=db_milestone.model_dump())
    return db_milestone

@app.delete("/milestones/{milestone_id}")
def delete_milestone(milestone_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_milestone = session.exec(select(Milestone).where(Milestone.id == milestone_id, Milestone.user_id == current_user.id)).first()
    if not db_milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")
    old_data = db_milestone.model_dump()
    session.delete(db_milestone)
    session.commit()
    log_audit(session, current_user.id, "DELETE", "Milestone", milestone_id, old_val=old_data)
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
    
    net_amount = milestone.amount - milestone.tax_amount
    new_tx = Transaction(
        user_id=current_user.id,
        client_id=milestone.client_id,
        milestone_id=milestone.id,
        amount=net_amount,
        tax_amount=milestone.tax_amount,
        tax_type=milestone.tax_type,
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
    old_data = db_expense.model_dump()
    for key, value in update_data.items():
        setattr(db_expense, key, value)
    
    session.add(db_expense)
    session.commit()
    session.refresh(db_expense)
    log_audit(session, current_user.id, "EDIT", "RecurringExpense", db_expense.id, old_val=old_data, new_val=db_expense.model_dump())
    return db_expense

@app.delete("/recurring-expenses/{expense_id}")
def delete_recurring_expense(expense_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_expense = session.exec(select(RecurringExpense).where(RecurringExpense.id == expense_id, RecurringExpense.user_id == current_user.id)).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Recurring expense not found")
    old_data = db_expense.model_dump()
    session.delete(db_expense)
    session.commit()
    log_audit(session, current_user.id, "DELETE", "RecurringExpense", expense_id, old_val=old_data)
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
    old_data = db_employee.model_dump()
    for key, value in update_data.items():
        setattr(db_employee, key, value)
    
    session.add(db_employee)
    session.commit()
    session.refresh(db_employee)
    log_audit(session, current_user.id, "EDIT", "Employee", db_employee.id, old_val=old_data, new_val=db_employee.model_dump())
    return db_employee

@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_employee = session.exec(select(Employee).where(Employee.id == employee_id, Employee.user_id == current_user.id)).first()
    if not db_employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    old_data = db_employee.model_dump()
    session.delete(db_employee)
    session.commit()
    log_audit(session, current_user.id, "DELETE", "Employee", employee_id, old_val=old_data)
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

# --- VENDORS ---
@app.post("/vendors/", response_model=VendorRead)
def create_vendor(vendor: VendorCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_vendor = Vendor(**vendor.dict(), user_id=current_user.id)
    session.add(db_vendor)
    session.commit()
    session.refresh(db_vendor)
    
    # If opening balance, create a dummy bill or just a transaction?
    # User might want to track this as a starting point.
    if db_vendor.opening_balance > 0:
        initial_bill = VendorBill(
            user_id=current_user.id,
            vendor_id=db_vendor.id,
            title="Opening Balance / Initial Debt",
            amount=db_vendor.opening_balance,
            due_date=datetime.utcnow(),
            status="Pending"
        )
        session.add(initial_bill)
        session.commit()
        
    return db_vendor

@app.get("/vendors/")
def get_vendors(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    statement = select(Vendor).where(Vendor.user_id == current_user.id)
    vendors = session.exec(statement).all()
    
    results = []
    for v in vendors:
        # Calculate totals
        bills_statement = select(VendorBill).where(VendorBill.vendor_id == v.id)
        bills = session.exec(bills_statement).all()
        total_paid = sum(b.amount for b in bills if b.status == "Paid")
        total_outstanding = sum(b.amount for b in bills if b.status != "Paid")
        
        v_dict = v.model_dump()
        v_dict["total_paid"] = total_paid
        v_dict["total_outstanding"] = total_outstanding
        results.append(v_dict)
        
    return results

@app.patch("/vendors/{vendor_id}", response_model=VendorRead)
def update_vendor(vendor_id: int, vendor_update: VendorCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_vendor = session.exec(select(Vendor).where(Vendor.id == vendor_id, Vendor.user_id == current_user.id)).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    update_data = vendor_update.dict(exclude_unset=True)
    old_data = db_vendor.model_dump()
    for key, value in update_data.items():
        setattr(db_vendor, key, value)
    
    session.add(db_vendor)
    session.commit()
    session.refresh(db_vendor)
    log_audit(session, current_user.id, "EDIT", "Vendor", db_vendor.id, old_val=old_data, new_val=db_vendor.model_dump())
    return db_vendor

@app.delete("/vendors/{vendor_id}")
def delete_vendor(vendor_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_vendor = session.exec(select(Vendor).where(Vendor.id == vendor_id, Vendor.user_id == current_user.id)).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    old_data = db_vendor.model_dump()
    session.delete(db_vendor)
    session.commit()
    log_audit(session, current_user.id, "DELETE", "Vendor", vendor_id, old_val=old_data)
    return {"ok": True}

# --- VENDOR BILLS ---
@app.post("/vendors/{vendor_id}/bills/", response_model=VendorBillRead)
def create_vendor_bill(vendor_id: int, bill: VendorBillCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_vendor = session.exec(select(Vendor).where(Vendor.id == vendor_id, Vendor.user_id == current_user.id)).first()
    if not db_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    # ensure bill's vendor matches url param, or trust the url param
    bill_data = bill.dict()
    bill_data["vendor_id"] = vendor_id
    db_bill = VendorBill(**bill_data, user_id=current_user.id)
    session.add(db_bill)
    session.commit()
    session.refresh(db_bill)
    return db_bill

@app.get("/vendors/{vendor_id}/bills/", response_model=List[VendorBillRead])
def read_vendor_bills(vendor_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return session.exec(select(VendorBill).where(VendorBill.vendor_id == vendor_id, VendorBill.user_id == current_user.id)).all()

@app.patch("/vendor-bills/{bill_id}", response_model=VendorBillRead)
def update_vendor_bill(bill_id: int, bill_update: VendorBillBase, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_bill = session.exec(select(VendorBill).where(VendorBill.id == bill_id, VendorBill.user_id == current_user.id)).first()
    if not db_bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    
    update_data = bill_update.dict(exclude_unset=True)
    old_data = db_bill.model_dump()
    for key, value in update_data.items():
        setattr(db_bill, key, value)
    
    session.add(db_bill)
    session.commit()
    session.refresh(db_bill)
    log_audit(session, current_user.id, "EDIT", "VendorBill", db_bill.id, old_val=old_data, new_val=db_bill.model_dump())
    return db_bill

@app.delete("/vendor-bills/{bill_id}")
def delete_vendor_bill(bill_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_bill = session.exec(select(VendorBill).where(VendorBill.id == bill_id, VendorBill.user_id == current_user.id)).first()
    if not db_bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    old_data = db_bill.model_dump()
    session.delete(db_bill)
    session.commit()
    log_audit(session, current_user.id, "DELETE", "VendorBill", bill_id, old_val=old_data)
    return {"ok": True}

@app.post("/vendor-bills/{bill_id}/pay", response_model=TransactionRead)
def pay_vendor_bill(bill_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    bill = session.exec(select(VendorBill).where(VendorBill.id == bill_id, VendorBill.user_id == current_user.id)).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    if bill.status == "Paid":
        raise HTTPException(status_code=400, detail="Bill already paid")
    
    bill.status = "Paid"
    session.add(bill)
    
    # Create expense transaction
    vendor = session.exec(select(Vendor).where(Vendor.id == bill.vendor_id)).first()
    
    net_amount = bill.amount - bill.tax_amount
    new_tx = Transaction(
        user_id=current_user.id,
        vendor_id=bill.vendor_id,
        vendor_bill_id=bill.id,
        amount=net_amount,
        tax_amount=bill.tax_amount,
        tax_type=bill.tax_type,
        type="expense",
        category="Accounts Payable",
        description=f"Bill Payment: {vendor.name} - {bill.title}",
        date=datetime.utcnow()
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
    old_data = db_transaction.model_dump()
    for key, value in update_data.items():
        setattr(db_transaction, key, value)
    
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)
    log_audit(session, current_user.id, "EDIT", "Transaction", db_transaction.id, old_val=old_data, new_val=db_transaction.model_dump())
    return db_transaction

@app.delete("/transactions/{transaction_id}")
def delete_transaction(transaction_id: int, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    db_transaction = session.exec(select(Transaction).where(Transaction.id == transaction_id, Transaction.user_id == current_user.id)).first()
    if not db_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    old_data = db_transaction.model_dump()
    session.delete(db_transaction)
    session.commit()
    log_audit(session, current_user.id, "DELETE", "Transaction", transaction_id, old_val=old_data)
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

@app.get("/metadata/categories")
def get_categories(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Fetch unique categories from multiple sources
    tx_cats = session.exec(select(Transaction.category).where(Transaction.user_id == current_user.id)).all()
    rec_cats = session.exec(select(RecurringExpense.category).where(RecurringExpense.user_id == current_user.id)).all()
    vendor_cats = session.exec(select(Vendor.category).where(Vendor.user_id == current_user.id)).all()
    
    all_cats = set(tx_cats + rec_cats + vendor_cats)
    
    # Defaults
    defaults = ['Software', 'Hardware', 'Marketing', 'Office Supplies', 'Legal', 'Contractor', 'Rent', 'Salaries', 'Utilities', 'Operations', 'Travel', 'Miscellaneous', 'Client Revenue']
    all_cats.update(defaults)
    
    return sorted(list(filter(None, all_cats)))

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

# --- REPORTS ---
import io
@app.get("/reports/pnl")
def get_pnl_report(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    txs = session.exec(select(Transaction).where(Transaction.user_id == current_user.id)).all()
    income_by_category = {}
    expense_by_category = {}
    total_in = 0
    total_out = 0
    
    for t in txs:
        if t.type == "income":
            total_in += t.amount
            income_by_category[t.category] = income_by_category.get(t.category, 0) + t.amount
        else:
            total_out += t.amount
            expense_by_category[t.category] = expense_by_category.get(t.category, 0) + t.amount

    return {
        "total_income": total_in,
        "total_expense": total_out,
        "net_profit": total_in - total_out,
        "income_breakdown": [{"category": k, "amount": v} for k,v in income_by_category.items()],
        "expense_breakdown": [{"category": k, "amount": v} for k,v in expense_by_category.items()],
    }

@app.get("/reports/export")
def export_transactions(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    txs = session.exec(select(Transaction).where(Transaction.user_id == current_user.id).order_by(Transaction.date.desc())).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Date", "Description", "Category", "Type", "Net Amount", "Tax Withheld", "Tax Type"])
    
    for t in txs:
        writer.writerow([
            t.id, 
            t.date.strftime("%Y-%m-%d %H:%M:%S"),
            t.description,
            t.category,
            t.type,
            t.amount,
            t.tax_amount or 0,
            t.tax_type or "None"
        ])
    
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=zetafin_transactions.csv"})
# --- AI PARSING CONFIG ---
import os
from dotenv import load_dotenv
load_dotenv()
XAI_KEY = os.getenv("XAI_KEY", "")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY", "")

async def fetch_ai_parsing(csv_text: str):
    # Try xAI (Primary)
    xai_url = "https://api.x.ai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {XAI_KEY}", "Content-Type": "application/json"}
    
    prompt = f"""
    Extract all transactions from this CSV bank statement. Skip metadata rows.
    CSV:
    {csv_text[:18000]}
    
    Return ONLY JSON: {{"transactions": [[date, description, amount], ...]}}
    JSON:
    """
    
    async with httpx.AsyncClient() as client:
        # 1. ATTEMPT X.AI
        try:
            resp = await client.post(xai_url, json={"model": "grok-beta", "messages": [{"role": "user", "content": prompt}]}, headers=headers, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                if "```json" in content: content = content.split("```json")[1].split("```")[0].strip()
                raw_data = json.loads(content)
                txs = []
                for i, tx in enumerate(raw_data.get("transactions", [])):
                    if isinstance(tx, (list, tuple)) and len(tx) >= 3:
                        try:
                            txs.append({
                                "id": i + 1,
                                "date": str(tx[0]),
                                "description": str(tx[1]),
                                "amount": float(tx[2])
                            })
                        except: continue
                return {"transactions": txs}
        except Exception as e:
            print(f"xAI error: {e}")

        # 2. ATTEMPT OPENROUTER (Backup)
        or_url = "https://openrouter.ai/api/v1/chat/completions"
        or_headers = {"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"}
        try:
            resp = await client.post(or_url, json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "response_format": {"type": "json_object"}}, headers=or_headers, timeout=30.0)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                raw_data = json.loads(content)
                txs = []
                for i, tx in enumerate(raw_data.get("transactions", [])):
                    if isinstance(tx, (list, tuple)) and len(tx) >= 3:
                        try:
                            txs.append({
                                "id": i + 1,
                                "date": str(tx[0]),
                                "description": str(tx[1]),
                                "amount": float(tx[2])
                            })
                        except: continue
                return {"transactions": txs}
        except Exception as e:
            print(f"OpenRouter error: {e}")
            
    return None

# --- RECONCILIATION ---
@app.post("/reconciliation/upload")
async def upload_bank_statement(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    content = await file.read()
    # Try UTF-8 with BOM signature handling first, then fallback
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")
    
    # TRY AI PARSING FIRST
    ai_result = await fetch_ai_parsing(text)
    if ai_result and ai_result.get("transactions"):
        return ai_result

    # FALLBACK: Standardize headers (case-insensitive, strip whitespace)
    header_map = {
        'date': ['date', 'txn date', 'transaction date', 'value date', 'booking date', 'txndate', 't_date'],
        'description': ['description', 'particulars', 'details', 'narrative', 'remarks', 'desc', 'transaction details'],
        'debit': ['debit', 'withdrawal', 'out', 'dr', 'withdrawal amount'],
        'credit': ['credit', 'deposit', 'in', 'cr', 'deposit amount'],
        'amount': ['amount', 'txn amount', 'total', 'amt', 'balance', 'available balance']
    }
    
    def find_col(row_keys, target):
        options = header_map.get(target, [])
        for opt in options:
            for k in row_keys:
                if opt in k.lower().strip(): return k
        return None

    # Robust CSV parsing
    try:
        lines = text.splitlines()
        # Skip junk rows at the start (metadata like account numbers, opening balances)
        header_index = 0
        for i, line in enumerate(lines[:15]): # Check first 15 lines
            sample_keys = [k.lower().strip() for k in line.split(',')]
            # If line has at least 2 distinct keys from our map, it's likely the header
            matches = 0
            for cat, opts in header_map.items():
                if any(opt in " ".join(sample_keys) for opt in opts):
                    matches += 1
            if matches >= 3: # Found it
                header_index = i
                break
        
        valid_text = "\n".join(lines[header_index:])
        reader = csv.DictReader(StringIO(valid_text))
        parsed_rows = []
        for row in reader:
            row_keys = list(row.keys())
            # Handle potential leading/trailing spaces in keys
            row = { (k.strip() if k else ""): v for k, v in row.items() }
            row_keys = list(row.keys())

            date_key = find_col(row_keys, 'date')
            desc_key = find_col(row_keys, 'description')
            debit_key = find_col(row_keys, 'debit')
            credit_key = find_col(row_keys, 'credit')
            amt_key = find_col(row_keys, 'amount')
            
            date_val = row.get(date_key, '') if date_key else ''
            desc_val = row.get(desc_key, '') if desc_key else ''
            
            if not date_val and not desc_val: continue
            
            try:
                def clean_float(val):
                    if not val: return 0
                    # Remove currency symbols, commas, and handle whitespace
                    cleaned = str(val).replace(',', '').replace('PKR', '').replace('RS', '').strip()
                    return float(cleaned) if cleaned else 0

                d_amt = clean_float(row.get(debit_key, '0')) if debit_key else 0
                c_amt = clean_float(row.get(credit_key, '0')) if credit_key else 0
                
                amount = c_amt - d_amt
                # If credit/debit logic results in 0, fallback to amount column
                # but AVOID using "Balance" as an amount
                if amount == 0 and amt_key and 'balance' not in amt_key.lower():
                    amount = clean_float(row.get(amt_key, '0'))
                
                if amount != 0:
                    parsed_rows.append({
                        "id": len(parsed_rows) + 1,
                        "date": date_val,
                        "description": desc_val,
                        "amount": amount
                    })
            except:
                continue
        return {"transactions": parsed_rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse CSV: {str(e)}")

# --- AI INSIGHTS ---
@app.post("/ai/query")
async def ai_query(request: Request, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    body = await request.json()
    query = body.get("query")
    if not query: raise HTTPException(status_code=400, detail="Missing query")
    answer = await query_ai_insights(query, session, current_user.id)
    return {"answer": answer}

@app.get("/ai/ceo-summary")
def ai_summary(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return get_ceo_summary(session, current_user.id)

# --- BUDGETS ---
@app.get("/budgets", response_model=List[BudgetRead])
def get_budgets(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return session.exec(select(Budget).where(Budget.user_id == current_user.id)).all()

@app.post("/budgets", response_model=BudgetRead)
def create_budget(budget: BudgetCreate, current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    # Check if exists for month/category
    existing = session.exec(select(Budget).where(
        Budget.user_id == current_user.id,
        Budget.category == budget.category,
        Budget.month == budget.month
    )).first()
    
    if existing:
        existing.amount = budget.amount
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
        
    db_budget = Budget(**budget.dict(), user_id=current_user.id)
    session.add(db_budget)
    session.commit()
    session.refresh(db_budget)
    return db_budget

# --- AUDIT LOGS ---
@app.get("/audit-logs", response_model=List[AuditLogRead])
def get_audit_logs(current_user: User = Depends(get_current_user), session: Session = Depends(get_session)):
    return session.exec(select(AuditLog).where(AuditLog.user_id == current_user.id).order_by(AuditLog.timestamp.desc()).limit(100)).all()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)