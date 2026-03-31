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
    vendors: List["Vendor"] = Relationship(back_populates="user")
    vendor_bills: List["VendorBill"] = Relationship(back_populates="user")

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
    tax_amount: float = Field(default=0.0)
    tax_type: Optional[str] = Field(default=None) # e.g. WHT, GST
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

class Vendor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    name: str
    category: str
    contact: Optional[str] = Field(default=None)
    status: str = Field(default="Active") # Active, Inactive
    
    user: User = Relationship(back_populates="vendors")
    vendor_bills: List["VendorBill"] = Relationship(back_populates="vendor")
    transactions: List["Transaction"] = Relationship(back_populates="vendor")

class VendorBill(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    vendor_id: int = Field(foreign_key="vendor.id")
    title: str
    amount: float
    tax_amount: float = Field(default=0.0)
    tax_type: Optional[str] = Field(default=None)
    due_date: datetime
    status: str = Field(default="Pending") # Pending, Paid, Partial, Overdue

    user: User = Relationship(back_populates="vendor_bills")
    vendor: Vendor = Relationship(back_populates="vendor_bills")

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    client_id: Optional[int] = Field(default=None, foreign_key="client.id")
    employee_id: Optional[int] = Field(default=None, foreign_key="employee.id")
    milestone_id: Optional[int] = Field(default=None, foreign_key="milestone.id")
    recurring_id: Optional[int] = Field(default=None, foreign_key="recurringexpense.id") # [New]
    vendor_id: Optional[int] = Field(default=None, foreign_key="vendor.id")
    vendor_bill_id: Optional[int] = Field(default=None, foreign_key="vendorbill.id")
    date: datetime = Field(default_factory=datetime.utcnow)
    amount: float
    tax_amount: float = Field(default=0.0)
    tax_type: Optional[str] = Field(default=None)
    category: str
    description: str
    type: str # income, expense
    
    user: User = Relationship(back_populates="transactions")
    client: Optional[Client] = Relationship(back_populates="transactions")
    employee: Optional[Employee] = Relationship(back_populates="transactions")
    vendor: Optional[Vendor] = Relationship(back_populates="transactions")
