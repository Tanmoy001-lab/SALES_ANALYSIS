# ⚡ RetailPulse AI — Enterprise Retail Sales Analytics & Machine Learning Platform

An enterprise-grade, full-stack Retail Sales Analytics and Machine Learning web application built on top of your team's dataset (`sales.csv`, `retail_sales.db`) and exploratory data science notebook (`01_Data_Exploration.ipynb`).

---

## 🌟 Highlights & Key Features

### 1. 🔐 User Authentication & Role-Based Access Control
- **Dual User Roles**:
  - **👑 Administrator (`admin`)**: Full system clearance. Can view dashboards, perform ML predictions, add/edit/delete sales records, upload new CSV datasets, and trigger on-demand model re-training.
  - **💼 Retail Analyst (`user`)**: Read-only business intelligence access. Can view all analytics, explore trends, run what-if ML predictions, analyze customer clusters, and export CSV reports.
- **One-Click Demo Login**: Switch roles instantly without typing credentials:
  - **Admin**: `admin@retailsales.com` / `admin123`
  - **Analyst**: `user@retailsales.com` / `user123`
- Secure password hashing using PBKDF2 / SHA-256 via `werkzeug.security`.
- Session persistence and quick role switcher menu in the navigation bar.

---

### 2. 📊 Executive Overview Dashboard
- **Real-Time KPI Cards**: Total Revenue, Gross Profit, Profit Margin (%), Total Orders, and Return Rate (%).
- **Interactive Global Filters**: Filter by Region (*North, South, East, West, Central*) or Category (*Electronics, Home & Kitchen, Clothing, Furniture, Sports*) with instant reactive chart updates.
- **Monthly Revenue & Profit Trajectory**: Interactive Chart.js spline line chart with gradient fills.
- **Category Performance**: Stacked bar comparison of sales volume vs profit per category.
- **Top 10 Products**: Horizontal ranking of best-selling inventory items.
- **Regional Distribution**: Donut chart detailing geographic revenue share.

---

### 3. 🤖 Machine Learning Studio (Trained Scikit-Learn Models)
- **Real ML Sales Predictor**:
  - Powered by a real trained **`RandomForestRegressor(n_estimators=100, max_depth=15)`** pipeline with `ColumnTransformer`, `StandardScaler`, and `OneHotEncoder`.
  - Input sliders & controls: Quantity (1–50), Unit Price ($1–$2000), Discount (0–60%), Category, Region, Segment, Order Priority, Delivery Days, Customer Rating.
  - Real-time calculation card showing Forecasted Sales, Gross Revenue, Discount Impact, Estimated Operational Profit, and Margin %.
- **Model Benchmarking & Comparison Table**:
  - Evaluated on a 20% holdout test set (2,020 samples).
  - Side-by-side comparison between **Random Forest Regressor** and **Multiple Linear Regression** displaying $R^2$ Score, RMSE, and MAE.
- **Feature Importance Chart**:
  - Visual breakdown of the most critical variables driving sales (Quantity, Unit Price, Discount, Category, etc.).
- **Customer RFM Segmentation (K-Means Clustering, K=4)**:
  - Generates RFM metrics (*Recency, Frequency, Monetary*) across 3,673 unique customers.
  - Identifies 4 archetypes:
    1. 💎 **VIP Platinum Customers**: Highest monetary spend ($2.5M+), frequent buyers.
    2. 🚀 **Frequent High-Value Shoppers**: Loyal buyers with high order frequency.
    3. 🛒 **Regular Shoppers**: Steady everyday purchasers.
    4. ⚠️ **Dormant / At-Risk Customers**: Long recency gap requiring win-back campaigns.
  - Interactive 2D scatter chart displaying Recency vs Monetary spend per cluster.

---

### 4. 🔬 Deep-Dive Exploratory Data Analysis (EDA)
- **Feature Correlation Matrix Heatmap**: Interactive, color-coded grid visualizing Pearson correlation coefficients between numeric variables (-1.0 to +1.0) with hover tooltips.
- **Sales Outlier Detection**: Statistical IQR analysis displaying Q1, Median, Q3, Upper Threshold, Max Sales, and an extreme outlier orders table.
- **Product Performance Quadrant**: Scatter plot correlating Total Sales vs Total Profit to discover high-margin stars vs loss leaders.
- **Top Return Rate Products**: Bar chart displaying items with the highest return frequencies.

---

### 5. 📋 Transactions & Data Explorer (CRUD)
- Paginated table browsing the 10,100 sales records in SQLite.
- Live search by Customer Name, Order ID, Product Name, and City.
- Multi-column filtering by Region and Category.
- CSV dataset export button.
- **Admin CRUD Operations**:
  - **➕ Add Transaction**: Modal form to insert a new sale into SQLite.
  - **✏️ Edit Transaction**: Modal to modify existing orders.
  - **🗑️ Delete Transaction**: One-click deletion with confirmation dialog.

---

### 6. 🛡️ Admin Control Center
- **System Health Diagnostics**: Live record count, database file size (MB), registered users count, and model training status.
- **Batch CSV Dataset Ingestion**: Upload a new `.csv` file to append records and trigger automatic model re-training.
- **On-Demand Retraining**: One-click button to re-fit Random Forest and K-Means models directly from the UI.

---

## 🚀 Running the Application Locally

### Prerequisites
- Python 3.10+ (Anaconda or standard Python)
- Required packages: `flask`, `pandas`, `numpy`, `scikit-learn`, `joblib`

### Start the Server
```bash
python app.py
```
The server will start at:
```
http://127.0.0.1:5000
```

### Default Credentials
| Role | Email | Password | Clearance |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@retailsales.com` | `admin123` | Full Admin + CRUD + Retrain |
| **Retail Analyst** | `user@retailsales.com` | `user123` | Analytics + ML + Export |

*(You can also use the 1-click demo login buttons directly in the interface!)*

---

## 📁 Project Architecture

```
.
├── app.py                  # Master Flask application & RESTful API endpoints
├── database.py             # SQLite database layer, user authentication & transactions CRUD
├── ml_service.py           # Scikit-Learn ML pipelines (Random Forest, Linear Regression, RFM K-Means)
├── retail_sales.db         # SQLite database storing 10,100 sales records and user accounts
├── sales.csv               # Raw dataset
├── models/                 # Serialized models and metrics
│   ├── sales_rf_model.joblib
│   ├── model_metrics.json
│   └── clusters_data.json
├── static/
│   ├── css/
│   │   └── styles.css      # Enterprise design system, glassmorphism, responsive styles
│   └── js/
│       ├── app.js          # Main SPA controller (Auth, Chart.js, ML inference, CRUD, Toast)
│       └── dashboard.js    # Teammate's original chart script (preserved)
├── templates/
│   └── index.html          # Modern HTML5 responsive user interface
└── notebooks/
    └── 01_Data_Exploration.ipynb # Exploratory data science & ML research notebook
```
