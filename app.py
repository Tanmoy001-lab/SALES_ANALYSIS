import os
import io
import sqlite3
import pandas as pd
import numpy as np
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from authlib.integrations.flask_client import OAuth
import database
import ml_service

# Load environment variables (.env)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "super-secure-retail-analytics-secret-2026")
DB_PATH = os.path.join(os.path.dirname(__file__), "retail_sales.db")

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Ensure database and initial ML models are initialized
database.init_db()
try:
    if not os.path.exists(ml_service.SALES_MODEL_PATH):
        print("Training initial ML models...")
        ml_service.train_sales_models(DB_PATH)
except Exception as e:
    print(f"Initial model training notice: {e}")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
    return response

def build_filter_clause(request_args):
    """Helper to extract region and category filters from query params"""
    clauses = []
    params = []
    region = request_args.get("region")
    category = request_args.get("category")

    if region and region != "All":
        clauses.append("Region = ?")
        params.append(region)
    if category and category != "All":
        clauses.append("Category = ?")
        params.append(category)

    where_str = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where_str, params

# ==========================================
# PAGE ROUTES
# ==========================================
@app.route("/")
def index():
    return render_template("index.html")

# ==========================================
# AUTHENTICATION API
# ==========================================
@app.route("/api/v1/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json() or {}
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = database.verify_user(email, password, DB_PATH)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    session["user"] = user
    return jsonify({"success": True, "user": user, "message": f"Welcome back, {user['name']}!"})

@app.route("/api/v1/auth/quick-login", methods=["POST"])
def auth_quick_login():
    data = request.get_json() or {}
    role = data.get("role", "user")

    if role == "admin":
        user = database.get_user_by_email("admin@retailsales.com", DB_PATH)
    else:
        user = database.get_user_by_email("user@retailsales.com", DB_PATH)

    if not user:
        return jsonify({"error": f"Default {role} user not found"}), 404

    clean_user = {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"]
    }
    session["user"] = clean_user
    return jsonify({"success": True, "user": clean_user, "message": f"Logged in as {clean_user['name']} ({clean_user['role'].upper()})"})

@app.route("/api/v1/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    name = data.get("name", "").strip()
    password = data.get("password", "").strip()
    role = data.get("role", "user").strip()

    if role not in ["admin", "user"]:
        role = "user"

    if not username or not email or not password or not name:
        return jsonify({"error": "Please fill out all required fields"}), 400

    try:
        new_user = database.create_user(username, email, name, password, role, DB_PATH)
        clean_user = {
            "id": new_user["id"],
            "username": new_user["username"],
            "email": new_user["email"],
            "name": new_user["name"],
            "role": new_user["role"]
        }
        session["user"] = clean_user
        return jsonify({"success": True, "user": clean_user, "message": "Account created successfully!"})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to register: {str(e)}"}), 500

@app.route("/api/v1/auth/logout", methods=["POST"])
def auth_logout():
    session.pop("user", None)
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route("/api/v1/auth/me", methods=["GET"])
def auth_me():
    user = session.get("user")
    if not user:
        return jsonify({"authenticated": False, "user": None}), 200
    return jsonify({"authenticated": True, "user": user})

@app.route("/api/v1/auth/google-login")
def auth_google_login():
    redirect_uri = url_for("auth_google_callback", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route("/api/v1/auth/google-callback")
def auth_google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get("userinfo")
        if not user_info:
            user_info = oauth.google.userinfo()
        
        email = user_info.get("email")
        name = user_info.get("name") or (email.split("@")[0] if email else "Google User")
        picture = user_info.get("picture")

        if not email:
            return redirect("/?auth=error&msg=No+email+returned+from+Google")

        user = database.get_or_create_google_user(email, name, DB_PATH)
        if picture:
            user["picture"] = picture
        
        session["user"] = user
        return redirect("/?auth=success")
    except Exception as e:
        print(f"OAuth Callback Error: {e}")
        return redirect(f"/?auth=error&msg=Google+Login+Failed")

# ==========================================
# ANALYTICS & EDA APIS
# ==========================================
@app.route("/api/v1/filter-options", methods=["GET"])
def get_filter_options():
    try:
        conn = get_db_connection()
        regions = [r[0] for r in conn.execute("SELECT DISTINCT Region FROM sales WHERE Region IS NOT NULL ORDER BY Region").fetchall()]
        categories = [r[0] for r in conn.execute("SELECT DISTINCT Category FROM sales WHERE Category IS NOT NULL ORDER BY Category").fetchall()]
        segments = [r[0] for r in conn.execute("SELECT DISTINCT Customer_Segment FROM sales WHERE Customer_Segment IS NOT NULL ORDER BY Customer_Segment").fetchall()]
        payments = [r[0] for r in conn.execute("SELECT DISTINCT Payment_Mode FROM sales WHERE Payment_Mode IS NOT NULL ORDER BY Payment_Mode").fetchall()]
        priorities = [r[0] for r in conn.execute("SELECT DISTINCT Order_Priority FROM sales WHERE Order_Priority IS NOT NULL ORDER BY Order_Priority").fetchall()]
        conn.close()

        return jsonify({
            "regions": regions,
            "categories": categories,
            "segments": segments,
            "payments": payments,
            "priorities": priorities
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/kpis", methods=["GET"])
def get_kpis():
    try:
        where_clause, params = build_filter_clause(request.args)
        conn = get_db_connection()
        query = f"SELECT Sales, Profit, Order_ID, Returned, Customer_Rating FROM sales {where_clause}"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return jsonify({
                "total_sales": 0.0,
                "total_profit": 0.0,
                "profit_margin": 0.0,
                "total_orders": 0,
                "avg_rating": 0.0,
                "return_rate": 0.0
            })

        total_sales = float(df['Sales'].sum())
        total_profit = float(df['Profit'].sum())
        total_orders = int(df['Order_ID'].nunique())
        avg_rating = float(df['Customer_Rating'].dropna().mean()) if not df['Customer_Rating'].dropna().empty else 0.0
        
        is_returned = df['Returned'].astype(str).str.lower().isin(['yes', '1', 'true'])
        return_rate = float(is_returned.mean() * 100)
        profit_margin = float((total_profit / total_sales) * 100) if total_sales > 0 else 0.0

        return jsonify({
            "total_sales": round(total_sales, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin": round(profit_margin, 2),
            "total_orders": total_orders,
            "avg_rating": round(avg_rating, 2),
            "return_rate": round(return_rate, 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/sales-trend", methods=["GET"])
def get_sales_trend():
    try:
        where_clause, params = build_filter_clause(request.args)
        conn = get_db_connection()
        query = f"SELECT Order_Date, Sales, Profit FROM sales {where_clause}"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return jsonify({"labels": [], "sales": [], "profit": []})

        df['Order_Date'] = pd.to_datetime(df['Order_Date'], errors='coerce')
        df = df.dropna(subset=['Order_Date'])

        df['Month'] = df['Order_Date'].dt.to_period('M').astype(str)
        monthly = df.groupby('Month').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
        monthly = monthly.sort_values('Month')

        return jsonify({
            "labels": monthly['Month'].tolist(),
            "sales": monthly['Sales'].round(2).tolist(),
            "profit": monthly['Profit'].round(2).tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/category-performance", methods=["GET"])
def get_category_performance():
    try:
        where_clause, params = build_filter_clause(request.args)
        conn = get_db_connection()
        query = f"SELECT Category, Sales, Profit FROM sales {where_clause}"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return jsonify({"categories": [], "sales": [], "profit": []})

        cat_df = df.groupby('Category').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
        cat_df = cat_df.sort_values(by='Sales', ascending=False)

        return jsonify({
            "categories": cat_df['Category'].tolist(),
            "sales": cat_df['Sales'].round(2).tolist(),
            "profit": cat_df['Profit'].round(2).tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/top-products", methods=["GET"])
def get_top_products():
    try:
        where_clause, params = build_filter_clause(request.args)
        conn = get_db_connection()
        query = f"SELECT Product_Name, Sales FROM sales {where_clause}"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return jsonify({"products": [], "sales": []})

        top_df = df.groupby('Product_Name')['Sales'].sum().nlargest(10).reset_index()

        return jsonify({
            "products": top_df['Product_Name'].tolist(),
            "sales": top_df['Sales'].round(2).tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/region-sales", methods=["GET"])
def get_region_sales():
    try:
        where_clause, params = build_filter_clause(request.args)
        conn = get_db_connection()
        query = f"SELECT Region, Sales, Profit FROM sales {where_clause}"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return jsonify({"regions": [], "sales": [], "profit": []})

        reg_df = df.groupby('Region').agg({'Sales': 'sum', 'Profit': 'sum'}).reset_index()
        reg_df = reg_df.sort_values(by='Sales', ascending=False)

        return jsonify({
            "regions": reg_df['Region'].tolist(),
            "sales": reg_df['Sales'].round(2).tolist(),
            "profit": reg_df['Profit'].round(2).tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/customer-segments", methods=["GET"])
def get_customer_segments():
    try:
        where_clause, params = build_filter_clause(request.args)
        conn = get_db_connection()
        query = f"SELECT Customer_Segment, COUNT(DISTINCT Customer_ID) as count, SUM(Sales) as total_sales FROM sales {where_clause} GROUP BY Customer_Segment"
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return jsonify({
            "segments": df['Customer_Segment'].tolist(),
            "counts": df['count'].tolist(),
            "sales": [round(s, 2) for s in df['total_sales'].tolist()]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/correlation", methods=["GET"])
def get_correlation():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Age, Quantity, Unit_Price, Discount, Sales, Cost, Profit, Delivery_Days, Customer_Rating FROM sales", conn)
        conn.close()

        numeric_df = df.apply(pd.to_numeric, errors='coerce').fillna(0)
        numeric_df = numeric_df.loc[:, (numeric_df != numeric_df.iloc[0]).any()]
        corr = numeric_df.corr().fillna(0).round(3)

        return jsonify({
            "features": corr.columns.tolist(),
            "matrix": corr.values.tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/sales-outliers", methods=["GET"])
def get_sales_outliers():
    try:
        conn = get_db_connection()
        df = pd.read_sql_query("SELECT Sales, Order_ID, Product_Name, Customer_Name FROM sales", conn)
        conn.close()

        sales = pd.to_numeric(df['Sales'], errors='coerce').dropna().sort_values().values
        if len(sales) == 0:
            return jsonify({"error": "No sales data available"}), 400

        q1 = float(np.percentile(sales, 25))
        median = float(np.median(sales))
        q3 = float(np.percentile(sales, 75))
        iqr = q3 - q1

        lower_bound = float(max(sales.min(), q1 - 1.5 * iqr))
        upper_bound = float(q3 + 1.5 * iqr)

        outliers = [float(x) for x in sales if x > upper_bound or x < lower_bound]

        # Top 10 extreme transactions
        extreme_df = df[df['Sales'] > upper_bound].sort_values(by='Sales', ascending=False).head(10)
        extreme_records = extreme_df.to_dict(orient='records')

        return jsonify({
            "min": round(float(sales.min()), 2),
            "q1": round(q1, 2),
            "median": round(median, 2),
            "q3": round(q3, 2),
            "max": round(float(sales.max()), 2),
            "lower_bound": round(lower_bound, 2),
            "upper_bound": round(upper_bound, 2),
            "outlier_count": len(outliers),
            "outlier_percentage": round((len(outliers) / len(sales)) * 100, 2),
            "extreme_records": extreme_records
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/product-performance", methods=["GET"])
def get_product_performance():
    try:
        where_clause, params = build_filter_clause(request.args)
        conn = get_db_connection()
        query = f"""
            SELECT Product_Name, Category, SUM(Sales) as Total_Sales, SUM(Profit) as Total_Profit, COUNT(*) as Orders
            FROM sales {where_clause}
            GROUP BY Product_Name, Category
            ORDER BY Total_Sales DESC
            LIMIT 40
        """
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        data_points = [
            {
                "x": round(float(row['Total_Sales']), 2),
                "y": round(float(row['Total_Profit']), 2),
                "name": str(row['Product_Name']),
                "category": str(row['Category']),
                "orders": int(row['Orders'])
            }
            for _, row in df.iterrows()
        ]

        return jsonify({"products": data_points})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/top-return-products", methods=["GET"])
def get_top_return_products():
    try:
        where_clause, params = build_filter_clause(request.args)
        and_clause = (" AND " + where_clause[7:]) if where_clause else ""
        conn = get_db_connection()
        query = f"""
            SELECT 
                Product_Name,
                Category,
                COUNT(*) AS Total_Orders,
                SUM(CASE WHEN LOWER(CAST(Returned AS TEXT)) IN ('yes', '1', 'true') THEN 1 ELSE 0 END) AS Returned_Orders
            FROM sales
            WHERE 1=1 {and_clause}
            GROUP BY Product_Name, Category
            HAVING Total_Orders >= 5
        """
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if df.empty:
            return jsonify({"products": [], "return_rates": [], "total_orders": [], "returned_orders": []})

        df['Return_Rate'] = (df['Returned_Orders'] / df['Total_Orders']) * 100
        df_top = df.sort_values(by='Return_Rate', ascending=False).head(10)

        return jsonify({
            "products": df_top['Product_Name'].tolist(),
            "categories": df_top['Category'].tolist(),
            "return_rates": [round(val, 2) for val in df_top['Return_Rate'].tolist()],
            "total_orders": df_top['Total_Orders'].tolist(),
            "returned_orders": df_top['Returned_Orders'].tolist()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# MACHINE LEARNING ENGINE APIS
# ==========================================
@app.route("/api/v1/predict", methods=["POST"])
@app.route("/api/v1/ml/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json() or {}
        result = ml_service.predict_sales_record(data, db_path=DB_PATH)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@app.route("/api/v1/ml/metrics", methods=["GET"])
def get_ml_metrics():
    try:
        metrics = ml_service.get_metrics_info(db_path=DB_PATH)
        if not metrics:
            return jsonify({"error": "Metrics not available"}), 404
        return jsonify(metrics)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/ml/clusters", methods=["GET"])
def get_ml_clusters():
    try:
        clusters = ml_service.get_clusters_info(db_path=DB_PATH)
        if not clusters:
            return jsonify({"error": "Clusters not available"}), 404
        return jsonify(clusters)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/ml/train", methods=["POST"])
def retrain_ml_models():
    # Only Admin should be allowed to retrain
    user = session.get("user")
    if user and user.get("role") != "admin":
        return jsonify({"error": "Admin privileges required to retrain ML models."}), 403

    try:
        metrics = ml_service.train_sales_models(DB_PATH)
        return jsonify({
            "success": True,
            "message": "Machine learning models retrained and serialized successfully!",
            "metrics": metrics
        })
    except Exception as e:
        return jsonify({"error": f"Model retraining failed: {str(e)}"}), 500

# ==========================================
# TRANSACTIONS CRUD & DATASET MANAGEMENT
# ==========================================
@app.route("/api/v1/transactions", methods=["GET"])
def get_transactions_list():
    try:
        limit = min(100, max(1, int(request.args.get("limit", 15))))
        offset = max(0, int(request.args.get("offset", 0)))
        search = request.args.get("search", "").strip() or None
        region = request.args.get("region", "").strip() or None
        category = request.args.get("category", "").strip() or None
        sort_by = request.args.get("sort_by", "Order_Date")
        sort_order = request.args.get("sort_order", "DESC")

        data = database.get_transactions(
            limit=limit,
            offset=offset,
            search=search,
            region=region,
            category=category,
            sort_by=sort_by,
            sort_order=sort_order,
            db_filepath=DB_PATH
        )
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/transactions", methods=["POST"])
def create_transaction():
    user = session.get("user")
    if user and user.get("role") != "admin":
        return jsonify({"error": "Admin privileges required to insert records."}), 403

    try:
        payload = request.get_json() or {}
        if not payload.get("Order_ID"):
            import time
            payload["Order_ID"] = f"ORD{int(time.time())}"

        success = database.insert_transaction(payload, db_filepath=DB_PATH)
        return jsonify({"success": success, "message": f"Order {payload['Order_ID']} created successfully!"})
    except Exception as e:
        return jsonify({"error": f"Creation failed: {str(e)}"}), 500

@app.route("/api/v1/transactions/<order_id>", methods=["PUT"])
def update_transaction(order_id):
    user = session.get("user")
    if user and user.get("role") != "admin":
        return jsonify({"error": "Admin privileges required to edit records."}), 403

    try:
        payload = request.get_json() or {}
        success = database.update_transaction(order_id, payload, db_filepath=DB_PATH)
        if not success:
            return jsonify({"error": "Record not found or nothing updated"}), 404
        return jsonify({"success": True, "message": f"Order {order_id} updated successfully!"})
    except Exception as e:
        return jsonify({"error": f"Update failed: {str(e)}"}), 500

@app.route("/api/v1/transactions/<order_id>", methods=["DELETE"])
def delete_transaction(order_id):
    user = session.get("user")
    if user and user.get("role") != "admin":
        return jsonify({"error": "Admin privileges required to delete records."}), 403

    try:
        success = database.delete_transaction(order_id, db_filepath=DB_PATH)
        if not success:
            return jsonify({"error": "Record not found"}), 404
        return jsonify({"success": True, "message": f"Order {order_id} deleted successfully!"})
    except Exception as e:
        return jsonify({"error": f"Delete failed: {str(e)}"}), 500

@app.route("/api/v1/export-csv", methods=["GET"])
def export_csv():
    try:
        where_clause, params = build_filter_clause(request.args)
        conn = get_db_connection()
        df = pd.read_sql_query(f"SELECT * FROM sales {where_clause} LIMIT 2000", conn, params=params)
        conn.close()

        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype="text/csv",
            as_attachment=True,
            download_name="retail_sales_export.csv"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/v1/upload-csv", methods=["POST"])
def upload_csv():
    user = session.get("user")
    if user and user.get("role") != "admin":
        return jsonify({"error": "Admin privileges required to upload datasets."}), 403

    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        df = pd.read_csv(file)
        if 'Order_ID' not in df.columns or 'Sales' not in df.columns:
            return jsonify({"error": "Uploaded CSV must contain at least 'Order_ID' and 'Sales' columns."}), 400

        # Append or merge to sales table
        conn = sqlite3.connect(DB_PATH)
        df.to_sql('sales', conn, if_exists='append', index=False)
        conn.close()

        # Re-train models with the new data
        ml_service.train_sales_models(DB_PATH)

        return jsonify({
            "success": True,
            "message": f"Uploaded {len(df)} records. Models retrained successfully!"
        })
    except Exception as e:
        return jsonify({"error": f"Upload processing failed: {str(e)}"}), 500

@app.route("/api/v1/admin/stats", methods=["GET"])
def admin_stats():
    try:
        stats = database.get_system_stats(DB_PATH)
        metrics = ml_service.get_metrics_info(DB_PATH)
        stats["model_metrics"] = metrics.get("models") if metrics else None
        stats["last_trained"] = metrics.get("last_trained") if metrics else "N/A"
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)