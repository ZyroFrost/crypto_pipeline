# declarative workflow (định nghĩa pipeline)

from airflow import DAG
from airflow.operators.python import PythonOperator # operator để chạy function Python

from datetime import datetime, timezone, timedelta

import requests, os, json

API_KEY_COINGECKO_URL = os.getenv("API_KEY_COINGECKO_URL")
API_ENDPOINT_COINGECKO_URL = os.getenv("API_ENDPOINT_COINGECKO_URL")

OUTPUT_DIR = "data/raw" # Output directory for raw data, container path

HEADER = {
    "x-cg-demo-api-key": API_KEY_COINGECKO_URL,
}

PARAMS = {
    "vs_currency": "usd",
    "order": "market_cap_desc",
    "per_page": 50,
}

# Function to fetch crypto data
def fetch_crypto():
    response = requests.get(API_ENDPOINT_COINGECKO_URL, params=PARAMS, headers=HEADER, timeout=10)

    # Check for successful response
    if response.status_code != 200:
        raise Exception(f"API error: {response.status_code} - {response.text}")

    data = response.json() # convert JSON to Python dict/list

    now = datetime.now(timezone.utc) # Current UTC time (múi giờ chuẩn quốc tế 0:00 UTC)
    date = now.strftime("%Y-%m-%d")  
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S") # Timestamp for file naming/tạo tên file unique

    folder = f"{OUTPUT_DIR}/{date}" # 
    os.makedirs(folder, exist_ok=True) # Data directory, create if not exists
    file_path = f"{folder}/crypto_{timestamp}.json" # File path with timestamp

    with open(file_path, "w", encoding="utf-8") as f: # Save data to JSON file
        json.dump(data, f, ensure_ascii=False, indent=2) # ensure_ascii=False để giữ nguyên ký tự Unicode (nếu có) trong dữ liệu, tránh bị mã hóa thành \uXXXX

    print(f"[INFO] Saved {len(data)} records → {file_path}")

# Define DAG
default_args = {
    "owner": "airflow", # name
    "retries": 2, # nếu API fail -> tự retry 2 lần
    "retry_delay": timedelta(minutes=1), # thời gian chờ giữa các lần retry
}

with DAG(
    dag_id="crypto_pipeline", # tên DAG (hiện trên UI)
    start_date=datetime(2024, 1, 1), # mốc bắt đầu
    schedule_interval="*/10 * * * *", # chạy mỗi 10 phút
    catchup=False, # không chạy lại quá khứ
) as dag:

    fetch_task = PythonOperator( # tạo task để chạy function fetch_crypto
        task_id="fetch_crypto", # tên task (hàm def đã tạo)
        python_callable=fetch_crypto,
    )

    # tạo task:
    # tên: fetch_crypto
    #chạy function fetch_crypto

    fetch_task # set task