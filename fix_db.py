import sqlite3

def fix():
    conn = sqlite3.connect('d:/finance product/backend/zetamize.db')
    cursor = conn.cursor()
    
    # helper to add column if not exists
    def add_col(table, col, type_def):
        try:
            # Use double quotes for table name and column name
            cursor.execute(f'ALTER TABLE "{table}" ADD COLUMN "{col}" {type_def}')
            print(f"Added {col} to {table}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col} already exists in {table}")
            else:
                print(f"Error adding {col} to {table}: {e}")

    # User table additions
    add_col("user", "bank_balance", "FLOAT DEFAULT 0.0")
    
    # Milestone additions
    add_col("milestone", "tax_amount", "FLOAT DEFAULT 0.0")
    add_col("milestone", "tax_type", "TEXT")
    
    # Vendor & Bill tables might not exist if create_all failed or didn't run
    # But usually SQLModel handles table creation. 
    # Just in case, try adding columns to them too
    add_col("vendorbill", "tax_amount", "FLOAT DEFAULT 0.0")
    add_col("vendorbill", "tax_type", "TEXT")
    
    # Transaction additions (use quotes for table name "transaction")
    add_col("transaction", "tax_amount", "FLOAT DEFAULT 0.0")
    add_col("transaction", "tax_type", "TEXT")
    add_col("transaction", "vendor_id", "INTEGER")
    add_col("transaction", "vendor_bill_id", "INTEGER")
    add_col("transaction", "recurring_id", "INTEGER")
    
    # Vendor new columns
    add_col("vendor", "description", "TEXT")
    add_col("vendor", "opening_balance", "FLOAT DEFAULT 0.0")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix()
