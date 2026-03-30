from sqlmodel import SQLModel
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    business_name: str
    industry: str
    currency: str = "PKR"
    whatsapp_number: Optional[str] = None
    bank_balance: float = 0.0

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class ClientBase(BaseModel):
    name: str
    contract_value: float
    payment_terms: str
    status: str = "Active"

class ClientCreate(ClientBase):
    pass

class ClientRead(ClientBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True

class MilestoneBase(BaseModel):
    title: str
    amount: float
    due_date: datetime
    status: str = "Pending"

class MilestoneCreate(MilestoneBase):
    pass

class MilestoneRead(MilestoneBase):
    id: int
    client_id: int
    user_id: int

    class Config:
        from_attributes = True

class EmployeeBase(BaseModel):
    name: str
    role: str
    salary: float

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeRead(EmployeeBase):
    id: int
    user_id: int
    join_date: datetime

    class Config:
        from_attributes = True

class RecurringExpenseBase(BaseModel):
    title: str
    amount: float
    category: str
    frequency: str # monthly, weekly
    next_due_date: datetime
    is_active: bool = True

class RecurringExpenseCreate(RecurringExpenseBase):
    pass

class RecurringExpenseRead(RecurringExpenseBase):
    id: int
    user_id: int

class BalanceUpdate(SQLModel):
    balance: float

    class Config:
        from_attributes = True

class TransactionBase(BaseModel):
    amount: float
    category: str
    description: str
    type: str
    date: datetime = datetime.utcnow()
    client_id: Optional[int] = None
    employee_id: Optional[int] = None
    milestone_id: Optional[int] = None
    recurring_id: Optional[int] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionRead(TransactionBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True
