import sqlite3

def check_db():
    conn = sqlite3.connect('d:/finance product/backend/zetamize.db')
    cursor = conn.cursor()
    
    tables = ['user', 'client', 'employee', 'milestone', 'recurringexpense', 'vendor', 'vendorbill', 'transaction']
    
    for table in tables:
        print(f"\n--- Table: {table} ---")
        try:
            # Use quotes for table names in case of reserved words
            cursor.execute(f'PRAGMA table_info("{table}")')
            columns = cursor.fetchall()
            for col in columns:
                print(f"  Field: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]}")
        except Exception as e:
            print(f"  Error checking {table}: {traceback.format_exc()}")
            
    conn.close()

import traceback
if __name__ == "__main__":
    check_db()
