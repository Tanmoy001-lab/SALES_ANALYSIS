import subprocess
import os
import time

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = r"C:\Users\mithu\OneDrive\Desktop\New folder\screenshots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

targets = [
    {
        "filename": "01_Executive_Overview_Dashboard.png",
        "url": "http://127.0.0.1:5000/?tab=overview",
        "description": "Executive Overview Dashboard with Real-Time KPIs and Financial Trends"
    },
    {
        "filename": "02_AI_and_ML_Studio.png",
        "url": "http://127.0.0.1:5000/?tab=ml-studio",
        "description": "Random Forest Sales Predictor & Model Benchmarking Metrics"
    },
    {
        "filename": "03_Customer_Segmentation_RFM_KMeans.png",
        "url": "http://127.0.0.1:5000/?tab=ml-studio&scroll=820",
        "description": "RFM K-Means Customer Clustering Archetypes and Scatter Plot"
    },
    {
        "filename": "04_Deep_Dive_EDA_Correlation_Matrix.png",
        "url": "http://127.0.0.1:5000/?tab=eda",
        "description": "Multivariate Feature Correlation Matrix Heatmap"
    },
    {
        "filename": "05_EDA_Outliers_and_Product_Matrix.png",
        "url": "http://127.0.0.1:5000/?tab=eda&scroll=650",
        "description": "Sales Outliers Analysis and Product Performance Quadrant"
    },
    {
        "filename": "06_Transactions_and_Data_CRUD.png",
        "url": "http://127.0.0.1:5000/?tab=transactions",
        "description": "Sales Transactions Database Explorer with Search and Admin CRUD"
    },
    {
        "filename": "07_Admin_Console_Management.png",
        "url": "http://127.0.0.1:5000/?tab=admin",
        "description": "Admin Control Center with Database Stats and Batch CSV Ingestion"
    },
    {
        "filename": "08_Authentication_Login_Modal.png",
        "url": "http://127.0.0.1:5000/?modal=auth",
        "description": "Role-Based Authentication Center with 1-Click Demo Login"
    }
]

def capture_all():
    for item in targets:
        out_file = os.path.join(OUTPUT_DIR, item["filename"])
        cmd = [
            CHROME_PATH,
            "--headless=new",
            f"--screenshot={out_file}",
            "--window-size=1920,1080",
            "--virtual-time-budget=6000",
            "--disable-gpu",
            item["url"]
        ]
        print(f"Capturing: {item['filename']} ...")
        res = subprocess.run(cmd, capture_output=True, text=True)
        if os.path.exists(out_file) and os.path.getsize(out_file) > 1000:
            print(f"  -> SUCCESS ({os.path.getsize(out_file)} bytes)")
        else:
            print(f"  -> FAILED: {res.stderr}")
        time.sleep(1)

if __name__ == "__main__":
    capture_all()
