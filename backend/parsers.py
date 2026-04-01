import csv
import re
from io import StringIO
from datetime import datetime

def parse_meezan(text: str):
    """
    Meezan Bank Typical CSV Structure:
    Date, Voucher, Narration, Cheque, Withdrawal, Deposit, Balance
    """
    rows = []
    lines = text.splitlines()
    f = StringIO(text)
    reader = csv.reader(f)
    
    found_header = False
    for row in reader:
        if not row: continue
        if "Date" in row and "Narration" in row:
            found_header = True
            continue
        if not found_header: continue
        
        try:
            date_str = row[0].strip()
            description = row[2].strip()
            withdrawal = float(row[4].replace(',', '').strip() or 0)
            deposit = float(row[5].replace(',', '').strip() or 0)
            
            amount = deposit if deposit > 0 else -withdrawal
            if amount == 0: continue
            
            rows.append({
                "date": date_str,
                "description": description,
                "amount": amount
            })
        except:
            continue
    return rows

def parse_hbl(text: str):
    """
    HBL Typical CSV Structure:
    Date, Description, Ref, Withdrawal, Deposit, Balance
    """
    rows = []
    f = StringIO(text)
    reader = csv.reader(f)
    found_header = False
    for row in reader:
        if not row: continue
        if "Withdrawal" in row and "Deposit" in row:
            found_header = True
            continue
        if not found_header: continue
        
        try:
            date_str = row[0].strip()
            description = row[1].strip()
            withdrawal = float(row[3].replace(',', '').strip() or 0)
            deposit = float(row[4].replace(',', '').strip() or 0)
            amount = deposit if deposit > 0 else -withdrawal
            if amount == 0: continue
            rows.append({"date": date_str, "description": description, "amount": amount})
        except: continue
    return rows

def parse_nayapay(text: str):
    """
    Nayapay Typical Export:
    Date, Transaction ID, Type, Description, Amount, Status
    """
    rows = []
    f = StringIO(text)
    reader = csv.reader(f)
    for row in reader:
        if len(row) < 5: continue
        if "Nayapay" in row or "Date" in row: continue
        try:
            date_str = row[0].strip()
            description = f"{row[2]} - {row[3]}".strip()
            amount_str = row[4].replace(',', '').replace('PKR', '').strip()
            # If 'Type' is 'Spend' or 'Payment', make it negative
            amount = float(amount_str)
            if "Spend" in row[2] or "Payment" in row[2] or "Transfer" in row[2]:
                amount = -abs(amount)
            rows.append({"date": date_str, "description": description, "amount": amount})
        except: continue
    return rows

def parse_generic_bank(text: str):
    """
    Format: Booking Date,Value Date,Doc No,Description,Debit,Credit,Available Balance
    """
    rows = []
    f = StringIO(text)
    reader = csv.reader(f)
    found_header = False
    for row in reader:
        if not row: continue
        if "Booking Date" in row and "Description" in row and "Debit" in row:
            found_header = True
            continue
        if not found_header: continue
        if len(row) < 6: continue
        
        try:
            date_str = row[0].strip()
            description = row[3].strip()
            doc_no = row[2].strip()
            if doc_no:
                description = f"{doc_no} - {description}"
                
            withdrawal = float(row[4].replace(',', '').strip() or 0)
            deposit = float(row[5].replace(',', '').strip() or 0)
            
            amount = deposit if deposit > 0 else -withdrawal
            if amount == 0: continue
            
            rows.append({
                "date": date_str,
                "description": description,
                "amount": amount
            })
        except:
            continue
    return rows

def get_bank_parser(text: str):
    """
    Detect bank based on headers and return the appropriate function.
    """
    header_sample = text[:1000].lower()
    
    # Check for Meezan explicitly
    if ("date" in header_sample and "voucher" in header_sample and "cheque" in header_sample and "withdrawal" in header_sample):
        return parse_meezan
    
    # Generic bank format (Meezan export alternative)
    if "booking date" in header_sample and "doc no" in header_sample and "debit" in header_sample:
        return parse_generic_bank
        
    # HBL format
    if ("ref" in header_sample and "withdrawal" in header_sample and "deposit" in header_sample):
        return parse_hbl
        
    # NayaPay format
    if ("transaction id" in header_sample and "type" in header_sample and "status" in header_sample):
        return parse_nayapay
        
    return None
