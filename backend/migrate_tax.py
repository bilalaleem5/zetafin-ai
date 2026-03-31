import sqlite3

def run_migration():
    conn = sqlite3.connect('d:/finance product/backend/zetamize.db')
    cursor = conn.cursor()
    tables = [("milestone", "tax_amount", "FLOAT DEFAULT 0.0"), 
              ("milestone", "tax_type", "VARCHAR"),
              ("vendorbill", "tax_amount", "FLOAT DEFAULT 0.0"),
              ("vendorbill", "tax_type", "VARCHAR"),
              ("transaction", "tax_amount", "FLOAT DEFAULT 0.0"),
              ("transaction", "tax_type", "VARCHAR")]
    
    for table, col, defn in tables:
        try:
            cursor.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {defn}')
            print(f"Added {col} to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"{col} already exists in {table}")
            elif "no such table" in str(e).lower():
                print(f"Table {table} not found yet")
            else:
                print(f"Error on {table}.{col}: {e}")
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    run_migration()
