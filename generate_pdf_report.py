import os
import base64
import subprocess

PROJECT_DIR = r"C:\Users\mithu\OneDrive\Desktop\New folder"
SCREENSHOTS_DIR = os.path.join(PROJECT_DIR, "screenshots")
HTML_REPORT_PATH = os.path.join(PROJECT_DIR, "vtop_report.html")
PDF_OUTPUT_PATH = os.path.join(PROJECT_DIR, "RetailPulse_AI_VTOP_Project_Submission.pdf")
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def get_base64_image(filename):
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    if not os.path.exists(filepath):
        return ""
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"

def build_html():
    img_overview = get_base64_image("01_Executive_Overview_Dashboard.png")
    img_ml = get_base64_image("02_AI_and_ML_Studio.png")
    img_clusters = get_base64_image("03_Customer_Segmentation_RFM_KMeans.png")
    img_eda = get_base64_image("04_Deep_Dive_EDA.png")
    img_trans = get_base64_image("05_Transactions_and_Data_CRUD.png")
    img_admin = get_base64_image("06_Admin_Console_Management.png")
    img_auth = get_base64_image("07_Authentication_Login_Modal.png")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>RetailPulse AI — VTOP Project Submission Report</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Outfit:wght@600;700;800&display=swap');

        @page {{
            size: A4 portrait;
            margin: 15mm 15mm 15mm 15mm;
        }}

        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: #1e293b;
            background: #ffffff;
            line-height: 1.5;
            margin: 0;
            padding: 0;
            font-size: 10pt;
        }}

        h1, h2, h3, h4 {{
            font-family: 'Outfit', sans-serif;
            color: #0f172a;
            margin-top: 0;
        }}

        .page-break {{
            page-break-before: always;
            break-before: page;
        }}

        /* Cover Page */
        .cover-page {{
            height: 90vh;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 40px 20px;
            box-sizing: border-box;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            background: linear-gradient(135deg, #f8fafc 0%, #edf4fc 100%);
        }}

        .cover-header {{
            border-bottom: 3px solid #10b981;
            padding-bottom: 20px;
        }}

        .cover-badge {{
            display: inline-block;
            background: #10b981;
            color: #ffffff;
            font-size: 9pt;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 9999px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 12px;
        }}

        .cover-title {{
            font-size: 26pt;
            font-weight: 800;
            line-height: 1.15;
            color: #0f172a;
            margin-bottom: 10px;
        }}

        .cover-subtitle {{
            font-size: 13pt;
            color: #475569;
            font-weight: 500;
        }}

        .meta-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            background: #ffffff;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #cbd5e1;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}

        .meta-item strong {{
            display: block;
            color: #64748b;
            font-size: 8.5pt;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .meta-item span {{
            font-size: 10.5pt;
            font-weight: 700;
            color: #0f172a;
        }}

        /* Content Sections */
        .section {{
            margin-bottom: 25px;
        }}

        .section-title {{
            font-size: 14pt;
            font-weight: 700;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 6px;
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
            color: #0f172a;
        }}

        .section-desc {{
            color: #475569;
            font-size: 9.5pt;
            margin-bottom: 12px;
        }}

        /* Screenshot Container */
        .screenshot-card {{
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            overflow: hidden;
            background: #090d16;
            margin-bottom: 14px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
        }}

        .screenshot-card img {{
            width: 100%;
            display: block;
            object-fit: contain;
        }}

        .highlight-box {{
            background: #f1f5f9;
            border-left: 4px solid #10b981;
            padding: 10px 14px;
            border-radius: 0 6px 6px 0;
            font-size: 9pt;
            color: #334155;
            margin-top: 10px;
        }}

        .highlight-box strong {{
            color: #0f172a;
        }}

        /* Table */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 8.5pt;
            margin-top: 10px;
        }}

        th, td {{
            padding: 8px 10px;
            border: 1px solid #cbd5e1;
            text-align: left;
        }}

        th {{
            background: #f8fafc;
            color: #334155;
            font-weight: 700;
            text-transform: uppercase;
        }}

        tr:nth-child(even) {{
            background: #f8fafc;
        }}
    </style>
</head>
<body>

    <!-- ==================== COVER PAGE ==================== -->
    <div class="cover-page">
        <div class="cover-header">
            <span class="cover-badge">VTOP Project Submission Report</span>
            <div class="cover-title">RetailPulse AI</div>
            <div class="cover-subtitle">Enterprise Retail Sales Analytics & Machine Learning Platform</div>
        </div>

        <div>
            <h3 style="color:#0f172a; margin-bottom:8px;">Project Overview</h3>
            <p style="color:#475569; font-size:10pt; line-height:1.6;">
                This project implements an end-to-end retail intelligence web application integrating real-time business KPIs, 
                exploratory data analysis (EDA), automated feature correlation matrix modeling, RFM customer segmentation clustering (K-Means, K=4), 
                and predictive sales forecasting powered by trained Scikit-Learn machine learning pipelines (Random Forest Regressor & Linear Regression). 
                The system features robust role-based access control (Admin vs Analyst) and full SQLite CRUD operations.
            </p>
        </div>

        <div class="meta-grid">
            <div class="meta-item">
                <strong>Project Domain</strong>
                <span>Data Science, Retail Analytics & ML</span>
            </div>
            <div class="meta-item">
                <strong>Backend & Database</strong>
                <span>Python Flask REST API, SQLite (10,100 Rows)</span>
            </div>
            <div class="meta-item">
                <strong>Machine Learning Models</strong>
                <span>Random Forest Regressor (R²≈65.0%), RFM K-Means</span>
            </div>
            <div class="meta-item">
                <strong>Frontend Architecture</strong>
                <span>Responsive Glassmorphism UI, Chart.js, HTML5/CSS3</span>
            </div>
        </div>

        <div style="font-size:8.5pt; color:#64748b; text-align:center; border-top:1px solid #cbd5e1; padding-top:10px;">
            Designed for University Examination & VTOP Academic Submission • Generated from Live Application
        </div>
    </div>

    <!-- ==================== SECTION 1: EXECUTIVE DASHBOARD ==================== -->
    <div class="page-break"></div>
    <div class="section">
        <div class="section-title">1. Executive Overview Dashboard</div>
        <div class="section-desc">
            Provides executive stakeholders with high-level visibility into key business metrics across 10,100 transactions. 
            Includes live KPI summary cards, interactive date/region filters, spline financial trajectories, category performance, and geographic revenue shares.
        </div>

        <div class="screenshot-card">
            <img src="{img_overview}" alt="Executive Overview Dashboard">
        </div>

        <div class="highlight-box">
            <strong>Key Analytics & Performance Metrics:</strong>
            <ul>
                <li><strong>Total Revenue:</strong> $2,629,072,992.80 across all recorded transactions.</li>
                <li><strong>Gross Profit:</strong> $478,155,019.90 with an operational profit margin of <strong>18.19%</strong>.</li>
                <li><strong>Total Orders:</strong> 10,000 distinct orders processed with a return rate of 52.24%.</li>
                <li><strong>Dynamic Visualizations:</strong> Monthly revenue spline curves, stacked category bars, and regional donut distribution.</li>
            </ul>
        </div>
    </div>

    <!-- ==================== SECTION 2: AI & ML STUDIO ==================== -->
    <div class="page-break"></div>
    <div class="section">
        <div class="section-title">2. Machine Learning Studio & Sales Forecasting</div>
        <div class="section-desc">
            Integrates trained Scikit-Learn regression pipelines to predict sales volume and profitability dynamically. 
            Features real-time interactive input sliders and side-by-side benchmark evaluation cards against a 20% holdout test set (2,020 samples).
        </div>

        <div class="screenshot-card">
            <img src="{img_ml}" alt="AI & ML Studio">
        </div>

        <div class="highlight-box">
            <strong>Model Architecture & Benchmark Comparison:</strong>
            <table>
                <thead>
                    <tr>
                        <th>Algorithm</th>
                        <th>R² Score</th>
                        <th>RMSE</th>
                        <th>MAE</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>Random Forest Regressor (100 Trees)</strong></td>
                        <td><strong>65.0%</strong></td>
                        <td>$220,491.45</td>
                        <td>$33,219.38</td>
                        <td><span style="color:#10b981; font-weight:700;">Best Model (Deployed)</span></td>
                    </tr>
                    <tr>
                        <td><strong>Multiple Linear Regression</strong></td>
                        <td>61.4%</td>
                        <td>$231,732.15</td>
                        <td>$105,242.25</td>
                        <td>Baseline Comparison</td>
                    </tr>
                </tbody>
            </table>
            <p style="margin-top:8px; font-size:8.5pt;">
                <strong>Inference Output:</strong> Forecasted Sales calculation, gross value breakdown, discount impact, and estimated margin (%) with 92.4% confidence score.
            </p>
        </div>
    </div>

    <!-- ==================== SECTION 3: CUSTOMER SEGMENTATION ==================== -->
    <div class="page-break"></div>
    <div class="section">
        <div class="section-title">3. Customer RFM Segmentation Intelligence (K-Means Clustering)</div>
        <div class="section-desc">
            Unsupervised machine learning module utilizing Recency, Frequency, and Monetary (RFM) metrics to partition 3,673 unique customers into 4 actionable business archetypes with a 2D cluster scatter plot.
        </div>

        <div class="screenshot-card">
            <img src="{img_clusters}" alt="Customer Segmentation K-Means">
        </div>

        <div class="highlight-box">
            <strong>Identified Customer Archetypes & Marketing Strategies:</strong>
            <ul>
                <li><strong>💎 VIP Platinum (7.1%):</strong> Avg spend $2.49M, frequency 5.18 orders. <em>Strategy: Concierge support & exclusive launches.</em></li>
                <li><strong>🚀 Frequent High-Value (28.2%):</strong> Avg spend $1.0M, frequency 4.03 orders. <em>Strategy: Upsell premium tiers & loyalty perks.</em></li>
                <li><strong>🛒 Regular Shoppers (38.4%):</strong> Avg spend $383k, frequency 2.07 orders. <em>Strategy: Cross-sell relevant categories & bundle offers.</em></li>
                <li><strong>⚠️ Dormant / At-Risk (26.4%):</strong> Avg recency 977 days. <em>Strategy: Targeted win-back discounts & re-engagement campaigns.</em></li>
            </ul>
        </div>
    </div>

    <!-- ==================== SECTION 4: DEEP DIVE EDA ==================== -->
    <div class="page-break"></div>
    <div class="section">
        <div class="section-title">4. Deep-Dive Exploratory Data Analysis (EDA)</div>
        <div class="section-desc">
            Statistical exploration of relationships between features via Pearson correlation heatmaps, alongside Interquartile Range (IQR) outlier detection for sales anomalies.
        </div>

        <div class="screenshot-card">
            <img src="{img_eda}" alt="Deep-Dive EDA">
        </div>

        <div class="highlight-box">
            <strong>Statistical Findings:</strong>
            <ul>
                <li><strong>Correlation Matrix:</strong> High positive correlation between Quantity & Cost (0.75), Sales & Profit (0.74), and Unit Price & Cost (0.46).</li>
                <li><strong>Outlier Statistics (IQR):</strong> Q1 ($59.1k), Median ($139.8k), Q3 ($301.7k), Upper Threshold ($665.6k). Total of <strong>1,068 outlier transactions (10.57%)</strong> identified.</li>
                <li><strong>Product Quadrant:</strong> Sales vs Profit distribution mapping high-margin champions vs loss leaders.</li>
            </ul>
        </div>
    </div>

    <!-- ==================== SECTION 5: TRANSACTIONS & CRUD ==================== -->
    <div class="page-break"></div>
    <div class="section">
        <div class="section-title">5. Transaction Records & Database CRUD Explorer</div>
        <div class="section-desc">
            Complete data management interface with real-time multi-column search, region/category dropdown filtering, pagination, and Administrator CRUD actions (Insert, Edit, Delete).
        </div>

        <div class="screenshot-card">
            <img src="{img_trans}" alt="Transactions CRUD Explorer">
        </div>

        <div class="highlight-box">
            <strong>Database & CRUD Capabilities:</strong>
            <ul>
                <li><strong>Storage:</strong> SQLite relational storage indexing 10,100 records across 28 feature columns.</li>
                <li><strong>Live Search & Filtering:</strong> Instant search by Customer Name, Order ID, and Product with compound regional filters.</li>
                <li><strong>Data Export:</strong> One-click export to CSV format for external auditing.</li>
                <li><strong>Admin Controls:</strong> Modal-driven Create, Read, Update, and Delete operations with confirmation safety guards.</li>
            </ul>
        </div>
    </div>

    <!-- ==================== SECTION 6: ADMIN CONSOLE & SECURITY ==================== -->
    <div class="page-break"></div>
    <div class="section">
        <div class="section-title">6. Admin Console & Role-Based Authentication</div>
        <div class="section-desc">
            Centralized administration hub providing system diagnostics, batch CSV dataset ingestion, on-demand model re-training orchestration, and secure role-based access control.
        </div>

        <div style="display:grid; grid-template-columns: 1.1fr 0.9fr; gap:12px;">
            <div class="screenshot-card">
                <img src="{img_admin}" alt="Admin Console Management">
            </div>
            <div class="screenshot-card">
                <img src="{img_auth}" alt="Authentication Login Modal">
            </div>
        </div>

        <div class="highlight-box">
            <strong>Security Architecture & Admin Utilities:</strong>
            <ul>
                <li><strong>Role-Based Access Control (RBAC):</strong> Separated privileges for System Administrators and Retail Analysts.</li>
                <li><strong>Instant Demo Switcher:</strong> One-click demo login buttons for rapid examination without typing credentials.</li>
                <li><strong>Batch CSV Ingestion:</strong> Allows administrators to upload new transaction datasets and automatically append records to the database.</li>
                <li><strong>Model Orchestration:</strong> On-demand trigger to re-train Random Forest regression and K-Means clustering pipelines.</li>
            </ul>
        </div>
    </div>

</body>
</html>
"""
    with open(HTML_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated HTML report at: {HTML_REPORT_PATH}")

def convert_to_pdf():
    cmd = [
        CHROME_PATH,
        "--headless=new",
        f"--print-to-pdf={PDF_OUTPUT_PATH}",
        "--no-pdf-header-footer",
        "--user-data-dir=C:\\Users\\mithu\\AppData\\Local\\Temp\\chrome_temp_pdf",
        "--no-first-run",
        "--no-default-browser-check",
        HTML_REPORT_PATH
    ]
    print("Converting HTML report to PDF via headless Chrome...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if os.path.exists(PDF_OUTPUT_PATH) and os.path.getsize(PDF_OUTPUT_PATH) > 5000:
        print(f"SUCCESS: Generated PDF report ({os.path.getsize(PDF_OUTPUT_PATH)} bytes)")
        print(f"Saved to: {PDF_OUTPUT_PATH}")
    else:
        print(f"ERROR generating PDF: {res.stderr}")

if __name__ == "__main__":
    build_html()
    convert_to_pdf()
