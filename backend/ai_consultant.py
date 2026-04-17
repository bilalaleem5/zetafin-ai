"""
ZetaFin AI Consultant — Hybrid Intelligence Engine v3.0
=========================================================
Primary:  Zero-API rule-based engine (12 intents, Roman Urdu + English)
          Rich template ResponseBuilder + live DB financial analysis
Fallback: Gemini 2.5 Flash for unknown/complex queries only

No API credits consumed for standard financial questions.
"""
import re
import random
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from sqlmodel import Session, select, func

from models import (
    Transaction, Milestone, VendorBill, RecurringExpense,
    User, AuditLog, Budget, Client, Employee, Vendor
)

load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_KEY", "")
_gemini_model = None
if GEMINI_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_KEY)
        _gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
        print(f"DEBUG: Gemini 2.5 Flash ready (fallback only).")
    except Exception as e:
        print(f"DEBUG: Gemini load failed: {e}")


# ═══════════════════════════════════════════════════════════════
# SECTION 1: INTENT DETECTION (Regex — Zero Cost)
# ═══════════════════════════════════════════════════════════════

INTENT_PATTERNS: Dict[str, List[str]] = {
    "greeting": [
        r"^(hi|hello|hey|salam|aoa|assalam|walaikum|السلام|ہیلو)[\s!.?]*$",
        r"\b(good morning|good evening|good afternoon)\b",
    ],
    "help": [
        r"\b(help|madad|menu|kya kar|kya kya|features?|guide|مدد)\b",
    ],
    "health_check": [
        r"\b(health|sehat|kaisa hai|overall|summary|khulasa|jaaiza|status|score)\b",
        r"\b(total picture|how.*doing|kaisi.*hai.*company)\b",
    ],
    "cost_cutting": [
        r"\b(cost.?cut|kharcha.*kam|expense.*kam|reduce.*cost|budget.*tight)\b",
        r"\b(bachao|bachat|savings?|save karo|بچت|بچاؤ|cut down|minimize)\b",
        r"\b(waste|fuzool|fizool|unnecessary|فضول|kahan.*se.*cut)\b",
    ],
    "hiring": [
        r"\b(hire|hiring|rakhna|recruit|naukri|بھرتی|ملازم)\b",
        r"\b(naye.*log|new.*employee|staff.*add|team.*barh|employee.*chahiye)\b",
        r"\b(gap.*hire|afford.*hire|kya.*hire|hire.*kar|rakh.*sakta)\b",
    ],
    "profit_analysis": [
        r"\b(profit|munafa|منافع|loss|nuksaan|نقصان|P&L|revenue|aamdani|kamai)\b",
        r"\b(margin|return|ROI|net.*income|kitna.*kama)\b",
    ],
    "cash_flow": [
        r"\b(cash|paisa|paise|پیسے|runway|burn.*rate|liquidity|bank.*balance)\b",
        r"\b(kitna.*bacha|paisa.*khatam|receivable|payable)\b",
    ],
    "salary_analysis": [
        r"\b(salary|salari|takhwa|تنخواہ|payroll|wages?|employee.*cost)\b",
    ],
    "forecast": [
        r"\b(forecast|projection|future|mustaqbil|agla.*mah|next.*month|predict)\b",
        r"\b(kya.*hoga|kaisa.*rahega|outlook|trend|آئندہ)\b",
    ],
    "risk_assessment": [
        r"\b(risk|خطرہ|khatra|danger|badi.*problem|koi.*issue|warning|alert)\b",
    ],
    "recommendations": [
        r"\brecommen\w*\b",
        r"\b(suggestion|salah|مشورہ|tips?|advice|kya.*karna.*chahiye|batao.*kya)\b",
        r"\b(top.*tips|best.*action|action.*plan|next.*step)\b",
    ],
    "expense_breakdown": [
        r"\b(expense.*detail|kharcha.*detail|breakdown|categories?|tafseel|تفصیل)\b",
        r"\b(kahan.*jata|kitna.*kharcha.*kahan)\b",
    ],
    "net_position": [
        r"\b(net.*position|net.*pos|overall.*position|financial.*position|total.*position)\b",
        r"\b(mukamal|sara.*hisab|poora.*picture|net)\b",
    ],
    "recent_transactions": [
        r"\b(recent|latest|last|pichli|akhri|transactions?|history)\b",
    ],
    "audit_log": [
        r"\b(audit|deleted|edited|updated|changed|kisne|who.*did|activity)\b",
    ],
    "thanks": [
        r"\b(thanks?|shukriya|شکریہ|jazakallah|meherbani|theek.*bye|okay.*bye)\b",
    ],
}

_COMPILED_INTENTS = {
    intent: [re.compile(p, re.IGNORECASE | re.UNICODE) for p in pats]
    for intent, pats in INTENT_PATTERNS.items()
}

ROMAN_URDU_WORDS = {
    "hai", "hain", "ka", "ki", "ko", "se", "mein", "kya", "karo", "karna",
    "bata", "batao", "chahiye", "hoga", "kaise", "kyun", "aur", "ya", "nahi",
    "theek", "agar", "toh", "phir", "paise", "kitna", "kitni", "kahan",
    "kaisa", "shukriya", "bohot", "bahut", "sirf", "zyada", "kam", "naya",
    "abhi", "yar", "bhai", "deko", "btao", "krna", "hay", "ha",
}


def detect_language(text: str) -> str:
    if re.search(r'[\u0600-\u06FF]', text):
        return "urdu"
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if len(words & ROMAN_URDU_WORDS) >= 2:
        return "roman_urdu"
    return "english"


def detect_intent(text: str) -> str:
    t = text.strip().lower()
    if re.match(r'^(hi|hello|hey|salam|aoa|assalam)[\s!.?]*$', t):
        return "greeting"
    scores: Dict[str, int] = {}
    for intent, patterns in _COMPILED_INTENTS.items():
        for p in patterns:
            if p.search(text):
                scores[intent] = scores.get(intent, 0) + 1
    return max(scores, key=scores.get) if scores else "unknown"


# ═══════════════════════════════════════════════════════════════
# SECTION 2: FINANCIAL ANALYSIS ENGINE (Zero API Cost)
# ═══════════════════════════════════════════════════════════════

def get_ceo_summary(db: Session, user_id: int) -> dict:
    user     = db.get(User, user_id)
    balance  = user.bank_balance if user else 0.0
    currency = user.currency if user else "PKR"

    receivables = db.exec(select(func.sum(Milestone.amount)).where(
        Milestone.user_id == user_id, Milestone.status != "Paid")).one() or 0.0
    payables = db.exec(select(func.sum(VendorBill.amount)).where(
        VendorBill.user_id == user_id, VendorBill.status != "Paid")).one() or 0.0

    thirty_ago = datetime.utcnow() - timedelta(days=30)
    burn = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == "expense",
        Transaction.date >= thirty_ago)).one() or 0.0
    income_30d = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == "income",
        Transaction.date >= thirty_ago)).one() or 0.0

    total_income  = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == "income")).one() or 0.0
    total_expense = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == "expense")).one() or 0.0

    # Monthly expense categories
    first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    exp_rows = db.exec(select(Transaction.category, func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == "expense",
        Transaction.date >= first_of_month).group_by(Transaction.category)).all()
    expense_categories = {cat: float(amt) for cat, amt in exp_rows if cat}

    # Payroll (salary category)
    payroll = db.exec(select(func.sum(Transaction.amount)).where(
        Transaction.user_id == user_id, Transaction.type == "expense",
        Transaction.category.ilike("%salary%"))).one() or 0.0

    client_count   = db.exec(select(func.count(Client.id)).where(Client.user_id == user_id)).one() or 0
    employee_count = db.exec(select(func.count(Employee.id)).where(Employee.user_id == user_id)).one() or 0
    vendor_count   = db.exec(select(func.count(Vendor.id)).where(Vendor.user_id == user_id)).one() or 0

    recent_txs    = db.exec(select(Transaction).where(
        Transaction.user_id == user_id).order_by(Transaction.date.desc()).limit(15)).all()
    recent_audits = db.exec(select(AuditLog).where(
        AuditLog.user_id == user_id).order_by(AuditLog.timestamp.desc()).limit(10)).all()

    # ── Run analysis ──────────────────────────────────────────
    net = total_income - total_expense
    margin = round((net / total_income) * 100, 1) if total_income > 0 else 0

    # Expense analysis
    exp_analysis = {}
    if expense_categories and total_expense > 0:
        HINTS = {
            "marketing":     "Digital marketing ROI track karo, low channels band karo",
            "rent":          "Remote work ya smaller office consider karo",
            "utility":       "Energy-efficient equipment lagao",
            "travel":        "Video calls se replace karo",
            "subscription":  "Unused tools audit karo aur cancel karo",
            "overtime":      "Workload distribution review karo",
            "training":      "Online courses > expensive workshops",
            "entertain":     "Per-employee limit set karo",
        }
        exp_analysis = {}
        for cat, amt in expense_categories.items():
            pct = round((amt / total_expense) * 100, 1)
            status = "critical" if pct >= 50 else "high" if pct >= 30 else "normal"
            hint = next((v for k, v in HINTS.items() if k in cat.lower()),
                        "Vendor renegotiation aur bulk deals try karo")
            exp_analysis[cat] = {
                "amount": amt, "percentage": pct,
                "status": status, "suggestion": hint
            }

    # Health score
    score = 100
    deductions = []
    if margin < 0:
        score -= 40; deductions.append("Loss mein hai (-40)")
    elif margin < 10:
        score -= 20; deductions.append("Profit margin bohot kam (-20)")
    elif margin < 20:
        score -= 10; deductions.append("Profit margin average (-10)")
    runway_months = round(balance / burn, 1) if burn > 0 else None
    if runway_months:
        if runway_months < 3:
            score -= 30; deductions.append("Cash runway critical (-30)")
        elif runway_months < 6:
            score -= 15; deductions.append("Cash runway short (-15)")
    payroll_pct = round((payroll / total_income) * 100, 1) if total_income > 0 else 0
    if payroll_pct > 60:
        score -= 15; deductions.append("Payroll burden high (-15)")
    score = max(0, score)
    grade = ("A — Excellent" if score >= 80 else "B — Good" if score >= 65
             else "C — Average" if score >= 50 else "D — Poor" if score >= 35 else "F — Critical")

    # Risk flags
    risks = []
    if total_expense > total_income > 0:
        risks.append({"level": "CRITICAL",
                      "flag": f"Business loss mein hai — {total_expense - total_income:,.0f} {currency} nuksaan",
                      "action": "Fori cost cutting implement karo"})
    if runway_months and runway_months < 3:
        risks.append({"level": "CRITICAL",
                      "flag": f"Cash runway sirf {runway_months} mahine",
                      "action": "Expense freeze ya emergency fundraising karo"})
    elif runway_months and runway_months < 6:
        risks.append({"level": "WARNING",
                      "flag": f"Cash runway {runway_months} mahine — tight",
                      "action": "Non-essential spending control karo"})
    if payroll_pct > 60:
        risks.append({"level": "HIGH",
                      "flag": f"Payroll income ka {payroll_pct}% hai",
                      "action": "Hiring freeze karo"})

    # Hiring recommendation
    hiring_rec = "CAUTIOUS"
    hiring_reason = "Enough information nahi — review needed"
    if net < 0:
        hiring_rec = "DO NOT HIRE"; hiring_reason = "Business loss mein hai"
    elif payroll_pct > 50:
        hiring_rec = "DEFER HIRING"; hiring_reason = f"Payroll pehle se {payroll_pct}% income ka hai"
    elif balance > burn * 3:
        hiring_rec = "CAN HIRE"; hiring_reason = "Healthy cash reserves hain"

    return {
        "balance": balance, "receivables": receivables, "payables": payables,
        "monthly_burn": burn, "income_30d": income_30d,
        "total_income": total_income, "total_expense": total_expense,
        "net_position": net, "profit_margin": margin,
        "currency": currency,
        "expense_categories": exp_analysis,
        "payroll": payroll, "payroll_pct": payroll_pct,
        "runway_months": runway_months,
        "runway_status": ("critical" if runway_months and runway_months < 3
                          else "warning" if runway_months and runway_months < 6 else "healthy"),
        "health_score": score, "grade": grade, "deductions": deductions,
        "risk_flags": risks,
        "hiring_rec": hiring_rec, "hiring_reason": hiring_reason,
        "counts": {"clients": client_count, "employees": employee_count, "vendors": vendor_count},
        "recent_transactions": recent_txs,
        "recent_audits": recent_audits,
    }


# ═══════════════════════════════════════════════════════════════
# SECTION 3: DEEP KEYWORD SEARCH
# ═══════════════════════════════════════════════════════════════

def deep_search(query: str, db: Session, user_id: int) -> list:
    from sqlmodel import or_
    STOP = {"how","much","tell","from","with","this","that","show","what","where",
            "when","ka","ki","ko","se","mein","kya","hai","ha","the","for","and",
            "karo","karna","btao","deko","mera","meri","aur","ya","bhi","jo","wo"}
    keywords = [w.strip("?,.!") for w in query.lower().split()
                if len(w) > 2 and w not in STOP]
    if not keywords:
        return []
    results = []

    # Transactions
    tf = [Transaction.description.ilike(f"%{w}%") for w in keywords]
    tf += [Transaction.category.ilike(f"%{w}%") for w in keywords]
    for t in db.exec(select(Transaction).where(
            Transaction.user_id == user_id, or_(*tf)
    ).order_by(Transaction.date.desc()).limit(20)).all():
        results.append(("tx", t))

    # Clients + their transactions
    for c in db.exec(select(Client).where(
            Client.user_id == user_id,
            or_(*[Client.name.ilike(f"%{w}%") for w in keywords]))).all():
        results.append(("client", c))
        for ct in db.exec(select(Transaction).where(
                Transaction.user_id == user_id,
                Transaction.client_id == c.id
        ).order_by(Transaction.date.desc()).limit(10)).all():
            results.append(("tx", ct))

    # Employees
    for e in db.exec(select(Employee).where(
            Employee.user_id == user_id,
            or_(*[Employee.name.ilike(f"%{w}%") for w in keywords]))).all():
        results.append(("employee", e))

    # Milestones
    for m in db.exec(select(Milestone).where(
            Milestone.user_id == user_id,
            or_(*[Milestone.title.ilike(f"%{w}%") for w in keywords]))).all():
        results.append(("milestone", m))

    # Bills
    for b in db.exec(select(VendorBill).where(
            VendorBill.user_id == user_id,
            or_(*[VendorBill.title.ilike(f"%{w}%") for w in keywords]))).all():
        results.append(("bill", b))

    # Vendors
    for v in db.exec(select(Vendor).where(
            Vendor.user_id == user_id,
            or_(*[Vendor.name.ilike(f"%{w}%") for w in keywords]))).all():
        results.append(("vendor", v))

    return results


# ═══════════════════════════════════════════════════════════════
# SECTION 4: RESPONSE BUILDER (Zero API, Rich Templates)
# ═══════════════════════════════════════════════════════════════

def _fmt(n): return f"{n:,.0f}"
def _fmtd(n): return f"{n:,.2f}"

def _score_icon(score):
    return "🟢" if score >= 80 else "🟡" if score >= 65 else "🟠" if score >= 50 else "🔴"

def respond_greeting(lang):
    msgs = {
        "roman_urdu": "Assalam o Alaikum! Main ZETA hoon — aapka ZetaFin AI consultant. 😊\nKya poochna chahte hain? (Cost cutting, hiring, profit, cash flow, health check)",
        "urdu": "السلام علیکم! میں ZETA ہوں — آپ کا ZetaFin AI مالی معاون۔ 😊\nکیا پوچھنا چاہتے ہیں؟",
        "english": "Hello! I'm ZETA, your ZetaFin AI Financial Consultant. 😊\nAsk me about cost cutting, hiring, profitability, cash flow, or your business health score!",
    }
    return msgs.get(lang, msgs["roman_urdu"])

def respond_help(lang):
    return """📋 ZETA kya kya kar sakta hai (Zero API):

1. health check  — Financial health score 0-100
2. cost cutting  — Expense breakdown + savings plan
3. hiring?       — Data-based hire/defer verdict
4. profit        — Revenue, expenses, margin analysis
5. cash flow     — Runway, burn rate, liquidity
6. salary        — Payroll analysis
7. forecast      — 3-month outlook
8. risk          — Risk flags + warnings
9. recommendations — Top priority action list
10. net position — Complete P&L snapshot
11. recent transactions — Last 15 entries
12. [name/vendor/client] — Deep search in DB

Koi bhi sawal karo — main jawab dunga! 🤖"""

def respond_net_position(s, lang):
    cur = s["currency"]
    net = s["net_position"]
    icon = _score_icon(s["health_score"])
    arrow = "+" if net >= 0 else ""
    word = "Profit" if net >= 0 else "Loss"
    if lang == "roman_urdu":
        return (f"📊 Net Financial Position:\n\n"
                f"💰 Bank Balance:     {_fmtd(s['balance'])} {cur}\n"
                f"📥 Receivables:      {_fmtd(s['receivables'])} {cur}\n"
                f"📤 Payables:         {_fmtd(s['payables'])} {cur}\n"
                f"📈 Total Income:     {_fmtd(s['total_income'])} {cur}\n"
                f"📉 Total Expenses:   {_fmtd(s['total_expense'])} {cur}\n"
                f"💹 Net {word}:       {arrow}{_fmtd(net)} {cur}\n"
                f"📊 Profit Margin:    {s['profit_margin']}%\n\n"
                f"{icon} Health Score: {s['health_score']}/100 — {s['grade']}\n"
                f"{'✅ Mubarak! Profitable ho.' if net >= 0 else '⚠️ Loss mein ho — action lo.'}")
    return (f"📊 Net Financial Position:\n\n"
            f"💰 Bank Balance: {_fmtd(s['balance'])} {cur}\n"
            f"📥 Receivables: {_fmtd(s['receivables'])} {cur}\n"
            f"📤 Payables: {_fmtd(s['payables'])} {cur}\n"
            f"📈 Total Income: {_fmtd(s['total_income'])} {cur}\n"
            f"📉 Total Expenses: {_fmtd(s['total_expense'])} {cur}\n"
            f"💹 Net {word}: {arrow}{_fmtd(net)} {cur}\n"
            f"📊 Profit Margin: {s['profit_margin']}%\n\n"
            f"{icon} Health Score: {s['health_score']}/100 — {s['grade']}\n"
            f"{'✅ Business is profitable!' if net >= 0 else '⚠️ Running at a loss — take action.'}")

def respond_health(s, lang):
    cur = s["currency"]
    icon = _score_icon(s["health_score"])
    lines = [f"🏥 Financial Health Report\n",
             f"{icon} Health Score: {s['health_score']}/100 — {s['grade']}\n",
             f"💰 Balance: {_fmtd(s['balance'])} {cur}",
             f"📈 Income (30d): {_fmtd(s['income_30d'])} {cur}",
             f"📉 Burn (30d): {_fmtd(s['monthly_burn'])} {cur}",
             f"💹 Net P&L: {s['net_position']:+,.2f} {cur}",
             f"📊 Margin: {s['profit_margin']}%"]
    if s["runway_months"]:
        ri = "🔴" if s["runway_status"] == "critical" else "🟡" if s["runway_status"] == "warning" else "🟢"
        label = "mahine" if lang == "roman_urdu" else "months"
        lines.append(f"{ri} Runway: {s['runway_months']} {label}")
    if s["deductions"]:
        lines.append(f"\n📉 Score deductions:")
        for d in s["deductions"]: lines.append(f"  • {d}")
    if s["risk_flags"]:
        lines.append(f"\n🚨 Risk Flags ({len(s['risk_flags'])}):")
        for r in s["risk_flags"]:
            lines.append(f"  [{r['level']}] {r['flag']}")
            lines.append(f"  → {r['action']}")
    else:
        lines.append("\n✅ Koi bada risk nahi mila!")
    score = s["health_score"]
    lines.append(f"\n{'─'*38}")
    if score >= 80:   lines.append("💪 Excellent! Business financially strong hai.")
    elif score >= 65: lines.append("👍 Good. Kuch areas improve ho sakte hain.")
    elif score >= 50: lines.append("⚠️ Average. Attention zaroor do.")
    elif score >= 35: lines.append("🚨 Poor. Fori action lo!")
    else:             lines.append("💀 Critical! Emergency measures lo!")
    return "\n".join(lines)

def respond_cost_cutting(s, lang):
    cur = s["currency"]
    cats = s["expense_categories"]
    lines = [f"✂️ Cost Cutting Plan\n",
             f"📊 This Month's Expenses: {_fmtd(s['monthly_burn'])} {cur}\n"]
    if cats:
        lines.append("Expense Breakdown (zyada se kam):")
        sorted_cats = sorted(cats.items(), key=lambda x: -x[1]["percentage"])
        for cat, info in sorted_cats:
            icon = "🚨" if info["status"] == "critical" else "⚠️" if info["status"] == "high" else "✅"
            lines.append(f"  {icon} {cat}: {_fmt(info['amount'])} {cur} ({info['percentage']}%)")
        lines.append(f"\n{'─'*38}")
        lines.append("💡 Optimization Opportunities (Priority):")
        i = 1
        for cat, info in sorted_cats:
            if info["status"] in ("high", "critical"):
                saving = info["amount"] * 0.15
                lines.append(f"\n{i}. {cat} ({info['percentage']}% of expenses)")
                lines.append(f"   Tip: {info['suggestion']}")
                lines.append(f"   Est. saving: ~{_fmt(saving)} {cur}/month")
                i += 1
        if i == 1:
            lines.append("Sab categories normal range mein hain.")
    lines += [f"\n{'─'*38}", "Quick Wins (Abhi Karo):",
              "1. Unused subscriptions cancel karo",
              "2. Vendor contracts renegotiate karo (10-15% discount maango)",
              "3. Travel/entertainment per-person limit set karo",
              "4. Electricity timers lagao office mein"]
    return "\n".join(lines)

def respond_hiring(s, lang):
    cur = s["currency"]
    rec = s["hiring_rec"]
    icon = "✅" if rec == "CAN HIRE" else "❌" if "DO NOT" in rec else "⚠️"
    lines = [f"👥 Hiring Decision\n",
             f"{icon} Verdict: {rec}\n",
             f"Reason: {s['hiring_reason']}\n",
             f"{'─'*38}",
             f"📊 Numbers:",
             f"  Employees: {s['counts']['employees']}",
             f"  Payroll: {_fmtd(s['payroll'])} {cur} ({s['payroll_pct']}% of income)"]
    if s["runway_months"]:
        ri = "🔴" if s["runway_status"] == "critical" else "🟡" if s["runway_status"] == "warning" else "🟢"
        lines.append(f"  {ri} Cash Runway: {s['runway_months']} months")
    lines.append(f"\n{'─'*38}")
    if rec == "CAN HIRE":
        lines += ["Steps before hiring:", "1. Clear job description banao",
                  "2. Budget mein salary define karo", "3. 3-month probation period rakho",
                  "4. KPIs pehle se set karo"]
    else:
        lines += ["Alternatives to hiring:", "1. Automate repetitive tasks",
                  "2. Freelancers hire karo specific projects ke liye",
                  "3. Non-core work outsource karo", "4. Existing team ki productivity measure karo"]
    return "\n".join(lines)

def respond_profit(s, lang):
    cur = s["currency"]
    net = s["net_position"]
    margin = s["profit_margin"]
    lines = [f"📈 Profit Analysis\n",
             f"💰 Total Income: {_fmtd(s['total_income'])} {cur}",
             f"💸 Total Expenses: {_fmtd(s['total_expense'])} {cur}",
             f"💹 Net {'Profit' if net >= 0 else 'Loss'}: {net:+,.2f} {cur}",
             f"📊 Profit Margin: {margin}%",
             f"  (Healthy: 15-25%)\n",
             f"{'─'*38}"]
    if net < 0:
        lines += ["🚨 Loss mein ho! Fori action:", "1. Biggest expenses immediately cut karo",
                  "2. New sales aggressively close karo", "3. Non-essential spending freeze karo"]
    elif margin < 15:
        lines += ["⚠️ Margin improve karo:", "1. Pricing review karo — thoda barha sakte ho",
                  "2. High-margin services pe focus karo", "3. Low-margin clients gracefully exit karo"]
    else:
        lines += ["✅ Healthy margin!", "1. Growth mein invest karo (marketing, sales)",
                  "2. New revenue streams explore karo", "3. Premium offerings add karo"]
    return "\n".join(lines)

def respond_cash_flow(s, lang):
    cur = s["currency"]
    lines = [f"💵 Cash Flow Analysis\n",
             f"💰 Bank Balance: {_fmtd(s['balance'])} {cur}",
             f"🔥 30-Day Burn Rate: {_fmtd(s['monthly_burn'])} {cur}",
             f"📥 Income (30d): {_fmtd(s['income_30d'])} {cur}",
             f"📥 Receivables: {_fmtd(s['receivables'])} {cur}",
             f"📤 Payables: {_fmtd(s['payables'])} {cur}"]
    if s["runway_months"]:
        ri = ("🔴" if s["runway_status"] == "critical"
              else "🟡" if s["runway_status"] == "warning" else "🟢")
        label = "mahine" if lang == "roman_urdu" else "months"
        lines.append(f"\n{ri} Cash Runway: {s['runway_months']} {label} [{s['runway_status'].upper()}]")
        if s["runway_status"] == "critical":
            lines += ["\n🚨 Emergency Steps:", "1. Non-essential expenses ABHI band karo",
                      "2. Outstanding payments collect karo", "3. Clients se advance maango"]
        elif s["runway_status"] == "warning":
            lines += ["\n⚠️ Action Plan:", "1. Discretionary spending reduce karo",
                      "2. Receivables accelerate karo", "3. New business aggressively close karo"]
        else:
            lines.append("\n✅ Cash position comfortable hai.")
    return "\n".join(lines)

def respond_salary(s, lang):
    cur = s["currency"]
    pct = s["payroll_pct"]
    icon = "🔴" if pct > 60 else "🟡" if pct > 45 else "🟢"
    lines = [f"💼 Payroll Analysis\n",
             f"💰 Total Payroll (salary txns): {_fmtd(s['payroll'])} {cur}",
             f"👥 Employees: {s['counts']['employees']}",
             f"{icon} Payroll % of Income: {pct}%",
             f"  (Healthy: 30-45%)\n",
             f"{'─'*38}"]
    if pct > 60:
        lines += ["🔴 Payroll BAHUT zyada hai!", "• Hiring freeze lagao",
                  "• Performance-based bonuses consider karo fixed ki jagah",
                  "• Underperforming roles review karo"]
    elif pct > 45:
        lines += ["⚠️ Payroll thoda high hai", "• New hiring se pehle sochna hoga",
                  "• Revenue badhao — ratio automatically improve hoga"]
    else:
        lines += ["✅ Payroll healthy range mein hai", "• Sustainable hai — koi fori action nahi"]
    return "\n".join(lines)

def respond_forecast(s, lang):
    cur = s["currency"]
    net = s["net_position"]
    margin = s["profit_margin"]
    is_loss = net < 0
    lines = [f"📈 3-Month Financial Forecast\n",
             f"Current Margin: {margin}%",
             f"Current Net: {net:+,.2f} {cur}\n",
             f"{'─'*38}",
             "3 Scenarios:\n"]
    if not is_loss:
        lines += [f"🟢 Best Case: Revenue +15%, Expenses -5% → Margin ~{margin + 8:.1f}%",
                  f"🟡 Realistic: Revenue +5%, Expenses flat → Margin ~{margin + 2:.1f}%",
                  f"🔴 Worst Case: Revenue -10%, Expenses +5% → Margin ~{margin - 7:.1f}%"]
    else:
        lines += ["🟢 Best Case: Expenses -20%, Revenue +10% → Break-even possible",
                  "🟡 Realistic: Expenses -10% → Loss reduces by 50%",
                  "🔴 Worst Case: Kuch na kiya → Loss badhta rahega"]
    lines += [f"\n{'─'*38}", "3-Month Targets:",
              "1. Revenue: +10% (aggressively sell karo)",
              "2. Expenses: -5 to -15% (cost cutting implement karo)",
              "3. Cash: Min 3 months runway maintain karo",
              "4. Payroll: 35-45% of income ke andar rakho"]
    return "\n".join(lines)

def respond_risks(s, lang):
    lines = [f"🚨 Risk Assessment Report\n"]
    if not s["risk_flags"]:
        lines += ["✅ Koi major risk flag nahi mila!",
                  f"Health Score: {s['health_score']}/100 — {s['grade']}",
                  "Business financially stable dikh raha hai.",
                  "\nMinor watch areas:",
                  "• Monthly review karo — data updated rakho",
                  f"• Profit margin {s['profit_margin']}% — {'good' if s['profit_margin'] >= 15 else 'improve karo'}"]
    else:
        for r in s["risk_flags"]:
            icon = "🔴" if r["level"] == "CRITICAL" else "🟠" if r["level"] == "HIGH" else "🟡"
            lines.append(f"{icon} [{r['level']}] {r['flag']}")
            lines.append(f"   → Action: {r['action']}\n")
    lines += [f"\n{'─'*38}", f"Overall: {s['health_score']}/100 — {s['grade']}"]
    return "\n".join(lines)

def respond_recommendations(s, lang):
    lines = [f"🎯 Top Recommendations (Priority Order)\n",
             f"Health Score: {s['health_score']}/100 — {s['grade']}\n",
             f"{'─'*38}"]
    recs = []
    for r in s["risk_flags"]:
        if r["level"] == "CRITICAL":
            recs.append(("🚨 URGENT", r["flag"], r["action"]))
    if s["runway_months"] and s["runway_months"] < 6:
        recs.append(("⚠️ HIGH", "Cash runway short hai",
                     "Receivables accelerate karo, non-essential spending band karo"))
    cats = s["expense_categories"]
    for cat, info in sorted(cats.items(), key=lambda x: -x[1]["percentage"])[:3]:
        if info["status"] in ("high", "critical"):
            recs.append(("💡 MEDIUM", f"{cat} optimize karo ({info['percentage']}%)",
                         info["suggestion"]))
    if s["payroll_pct"] > 50:
        recs.append(("⚠️ HIGH", f"Payroll {s['payroll_pct']}% — zyada hai",
                     "Hiring freeze + performance-based compensation consider karo"))
    if s["profit_margin"] < 15 and s["profit_margin"] >= 0:
        recs.append(("💡 MEDIUM", f"Profit margin {s['profit_margin']}% — improve karo",
                     "Pricing review karo, high-margin services pe focus karo"))
    if s["health_score"] >= 65:
        recs.append(("📈 GROWTH", "Financial position stable hai",
                     "Marketing aur sales mein invest karo — growth ke liye ready ho"))
    if not recs:
        recs.append(("✅ GOOD", "Koi major issue nahi", "Current strategy maintain karo"))
    for i, (priority, issue, action) in enumerate(recs[:8], 1):
        lines.append(f"\n{i}. [{priority}] {issue}")
        lines.append(f"   → {action}")
    lines += [f"\n{'─'*38}", "Kisi specific topic pe detail chahiye? Poochein!"]
    return "\n".join(lines)

def respond_expense_breakdown(s, lang):
    cur = s["currency"]
    cats = s["expense_categories"]
    if not cats:
        return f"Is mahine abhi tak koi expense record nahi. 30-day burn: {_fmtd(s['monthly_burn'])} {cur}"
    lines = [f"📋 Expense Breakdown (This Month)\n",
             f"Total: {_fmtd(s['monthly_burn'])} {cur}\n"]
    for cat, info in sorted(cats.items(), key=lambda x: -x[1]["percentage"]):
        icon = "🚨" if info["status"] == "critical" else "⚠️" if info["status"] == "high" else "✅"
        lines.append(f"  {icon} {cat}: {_fmt(info['amount'])} {cur} ({info['percentage']}%)")
    return "\n".join(lines)

def respond_recent_transactions(s, lang):
    cur = s["currency"]
    txs = s.get("recent_transactions", [])
    if not txs:
        return "Koi transaction record nahi mila."
    lines = [f"📋 Recent Transactions:\n"]
    for t in txs[:15]:
        arrow = "📥" if t.type == "income" else "📤"
        lines.append(f"{arrow} {t.date.strftime('%d %b %Y')} | {t.description} | {_fmt(t.amount)} {cur}")
    return "\n".join(lines)

def respond_audit(s, lang):
    audits = s.get("recent_audits", [])
    if not audits:
        return "Koi audit log nahi mila."
    lines = [f"📜 System Activity Log:\n"]
    for a in audits[:10]:
        lines.append(f"🔍 {a.timestamp.strftime('%d %b %Y %H:%M')} | {a.action} on {a.table_name} (ID: {a.record_id})")
    return "\n".join(lines)

def respond_search_results(search_results, s, lang):
    cur = s["currency"]
    if not search_results:
        return None
    lines = [f"🔍 Matching Records Found:\n"]
    total_in = total_out = 0
    for rtype, record in search_results[:15]:
        if rtype == "tx":
            arrow = "📥" if record.type == "income" else "📤"
            lines.append(f"{arrow} {record.date.strftime('%d %b %Y')} | {record.description} | {_fmt(record.amount)} {cur} ({record.type})")
            if record.type == "income": total_in += record.amount
            else: total_out += record.amount
        elif rtype == "client":
            lines.append(f"👤 Client: {record.name} | Contract: {_fmt(record.contract_value)} {cur} | {record.status}")
        elif rtype == "employee":
            lines.append(f"👨‍💼 Employee: {record.name} | {record.role} | Salary: {_fmt(record.salary)} {cur}")
        elif rtype == "milestone":
            lines.append(f"🎯 Milestone: {record.title} | {_fmt(record.amount)} {cur} | {record.status}")
        elif rtype == "bill":
            lines.append(f"🧾 Bill: {record.title} | {_fmt(record.amount)} {cur} | {record.status}")
        elif rtype == "vendor":
            lines.append(f"🏪 Vendor: {record.name} | {record.category}")
    if total_in > 0: lines.append(f"\n💵 Total Received: {_fmt(total_in)} {cur}")
    if total_out > 0: lines.append(f"💸 Total Paid: {_fmt(total_out)} {cur}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# SECTION 5: GEMINI FALLBACK (only for unknown intents)
# ═══════════════════════════════════════════════════════════════

async def _gemini_fallback(query: str, s: dict) -> str:
    global _gemini_model
    if not _gemini_model:
        return _fallback_summary(s)
    cur = s["currency"]
    prompt = f"""You are ZETA — ZetaFin AI Financial Consultant.

RULES:
- Respond in same language as user (Roman Urdu → Roman Urdu, English → English).
- Use live data below. Be specific with numbers.
- Do NOT use markdown bold (**). Plain text only.
- Keep response concise and actionable.

LIVE FINANCIAL DATA:
Balance: {s['balance']:,.2f} {cur}
Net P&L: {s['net_position']:+,.2f} {cur}
Margin: {s['profit_margin']}%
Health Score: {s['health_score']}/100 — {s['grade']}
Receivables: {s['receivables']:,.2f} {cur}
Payables: {s['payables']:,.2f} {cur}
30d Burn: {s['monthly_burn']:,.2f} {cur}
Clients: {s['counts']['clients']} | Employees: {s['counts']['employees']}
Runway: {s['runway_months']} months
Hiring Signal: {s['hiring_rec']}
Risk Flags: {'; '.join(r['flag'] for r in s['risk_flags']) or 'None'}

CEO QUERY: {query}

RESPONSE:"""
    try:
        response = _gemini_model.generate_content(prompt)
        if response and response.text:
            return response.text.replace("**", "").strip()
    except Exception as e:
        print(f"Gemini fallback error: {e}")
    return _fallback_summary(s)

def _fallback_summary(s):
    cur = s["currency"]
    return (f"ZetaFin Summary:\n"
            f"Balance: {_fmtd(s['balance'])} {cur}\n"
            f"Net P&L: {s['net_position']:+,.2f} {cur}\n"
            f"Health: {s['health_score']}/100 — {s['grade']}\n\n"
            f"Poochein: 'health check', 'cost cutting', 'hiring?', 'net position', 'risks'")


# ═══════════════════════════════════════════════════════════════
# SECTION 6: MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════

async def query_ai_insights(query: str, db: Session, user_id: int) -> str:
    try:
        s    = get_ceo_summary(db, user_id)
        lang = detect_language(query)
        intent = detect_intent(query)

        # Intent → Rule-based handler (zero API cost)
        handlers = {
            "greeting":            lambda: respond_greeting(lang),
            "help":                lambda: respond_help(lang),
            "net_position":        lambda: respond_net_position(s, lang),
            "health_check":        lambda: respond_health(s, lang),
            "cost_cutting":        lambda: respond_cost_cutting(s, lang),
            "expense_breakdown":   lambda: respond_expense_breakdown(s, lang),
            "hiring":              lambda: respond_hiring(s, lang),
            "profit_analysis":     lambda: respond_profit(s, lang),
            "cash_flow":           lambda: respond_cash_flow(s, lang),
            "salary_analysis":     lambda: respond_salary(s, lang),
            "forecast":            lambda: respond_forecast(s, lang),
            "risk_assessment":     lambda: respond_risks(s, lang),
            "recommendations":     lambda: respond_recommendations(s, lang),
            "recent_transactions": lambda: respond_recent_transactions(s, lang),
            "audit_log":           lambda: respond_audit(s, lang),
            "thanks":              lambda: random.choice([
                "Koi baat nahi! Aur kuch poochna ho to batayein. 😊",
                "Khushi hui madad karke! 🤖",
                "You're welcome! Feel free to ask anything else. 😊"]),
        }

        if intent in handlers:
            return handlers[intent]()

        # Deep search for specific names/entities
        search_results = deep_search(query, db, user_id)
        if search_results:
            result = respond_search_results(search_results, s, lang)
            if result:
                return result

        # Fallback: Gemini for truly unknown queries
        return await _gemini_fallback(query, s)

    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"ZetaFin AI Engine Error: {e}")
        return "ZetaFin AI encountered an error. Please try again."


# ═══════════════════════════════════════════════════════════════
# AUDIT LOGGER
# ═══════════════════════════════════════════════════════════════

def log_audit(db: Session, user_id: int, action: str, table: str,
              record_id: int, old_val=None, new_val=None):
    log = AuditLog(
        user_id=user_id, action=action, table_name=table, record_id=record_id,
        old_values=json.dumps(old_val) if old_val else None,
        new_values=json.dumps(new_val) if new_val else None,
        timestamp=datetime.utcnow()
    )
    db.add(log)
    db.commit()
