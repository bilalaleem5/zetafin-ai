"""
ZetaFin AI Consultant - 100% Local, Zero-Dependency Engine
No external API calls. Queries the database directly and generates
intelligent, language-adaptive responses in English and Roman Urdu.
"""
from sqlmodel import Session, select, func
from models import Transaction, Milestone, VendorBill, RecurringExpense, User, AuditLog, Budget, Client, Employee, Vendor
from datetime import datetime, timedelta
import json


# ─────────────────────────────────────────────
# UTILITY: Language Detection
# ─────────────────────────────────────────────
ROMAN_URDU_WORDS = {
    "kitna", "kya", "kahan", "kaun", "kab", "paisay", "paisa", "paise", "raqam",
    "batao", "bata", "dena", "diya", "aya", "aya", "milna", "mila", "lena", "total",
    "net", "position", "mera", "meri", "hamara", "hamari", "aapka", "aapki",
    "kitni", "kare", "kita", "hay", "hai", "ha", "tha", "thi", "hoga", "hogi",
    "abhi", "pehle", "baad", "kal", "aaj", "mahina", "saal", "hafta",
    "kharcha", "kamai", "aamdani", "balance", "kharch", "income",
    "jo", "ka", "ki", "ko", "se", "mein", "par", "yeh", "woh", "yar", "bhai",
    "check", "deko", "dekho", "btao", "batado"
}

def is_roman_urdu(query: str) -> bool:
    words = set(query.lower().split())
    return len(words & ROMAN_URDU_WORDS) >= 2


# ─────────────────────────────────────────────
# DATABASE SUMMARY FETCHER
# ─────────────────────────────────────────────
def get_ceo_summary(db: Session, user_id: int):
    user = db.get(User, user_id)
    balance = user.bank_balance if user else 0
    currency = user.currency if user else "PKR"

    receivables = db.exec(select(func.sum(Milestone.amount)).where(
        Milestone.user_id == user_id, Milestone.status != "Paid")).one() or 0

    payables = db.exec(select(func.sum(VendorBill.amount)).where(
        VendorBill.user_id == user_id, VendorBill.status != "Paid")).one() or 0

    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    burn = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.date >= thirty_days_ago)).one() or 0

    income_30d = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == "income",
        Transaction.date >= thirty_days_ago)).one() or 0

    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    expenses = db.exec(select(Transaction.category, func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id,
        Transaction.type == "expense",
        Transaction.date >= first_of_month
    ).group_by(Transaction.category)).all()
    actual_spending = {cat: amt for cat, amt in expenses}

    recent_txs = db.exec(select(Transaction).where(
        Transaction.user_id == user_id).order_by(Transaction.date.desc()).limit(20)).all()

    recent_audits = db.exec(select(AuditLog).where(
        AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).limit(10)).all()

    client_count = db.exec(select(func.count(Client.id)).where(Client.user_id == user_id)).one() or 0
    employee_count = db.exec(select(func.count(Employee.id)).where(Employee.user_id == user_id)).one() or 0
    vendor_count = db.exec(select(func.count(Vendor.id)).where(Vendor.user_id == user_id)).one() or 0

    total_income = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == "income")).one() or 0
    total_expense = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == "expense")).one() or 0

    return {
        "balance": balance, "receivables": receivables, "payables": payables,
        "monthly_burn": burn, "income_30d": income_30d,
        "net_position": total_income - total_expense,
        "total_income": total_income, "total_expense": total_expense,
        "actual_spending": actual_spending, "currency": currency,
        "recent_transactions": recent_txs,
        "recent_audits": recent_audits,
        "counts": {"clients": client_count, "employees": employee_count, "vendors": vendor_count}
    }


# ─────────────────────────────────────────────
# DEEP SEARCH: Find specific records by keyword
# ─────────────────────────────────────────────
def deep_search(query: str, db: Session, user_id: int):
    from sqlmodel import or_
    stop = {"how", "much", "tell", "from", "with", "this", "that", "show", "what",
            "where", "when", "paisa", "kitna", "aya", "tha", "diya", "ka", "ki",
            "ko", "se", "mein", "kya", "hai", "ha", "the", "for", "and", "net",
            "total", "position", "karo", "karna", "btao", "deko", "mera", "meri"}
    q = query.lower()
    keywords = [w.strip("?,.!") for w in q.split() if len(w) > 2 and w not in stop]
    results = []

    if not keywords:
        return results

    # Transactions
    tx_filters = [Transaction.description.ilike(f"%{w}%") for w in keywords]
    tx_filters += [Transaction.category.ilike(f"%{w}%") for w in keywords]
    txs = db.exec(select(Transaction).where(
        Transaction.user_id == user_id, or_(*tx_filters)
    ).order_by(Transaction.date.desc()).limit(20)).all()
    for t in txs:
        results.append(("tx", t))

    # Milestones
    mil_filters = [Milestone.title.ilike(f"%{w}%") for w in keywords]
    mils = db.exec(select(Milestone).where(
        Milestone.user_id == user_id, or_(*mil_filters)).limit(10)).all()
    for m in mils:
        results.append(("milestone", m))

    # Vendor Bills
    bill_filters = [VendorBill.title.ilike(f"%{w}%") for w in keywords]
    bills = db.exec(select(VendorBill).where(
        VendorBill.user_id == user_id, or_(*bill_filters)).limit(10)).all()
    for b in bills:
        results.append(("bill", b))

    # Clients
    client_filters = [Client.name.ilike(f"%{w}%") for w in keywords]
    clients = db.exec(select(Client).where(
        Client.user_id == user_id, or_(*client_filters)).limit(5)).all()
    for c in clients:
        # Get all transactions for this client
        client_txs = db.exec(select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.client_id == c.id
        ).order_by(Transaction.date.desc()).limit(10)).all()
        results.append(("client", c))
        for ct in client_txs:
            results.append(("client_tx", ct))

    # Employees
    emp_filters = [Employee.name.ilike(f"%{w}%") for w in keywords]
    emps = db.exec(select(Employee).where(
        Employee.user_id == user_id, or_(*emp_filters)).limit(5)).all()
    for e in emps:
        emp_txs = db.exec(select(Transaction).where(
            Transaction.user_id == user_id,
            Transaction.employee_id == e.id
        ).order_by(Transaction.date.desc()).limit(10)).all()
        results.append(("employee", e))
        for et in emp_txs:
            results.append(("emp_tx", et))

    # Vendors
    vendor_filters = [Vendor.name.ilike(f"%{w}%") for w in keywords]
    vendors = db.exec(select(Vendor).where(
        Vendor.user_id == user_id, or_(*vendor_filters)).limit(5)).all()
    for v in vendors:
        results.append(("vendor", v))

    # Audit Logs
    audit_filters = [AuditLog.table_name.ilike(f"%{w}%") for w in keywords]
    audit_filters += [AuditLog.action.ilike(f"%{w}%") for w in keywords]
    audits = db.exec(select(AuditLog).where(
        AuditLog.user_id == user_id, or_(*audit_filters)
    ).order_by(AuditLog.timestamp.desc()).limit(10)).all()
    for a in audits:
        results.append(("audit", a))

    return results


# ─────────────────────────────────────────────
# RESPONSE GENERATOR: Builds human-readable answers
# ─────────────────────────────────────────────
def build_response(query: str, summary: dict, search_results: list) -> str:
    q = query.lower()
    cur = summary["currency"]
    is_urdu = is_roman_urdu(q)

    def fmt(n):
        return f"{n:,.2f}"

    # ── INTENT: Net Position / Overall Financial Summary ──
    if any(w in q for w in ["net position", "net pos", "overall", "summary", "total position",
                              "financial position", "net", "position", "overview",
                              "total balance", "mukamal", "sara", "poora", "sab kuch"]):
        net = summary["net_position"]
        direction = "+" if net >= 0 else ""
        if is_urdu:
            return (f"📊 **Aapki Net Financial Position:**\n\n"
                    f"💰 Bank Balance: **{fmt(summary['balance'])} {cur}**\n"
                    f"📥 Receivables (Milne Wali Raqam): **{fmt(summary['receivables'])} {cur}**\n"
                    f"📤 Payables (Deny Wali Raqam): **{fmt(summary['payables'])} {cur}**\n"
                    f"📈 Total Income (Sab Waqt): **{fmt(summary['total_income'])} {cur}**\n"
                    f"📉 Total Expense (Sab Waqt): **{fmt(summary['total_expense'])} {cur}**\n"
                    f"🧾 **Net P&L: {direction}{fmt(net)} {cur}**\n\n"
                    f"{'✅ Profit mein hain!' if net >= 0 else '⚠️ Loss mein hain, kharcha zyada hai.'}")
        else:
            return (f"📊 **Your Complete Financial Position:**\n\n"
                    f"💰 Bank Balance: **{fmt(summary['balance'])} {cur}**\n"
                    f"📥 Receivables (Pending Income): **{fmt(summary['receivables'])} {cur}**\n"
                    f"📤 Payables (Bills Owed): **{fmt(summary['payables'])} {cur}**\n"
                    f"📈 Total Income (All Time): **{fmt(summary['total_income'])} {cur}**\n"
                    f"📉 Total Expenses (All Time): **{fmt(summary['total_expense'])} {cur}**\n"
                    f"🧾 **Net P&L: {direction}{fmt(net)} {cur}**\n\n"
                    f"{'✅ You are profitable!' if net >= 0 else '⚠️ Expenses exceed income — review spending.'}")

    # ── INTENT: Balance ──
    if any(w in q for w in ["balance", "bank", "account", "bakaya", "kitna pesa", "kitna paisa"]):
        if is_urdu:
            return f"💰 Aapka **Bank Balance {fmt(summary['balance'])} {cur}** hai."
        return f"💰 Your current **Bank Balance is {fmt(summary['balance'])} {cur}**."

    # ── INTENT: Income / Kamai ──
    if any(w in q for w in ["income", "kamai", "revenue", "earned", "mila", "aya", "received",
                              "total income", "kitni kamai"]):
        recent_income = [r for r in search_results if r[0] in ("tx", "client_tx") and r[1].type == "income"]
        if recent_income and any(w in q for w in ["from", "se", "ka", "ki", "naam"]):
            lines = []
            total = 0
            for _, t in recent_income[:10]:
                lines.append(f"  • {t.date.strftime('%d %b %Y')} — {t.description}: **{fmt(t.amount)} {cur}**")
                total += t.amount
            if is_urdu:
                return f"📥 **Matching Income Records:**\n\n" + "\n".join(lines) + f"\n\n💵 **Total: {fmt(total)} {cur}**"
            return f"📥 **Matching Income Records:**\n\n" + "\n".join(lines) + f"\n\n💵 **Total: {fmt(total)} {cur}**"
        if is_urdu:
            return (f"📥 **Income Summary:**\n"
                    f"• Pichle 30 Din: **{fmt(summary['income_30d'])} {cur}**\n"
                    f"• Sab Waqt Total: **{fmt(summary['total_income'])} {cur}**")
        return (f"📥 **Income Summary:**\n"
                f"• Last 30 Days: **{fmt(summary['income_30d'])} {cur}**\n"
                f"• All Time Total: **{fmt(summary['total_income'])} {cur}**")

    # ── INTENT: Expenses / Kharcha ──
    if any(w in q for w in ["expense", "kharcha", "kharch", "spent", "spend", "expenditure",
                              "cost", "burn", "burn rate", "kitna kharch", "kharcha kitna"]):
        spending = summary["actual_spending"]
        if spending:
            lines = [f"  • {cat}: **{fmt(amt)} {cur}**" for cat, amt in sorted(spending.items(), key=lambda x: -x[1])]
            if is_urdu:
                return (f"💸 **Is Mahine Ka Kharcha ({fmt(summary['monthly_burn'])} {cur} / 30 din):**\n\n"
                        + "\n".join(lines))
            return (f"💸 **This Month's Expenses ({fmt(summary['monthly_burn'])} {cur} / 30-day burn):**\n\n"
                    + "\n".join(lines))
        if is_urdu:
            return f"💸 Is mahine abhi tak koi kharcha nahi darz kiya. 30-din burn: **{fmt(summary['monthly_burn'])} {cur}**"
        return f"💸 No expenses recorded this month yet. 30-day burn: **{fmt(summary['monthly_burn'])} {cur}**"

    # ── INTENT: Receivables ──
    if any(w in q for w in ["receivable", "milne wali", "receive", "outstanding", "pending income",
                              "clients owe", "due from", "milne wala"]):
        pending_mils = [r for r in search_results if r[0] == "milestone"]
        if pending_mils:
            lines = [f"  • {m.title} — **{fmt(m.amount)} {cur}** ({m.status})" for _, m in pending_mils[:10]]
            if is_urdu:
                return f"📥 **Pending Milestones (Milne Wali Raqam):**\n\n" + "\n".join(lines) + f"\n\n💵 Total: **{fmt(summary['receivables'])} {cur}**"
            return f"📥 **Pending Milestones (Receivables):**\n\n" + "\n".join(lines) + f"\n\n💵 Total: **{fmt(summary['receivables'])} {cur}**"
        if is_urdu:
            return f"📥 Aapki total receivables: **{fmt(summary['receivables'])} {cur}**"
        return f"📥 Total Receivables: **{fmt(summary['receivables'])} {cur}**"

    # ── INTENT: Payables / Bills ──
    if any(w in q for w in ["payable", "dene wali", "bill", "vendor bill", "owed", "due to",
                              "outstanding payment", "dena hai"]):
        bills = [r for r in search_results if r[0] == "bill"]
        if bills:
            lines = [f"  • {b.title} — **{fmt(b.amount)} {cur}** ({b.status})" for _, b in bills[:10]]
            if is_urdu:
                return f"📤 **Pending Bills (Dene Wali Raqam):**\n\n" + "\n".join(lines) + f"\n\n💵 Total: **{fmt(summary['payables'])} {cur}**"
            return f"📤 **Pending Bills (Payables):**\n\n" + "\n".join(lines) + f"\n\n💵 Total: **{fmt(summary['payables'])} {cur}**"
        if is_urdu:
            return f"📤 Aapki total payables: **{fmt(summary['payables'])} {cur}**"
        return f"📤 Total Payables: **{fmt(summary['payables'])} {cur}**"

    # ── INTENT: Specific person/vendor search (pay from/to) ──
    if search_results:
        type_map = {"tx": "Transaction", "client_tx": "Client Tx", "emp_tx": "Employee Tx",
                    "milestone": "Milestone", "bill": "Bill", "client": "Client",
                    "employee": "Employee", "vendor": "Vendor", "audit": "System Log"}
        lines = []
        total_income_found = 0
        total_expense_found = 0

        for rtype, record in search_results[:15]:
            if rtype in ("tx", "client_tx", "emp_tx"):
                arrow = "📥" if record.type == "income" else "📤"
                lines.append(f"{arrow} {record.date.strftime('%d %b %Y')} | {record.description} | **{fmt(record.amount)} {cur}** ({record.type})")
                if record.type == "income":
                    total_income_found += record.amount
                else:
                    total_expense_found += record.amount
            elif rtype == "milestone":
                lines.append(f"🎯 Milestone: **{record.title}** | {fmt(record.amount)} {cur} | {record.status}")
            elif rtype == "bill":
                lines.append(f"🧾 Bill: **{record.title}** | {fmt(record.amount)} {cur} | {record.status}")
            elif rtype == "client":
                lines.append(f"👤 Client: **{record.name}** | Contract: {fmt(record.contract_value)} {cur} | {record.status}")
            elif rtype == "employee":
                lines.append(f"👨‍💼 Employee: **{record.name}** | Role: {record.role} | Salary: {fmt(record.salary)} {cur}")
            elif rtype == "vendor":
                lines.append(f"🏪 Vendor: **{record.name}** | Category: {record.category}")
            elif rtype == "audit":
                lines.append(f"🔍 Log: {record.timestamp.strftime('%d %b %Y %H:%M')} | {record.action} on {record.table_name}")

        out = "\n".join(lines)
        summary_line = ""
        if total_income_found > 0:
            summary_line += f"\n\n💵 **Total Received: {fmt(total_income_found)} {cur}**"
        if total_expense_found > 0:
            summary_line += f"\n💸 **Total Paid: {fmt(total_expense_found)} {cur}**"

        if is_urdu:
            return f"🔍 **Iss query se milte julte records:**\n\n{out}{summary_line}"
        return f"🔍 **Matching records found:**\n\n{out}{summary_line}"

    # ── INTENT: Recent transactions ──
    if any(w in q for w in ["recent", "last", "latest", "transactions", "history",
                              "pichli", "akhri", "purani", "log"]):
        txs = summary.get("recent_transactions", [])[:10]
        if txs:
            lines = []
            for t in txs:
                arrow = "📥" if t.type == "income" else "📤"
                lines.append(f"{arrow} {t.date.strftime('%d %b %Y')} | {t.description} | **{fmt(t.amount)} {cur}**")
            if is_urdu:
                return f"📋 **Aakhri Transactions:**\n\n" + "\n".join(lines)
            return f"📋 **Recent Transactions:**\n\n" + "\n".join(lines)

    # ── INTENT: Audit Log / System Activity ──
    if any(w in q for w in ["deleted", "edited", "updated", "changed", "who", "audit", "log",
                              "kisne", "delete", "edit", "badla", "activity", "history"]):
        audits = summary.get("recent_audits", [])[:10]
        if audits:
            lines = [f"🔍 {a.timestamp.strftime('%d %b %Y %H:%M')} | {a.action} on {a.table_name} (ID: {a.record_id})"
                     for a in audits]
            if is_urdu:
                return f"📜 **System Activity Log (Akhri Actions):**\n\n" + "\n".join(lines)
            return f"📜 **System Activity Log (Recent Actions):**\n\n" + "\n".join(lines)

    # ── INTENT: Clients / Employees / Vendors count ──
    if any(w in q for w in ["client", "customer", "grahak", "employee", "mulazim", "staff",
                              "vendor", "supplier", "how many", "kitne", "count", "total"]):
        c = summary["counts"]
        if is_urdu:
            return (f"👥 **Aapke System Mein:**\n"
                    f"• Clients: **{c['clients']}**\n"
                    f"• Employees: **{c['employees']}**\n"
                    f"• Vendors: **{c['vendors']}**")
        return (f"👥 **Your System Totals:**\n"
                f"• Clients: **{c['clients']}**\n"
                f"• Employees: **{c['employees']}**\n"
                f"• Vendors: **{c['vendors']}**")

    # ── FALLBACK: General dashboard summary ──
    if is_urdu:
        return (f"💼 **ZetaFin Dashboard Summary:**\n\n"
                f"💰 Balance: **{fmt(summary['balance'])} {cur}**\n"
                f"📥 Receivables: **{fmt(summary['receivables'])} {cur}**\n"
                f"📤 Payables: **{fmt(summary['payables'])} {cur}**\n"
                f"📉 30-Din Kharcha: **{fmt(summary['monthly_burn'])} {cur}**\n\n"
                f"💡 Specific cheez poochein jaise: 'Ali se kitna paisa aya?' ya 'Is mahine ka kharcha?'")
    return (f"💼 **ZetaFin Dashboard Summary:**\n\n"
            f"💰 Balance: **{fmt(summary['balance'])} {cur}**\n"
            f"📥 Receivables: **{fmt(summary['receivables'])} {cur}**\n"
            f"📤 Payables: **{fmt(summary['payables'])} {cur}**\n"
            f"📉 30-Day Burn: **{fmt(summary['monthly_burn'])} {cur}**\n\n"
            f"💡 Try asking: 'Income from Ali?' or 'This month expenses?'")


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
async def query_ai_insights(query: str, db: Session, user_id: int):
    try:
        summary = get_ceo_summary(db, user_id)
        search_results = deep_search(query, db, user_id)
        return build_response(query, summary, search_results)
    except Exception as e:
        print(f"ZetaFin AI Engine Error: {e}")
        import traceback; traceback.print_exc()
        return "⚠️ ZetaFin AI encountered an error. Please try again."


# ─────────────────────────────────────────────
# AUDIT LOGGER
# ─────────────────────────────────────────────
def log_audit(db: Session, user_id: int, action: str, table: str, record_id: int, old_val=None, new_val=None):
    log = AuditLog(
        user_id=user_id,
        action=action,
        table_name=table,
        record_id=record_id,
        old_values=json.dumps(old_val) if old_val else None,
        new_values=json.dumps(new_val) if new_val else None,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
