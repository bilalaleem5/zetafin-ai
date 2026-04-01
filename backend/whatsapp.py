import re
from typing import Optional, Dict, Any
from models import Transaction, User, Client, Employee
from sqlmodel import Session, select
from datetime import datetime

def parse_whatsapp_message(message: str, user: User, session: Session) -> Optional[Dict[str, Any]]:
    """
    Parses structured WhatsApp commands and returns transaction data or query results.
    Formats:
    - INCOME: in [amount] [client] [description]
    - EXPENSE: ex [amount] [category] [description]
    - SALARY: salary [employee-name]
    - PAID: paid [client-name] [amount]
    - QUICK QUERIES: summary, pending, upcoming
    """
    message = message.strip().lower()
    
    # INCOME ENTRY: in [amount] [client/source] [description]
    # Supports: "in 50000 Ali March-inv", "in 50000 for Ali Traders Payment"
    match_in = re.match(r"^in\s+(\d+)\s+(?:for\s+)?([\w-]+)\s*(.*)$", message)
    if match_in:
        amount = float(match_in.group(1))
        client_name = match_in.group(2).replace("-", " ")
        description = match_in.group(3) or "Income entry"
        
        # Try to find client
        client = session.exec(select(Client).where(Client.user_id == user.id, Client.name.ilike(client_name))).first()
        
        return {
            "type": "income",
            "amount": amount,
            "category": "Client Revenue",
            "description": f"From {client_name}: {description}",
            "client_id": client.id if client else None,
            "confirmation": f"Income logged: {user.currency} {amount:,.0f} from {client_name} — {description}. Correct? Reply YES or EDIT."
        }

    # EXPENSE ENTRY: ex [amount] [category] [description]
    # Supports: "ex 8000 rent Office", "ex 1500 on Marketing Ads"
    match_ex = re.match(r"^ex\s+(\d+)\s+(?:on\s+)?([\w-]+)\s*(.*)$", message)
    if match_ex:
        amount = float(match_ex.group(1))
        category = match_ex.group(2).replace("-", " ")
        description = match_ex.group(3) or "Expense entry"
        
        return {
            "type": "expense",
            "amount": amount,
            "category": category.capitalize(),
            "description": description,
            "confirmation": f"Expense logged: {user.currency} {amount:,.0f} — {category.capitalize()} — {description}. Correct? Reply YES or EDIT."
        }

    # SALARY PAID: salary [employee-name]
    match_salary = re.match(r"^salary\s+([\w-]+)$", message)
    if match_salary:
        employee_name = match_salary.group(1).replace("-", " ")
        employee = session.exec(select(Employee).where(Employee.user_id == user.id, Employee.name.ilike(employee_name))).first()
        
        if not employee:
            return {"error": f"Employee {employee_name} not found."}
            
        return {
            "type": "expense",
            "amount": employee.salary,
            "category": "Salaries",
            "description": f"Salary for {employee.name}",
            "employee_id": employee.id,
            "confirmation": f"Salary marked paid for {employee.name} — {user.currency} {employee.salary:,.0f}. Logged."
        }

    # CLIENT PAID: paid [client-name] [amount]
    match_paid = re.match(r"^paid\s+([\w-]+)\s+(\d+)$", message)
    if match_paid:
        client_name = match_paid.group(1).replace("-", " ")
        amount = float(match_paid.group(2))
        client = session.exec(select(Client).where(Client.user_id == user.id, Client.name.ilike(client_name))).first()
        
        if not client:
            return {"error": f"Client {client_name} not found."}
            
        return {
            "type": "income",
            "amount": amount,
            "category": "Client Revenue",
            "description": f"Payment from {client.name}",
            "client_id": client.id,
            "confirmation": f"Payment of {user.currency} {amount:,.0f} received from {client.name}. Outstanding balance updated."
        }

    # QUERIES
    if message == "summary":
        # Calculate summary logic
        transactions = session.exec(select(Transaction).where(Transaction.user_id == user.id, Transaction.date >= datetime.utcnow().replace(day=1))).all()
        income = sum(t.amount for t in transactions if t.type == "income")
        expense = sum(t.amount for t in transactions if t.type == "expense")
        net = income - expense
        
        return {
            "query_result": True,
            "text": f"This month: Income {user.currency} {income:,.0f} | Expenses {user.currency} {expense:,.0f} | Net {user.currency} {net:,.0f}."
        }

    return None

import os
import httpx

async def send_whatsapp_message(to_number: str, text: str):
    """
    Sends a message via Meta WhatsApp Cloud API.
    Uses environment variables for credentials.
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_ID") # User must provide this
    
    if not access_token or not phone_number_id:
        print("DEBUG: WhatsApp credentials missing. Cannot send message.")
        return False
        
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {"body": text}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code in [200, 201]:
                return True
            else:
                print(f"DEBUG: WhatsApp send failed: {resp.text}")
                return False
        except Exception as e:
            print(f"DEBUG: WhatsApp error: {e}")
            return False
