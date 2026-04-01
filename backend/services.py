from sqlmodel import Session, select
from datetime import datetime, timedelta
from models import Transaction, RecurringExpense, Milestone, User, VendorBill
import traceback

def process_automation_for_user(session: Session, user: User):
    """
    Main automation entry point for a user.
    - Processes recurring expenses.
    - Updates milestone overdue statuses.
    """
def ensure_dt(d):
    if isinstance(d, str):
        try: return datetime.fromisoformat(d.replace('Z', '+00:00'))
        except: return datetime.utcnow()
    return d

def process_automation_for_user(session: Session, user: User):
    """
    Main automation entry point for a user.
    """
    now = datetime.utcnow()
    
    # 1. RECURRING EXPENSES
    # Fetch all active and filter in memory to handle SQLite strings safely
    all_recurring = session.exec(select(RecurringExpense).where(
        RecurringExpense.user_id == user.id,
        RecurringExpense.is_active == True
    )).all()
    
    recurring = [r for r in all_recurring if ensure_dt(r.next_due_date) <= now]
    
    for r in recurring:
        try:
            # Create the transaction
            new_tx = Transaction(
                user_id=user.id,
                recurring_id=r.id,
                amount=r.amount,
                type="expense",
                category=r.category,
                description=f"Automated: {r.title}",
                date=r.next_due_date # Log on the date it was due
            )
            session.add(new_tx)
            
            # Update next due date
            current_due = ensure_dt(r.next_due_date)
            if r.frequency == "monthly":
                r.next_due_date = current_due + timedelta(days=30)
            elif r.frequency == "weekly":
                r.next_due_date = current_due + timedelta(days=7)
            
            session.add(r)
        except Exception as e:
            print(f"Error processing recurring expense {r.id}: {e}")
            traceback.print_exc()

    # 2. MILESTONE OVERDUE CHECK
    all_milestones = session.exec(select(Milestone).where(
        Milestone.user_id == user.id,
        Milestone.status == "Pending"
    )).all()
    
    milestones = [m for m in all_milestones if ensure_dt(m.due_date) < now]
    
    for m in milestones:
        m.status = "Overdue"
        session.add(m)

    # 3. VENDOR BILL OVERDUE CHECK
    all_vendor_bills = session.exec(select(VendorBill).where(
        VendorBill.user_id == user.id,
        VendorBill.status == "Pending"
    )).all()
    
    vendor_bills = [b for b in all_vendor_bills if ensure_dt(b.due_date) < now]
    for b in vendor_bills:
        b.status = "Overdue"
        session.add(b)

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error committing automation tasks: {e}")
