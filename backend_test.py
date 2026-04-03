import httpx
import json

base = "http://127.0.0.1:8000"

# Login with existing account
tok = httpx.post(f"{base}/token", data={
    "username": "audit@zetafin.io",
    "password": "Test1234"
}, timeout=10)
print("Login:", tok.status_code)
if tok.status_code != 200:
    print(tok.text)
    exit(1)

token = tok.json()["access_token"]
h = {"Authorization": f"Bearer {token}"}

# Check all endpoints
routes = httpx.get(f"{base}/openapi.json", timeout=10)
paths = list(routes.json()["paths"].keys())
print(f"Total API endpoints: {len(paths)}")
for p in sorted(paths):
    methods = list(routes.json()["paths"][p].keys())
    print(f"  {','.join(m.upper() for m in methods):<30} {p}")

print("\n")

# Dashboard - all periods
for period in ["this_month", "last_month", "this_year", "all_time"]:
    d = httpx.get(f"{base}/dashboard-stats?period={period}", headers=h, timeout=15)
    s = d.json()
    print(f"[{period.upper():<12}] Income: PKR {s['total_income']:>10,.0f} | Expense: PKR {s['total_expense']:>10,.0f} | Net: PKR {s['net_position']:>10,.0f}")

print("\n")

# Transactions
txs = httpx.get(f"{base}/transactions/", headers=h, timeout=10)
txlist = txs.json()
print(f"Transactions: {len(txlist)} total records")
for tx in txlist[:5]:
    print(f"  [{tx['type'].upper():<8}] {tx['date'][:10]}  PKR {tx['amount']:>10,.0f}  {tx['description'][:40]}")

print("\n")

# Clients
clients = httpx.get(f"{base}/clients/", headers=h, timeout=10)
print(f"Clients: {len(clients.json())} records")
for c in clients.json():
    print(f"  {c['name']} | Contract: PKR {c['contract_value']:,.0f} | Status: {c['status']}")

# Employees
emps = httpx.get(f"{base}/employees/", headers=h, timeout=10)
print(f"Employees: {len(emps.json())} records")

# Vendors
vendors = httpx.get(f"{base}/vendors/", headers=h, timeout=10)
print(f"Vendors: {len(vendors.json())} records")

# Metadata
cats = httpx.get(f"{base}/metadata/categories", headers=h, timeout=10)
print(f"Categories: {cats.json()}")
