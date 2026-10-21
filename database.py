import pandas as pd
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DB_FILE = os.path.join(os.path.dirname(__file__), "retail_sales.db")
CSV_FILE = os.path.join(os.path.dirname(__file__), "sales.csv")

def get_connection(db_filepath=DB_FILE):
    conn = sqlite3.connect(db_filepath)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(csv_filepath=CSV_FILE, db_filepath=DB_FILE):
    conn = sqlite3.connect(db_filepath)
    cursor = conn.cursor()

    # 1. Create Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. Seed Default Admin and User if not already present
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'admin@retailsales.com'")
    if cursor.fetchone()[0] == 0:
        admin_hash = generate_password_hash("admin123")
        cursor.execute("""
            INSERT INTO users (username, email, name, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("admin", "admin@retailsales.com", "Admin Astha", admin_hash, "admin"))

    cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'user@retailsales.com'")
    if cursor.fetchone()[0] == 0:
        user_hash = generate_password_hash("user123")
        cursor.execute("""
            INSERT INTO users (username, email, name, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("user", "user@retailsales.com", "Alex Morgan", user_hash, "user"))

    # Seed Admin for mithusahoo943@gmail.com
    cursor.execute("SELECT COUNT(*) FROM users WHERE email = 'mithusahoo943@gmail.com'")
    if cursor.fetchone()[0] == 0:
        admin_hash = generate_password_hash("admin123")
        cursor.execute("""
            INSERT INTO users (username, email, name, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, ("mithu", "mithusahoo943@gmail.com", "Mithu Sahoo", admin_hash, "admin"))
    else:
        cursor.execute("UPDATE users SET role = 'admin' WHERE email = 'mithusahoo943@gmail.com'")

    # 3. Check if sales table exists; if not or if empty, load from CSV
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sales'")
    sales_table_exists = cursor.fetchone()

    should_load_csv = False
    if not sales_table_exists:
        should_load_csv = True
    else:
        cursor.execute("SELECT COUNT(*) FROM sales")
        if cursor.fetchone()[0] == 0:
            should_load_csv = True

    conn.commit()
    conn.close()

    if should_load_csv and os.path.exists(csv_filepath):
        print("Importing sales data from CSV...")
        df = pd.read_csv(csv_filepath)
        df['Order_Date'] = pd.to_datetime(df['Order_Date'], format='%d-%m-%Y', errors='coerce')
        df['Ship_Date'] = pd.to_datetime(df['Ship_Date'], format='%d-%m-%Y', errors='coerce')

        df['Email'] = df['Email'].fillna('unknown@example.com')
        df['Phone'] = df['Phone'].fillna(0)
        df['Discount'] = df['Discount'].fillna(0.0)
        if 'Customer_Rating' in df.columns:
            df['Customer_Rating'] = df['Customer_Rating'].fillna(df['Customer_Rating'].mean())

        df['Order_Date'] = df['Order_Date'].dt.strftime('%Y-%m-%d')
        df['Ship_Date'] = df['Ship_Date'].dt.strftime('%Y-%m-%d')

        conn = sqlite3.connect(db_filepath)
        df.to_sql('sales', conn, if_exists='replace', index=False)
        conn.close()
        print("Database initialized successfully with sales dataset.")
    else:
        print("Database schema checked; sales data and users ready.")

# --- User & Auth Operations ---
def get_user_by_email(email, db_filepath=DB_FILE):
    conn = get_connection(db_filepath)
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id, db_filepath=DB_FILE):
    conn = get_connection(db_filepath)
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(username, email, name, password, role="user", db_filepath=DB_FILE):
    password_hash = generate_password_hash(password)
    conn = get_connection(db_filepath)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (username, email, name, password_hash, role)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, name, password_hash, role))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return get_user_by_id(new_id, db_filepath)
    except sqlite3.IntegrityError as e:
        conn.close()
        raise ValueError(f"User with this email or username already exists. {e}")

def verify_user(email, password, db_filepath=DB_FILE):
    user = get_user_by_email(email, db_filepath)
    if not user:
        return None
    if check_password_hash(user['password_hash'], password):
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"]
        }
    return None

def list_all_users(db_filepath=DB_FILE):
    conn = get_connection(db_filepath)
    users = conn.execute("SELECT id, username, email, name, role, created_at FROM users ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(u) for u in users]

ADMIN_EMAILS = {"admin@retailsales.com", "mithusahoo943@gmail.com"}

def get_or_create_google_user(email, name, db_filepath=DB_FILE):
    import secrets
    # Grant full ADMIN privileges to all Google-authenticated accounts (Mithu and all teammates)
    target_role = "admin"

    existing = get_user_by_email(email, db_filepath)
    if existing:
        if existing["role"] != "admin":
            conn = get_connection(db_filepath)
            conn.execute("UPDATE users SET role = 'admin' WHERE id = ?", (existing["id"],))
            conn.commit()
            conn.close()
            existing["role"] = "admin"

        return {
            "id": existing["id"],
            "username": existing["username"],
            "email": existing["email"],
            "name": existing["name"],
            "role": existing["role"]
        }
    
    base_username = email.split("@")[0].replace(".", "_")
    username = base_username
    counter = 1
    conn = get_connection(db_filepath)
    while conn.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
        username = f"{base_username}_{counter}"
        counter += 1
    conn.close()

    random_pwd = secrets.token_urlsafe(16)
    new_user = create_user(username, email, name or username, random_pwd, role=target_role, db_filepath=db_filepath)
    return {
        "id": new_user["id"],
        "username": new_user["username"],
        "email": new_user["email"],
        "name": new_user["name"],
        "role": new_user["role"]
    }

# --- Sales Transactions CRUD ---
def get_transactions(limit=15, offset=0, search=None, region=None, category=None, sort_by="Order_Date", sort_order="DESC", db_filepath=DB_FILE):
    conn = get_connection(db_filepath)
    query = "SELECT * FROM sales WHERE 1=1"
    params = []

    if search:
        search_term = f"%{search}%"
        query += " AND (Customer_Name LIKE ? OR Order_ID LIKE ? OR Product_Name LIKE ? OR City LIKE ?)"
        params.extend([search_term, search_term, search_term, search_term])

    if region and region != "All":
        query += " AND Region = ?"
        params.append(region)

    if category and category != "All":
        query += " AND Category = ?"
        params.append(category)

    # Valid sort columns whitelist
    valid_cols = ["Order_Date", "Sales", "Profit", "Customer_Name", "Order_ID", "Quantity", "Discount"]
    if sort_by not in valid_cols:
        sort_by = "Order_Date"
    sort_order = "ASC" if sort_order.upper() == "ASC" else "DESC"

    query += f" ORDER BY {sort_by} {sort_order} LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    rows = conn.execute(query, params).fetchall()

    # Get total count with same filters
    count_query = "SELECT COUNT(*) FROM sales WHERE 1=1"
    count_params = []
    if search:
        search_term = f"%{search}%"
        count_query += " AND (Customer_Name LIKE ? OR Order_ID LIKE ? OR Product_Name LIKE ? OR City LIKE ?)"
        count_params.extend([search_term, search_term, search_term, search_term])
    if region and region != "All":
        count_query += " AND Region = ?"
        count_params.append(region)
    if category and category != "All":
        count_query += " AND Category = ?"
        count_params.append(category)

    total_count = conn.execute(count_query, count_params).fetchone()[0]
    conn.close()

    return {
        "items": [dict(r) for r in rows],
        "total": total_count,
        "limit": limit,
        "offset": offset
    }

def insert_transaction(data, db_filepath=DB_FILE):
    conn = get_connection(db_filepath)
    cursor = conn.cursor()

    columns = [
        "Order_ID", "Order_Date", "Ship_Date", "Customer_ID", "Customer_Name",
        "Gender", "Age", "Email", "Phone", "Region", "State", "City",
        "Product_ID", "Product_Name", "Category", "Brand", "Quantity",
        "Unit_Price", "Discount", "Sales", "Cost", "Profit", "Payment_Mode",
        "Order_Priority", "Customer_Segment", "Delivery_Days", "Customer_Rating", "Returned"
    ]

    # Calculate derived values if missing
    qty = float(data.get("Quantity", 1))
    price = float(data.get("Unit_Price", 100))
    disc = float(data.get("Discount", 0))
    sales = float(data.get("Sales", round(qty * price * (1 - disc / 100.0), 2)))
    cost = float(data.get("Cost", round(sales * 0.8, 2)))
    profit = float(data.get("Profit", round(sales - cost, 2)))

    values = [
        data.get("Order_ID"),
        data.get("Order_Date", "2024-01-01"),
        data.get("Ship_Date", "2024-01-03"),
        data.get("Customer_ID", "CUST-9999"),
        data.get("Customer_Name", "New Customer"),
        data.get("Gender", "Other"),
        int(data.get("Age", 30)),
        data.get("Email", "cust@example.com"),
        data.get("Phone", 0),
        data.get("Region", "North"),
        data.get("State", "Delhi"),
        data.get("City", "New Delhi"),
        data.get("Product_ID", "PROD-9999"),
        data.get("Product_Name", "Sample Product"),
        data.get("Category", "Electronics"),
        data.get("Brand", "Generic"),
        qty,
        price,
        disc,
        sales,
        cost,
        profit,
        data.get("Payment_Mode", "Credit Card"),
        data.get("Order_Priority", "Medium"),
        data.get("Customer_Segment", "Regular"),
        int(data.get("Delivery_Days", 3)),
        float(data.get("Customer_Rating", 4.0)),
        data.get("Returned", "No")
    ]

    placeholders = ",".join(["?"] * len(columns))
    col_str = ",".join(columns)

    cursor.execute(f"INSERT INTO sales ({col_str}) VALUES ({placeholders})", values)
    conn.commit()
    conn.close()
    return True

def update_transaction(order_id, data, db_filepath=DB_FILE):
    conn = get_connection(db_filepath)
    cursor = conn.cursor()

    updatable = [
        "Customer_Name", "Region", "Category", "Product_Name",
        "Quantity", "Unit_Price", "Discount", "Sales", "Profit",
        "Order_Priority", "Customer_Segment", "Returned", "Payment_Mode"
    ]

    clauses = []
    values = []
    for col in updatable:
        if col in data:
            clauses.append(f"{col} = ?")
            values.append(data[col])

    if not clauses:
        conn.close()
        return False

    values.append(order_id)
    query = f"UPDATE sales SET {', '.join(clauses)} WHERE Order_ID = ?"
    cursor.execute(query, values)
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def delete_transaction(order_id, db_filepath=DB_FILE):
    conn = get_connection(db_filepath)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sales WHERE Order_ID = ?", (order_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_system_stats(db_filepath=DB_FILE):
    conn = get_connection(db_filepath)
    sales_count = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_sales = conn.execute("SELECT SUM(Sales) FROM sales").fetchone()[0] or 0.0
    total_profit = conn.execute("SELECT SUM(Profit) FROM sales").fetchone()[0] or 0.0
    conn.close()

    db_size_mb = 0.0
    if os.path.exists(db_filepath):
        db_size_mb = round(os.path.getsize(db_filepath) / (1024 * 1024), 2)

    return {
        "total_records": sales_count,
        "total_users": users_count,
        "total_revenue": round(float(total_sales), 2),
        "total_profit": round(float(total_profit), 2),
        "database_size_mb": db_size_mb
    }

if __name__ == "__main__":
    init_db()