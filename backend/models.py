from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password_hash: str
    business_name: str
    industry: str
    currency: str = Field(default="PKR")
    whatsapp_number: Optional[str] = Field(unique=True, index=True)
    bank_balance: float = Field(default=0.0) # [New] for Runway calculation
    
    clients: List["Client"] = Relationship(back_populates="user")
    employees: List["Employee"] = Relationship(back_populates="user")
    transactions: List["Transaction"] = Relationship(back_populates="user")
    milestones: List["Milestone"] = Relationship(back_populates="user")
    recurring_expenses: List["RecurringExpense"] = Relationship(back_populates="user")

class Client(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    contract_value: float
    payment_terms: str
    status: str = Field(default="Active") # Active, Paused, Completed
    
    user: User = Relationship(back_populates="clients")
    transactions: List["Transaction"] = Relationship(back_populates="client")
    milestones: List["Milestone"] = Relationship(back_populates="client")

class Employee(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    role: str
    salary: float
    join_date: datetime = Field(default_factory=datetime.utcnow)
    
    user: User = Relationship(back_populates="employees")
    transactions: List["Transaction"] = Relationship(back_populates="employee")

class Milestone(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    client_id: int = Field(foreign_key="client.id")
    title: str
    amount: float
    due_date: datetime
    status: str = Field(default="Pending") # Pending, Paid, Partial, Overdue, Disputed, Advance
    
    user: User = Relationship(back_populates="milestones")
    client: Client = Relationship(back_populates="milestones")

class RecurringExpense(SQLModel, table=True): # [New] v2
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    title: str # e.g. Rent, Adobe Sub
    amount: float
    category: str # Marketing, Rent, Software
    frequency: str # monthly, weekly
    next_due_date: datetime
    is_active: bool = Field(default=True)
    
    user: User = Relationship(back_populates="recurring_expenses")

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    employee_id: Optional[int] = Field(default=None, foreign_key="employee.id")
    milestone_id: Optional[int] = Field(default=None, foreign_key="milestone.id")
    recurring_id: Optional[int] = Field(default=None, foreign_key="recurringexpense.id") # [New]
    date: datetime = Field(default_factory=datetime.utcnow)
    amount: float
    category: str
    description: str
    type: str # income, expense
    
    user: User = Relationship(back_populates="transactions")
    client: Optional[Client] = Relationship(back_populates="transactions")
    employee: Optional[Employee] = Relationship(back_populates="transactions")
