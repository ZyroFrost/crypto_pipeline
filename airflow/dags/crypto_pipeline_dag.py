# declarative workflow (định nghĩa pipeline)

from airflow import DAG
from airflow.operators.python import PythonOperator # operator để chạy function Python
from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator

from datetime import datetime, timezone, timedelta

import requests, os, json

API_KEY_COINGECKO_URL = os.getenv("API_KEY_COINGECKO_URL")
API_ENDPOINT_COINGECKO_URL = os.getenv("API_ENDPOINT_COINGECKO_URL")

GCS_BUCKET_NAME = "crypto-pipeline-store"

OUTPUT_DIR = "/opt/airflow/data/raw" # Sửa lại đường dẫn tuyệt đối trong container

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
    
    # LẤY THỜI GIAN CHUẨN
    now = datetime.now(timezone.utc) # Current UTC time (múi giờ chuẩn quốc tế 0:00 UTC)
    extraction_time = now.strftime("%Y-%m-%d %H:%M:%S") # Định dạng chuẩn cho BigQuery
    date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S") # Timestamp for file naming/tạo tên file unique

    # QUAN TRỌNG: Chèn thêm thời gian vào từng bản ghi để BigQuery dễ query
    # Sửa logic: Kiểm tra nếu là list thì lặp, nếu là dict thì gán trực tiếp để tránh lỗi 'str' object assignment
    if isinstance(data, list):
        for item in data:
            item["extraction_timestamp"] = extraction_time
    else:
        data["extraction_timestamp"] = extraction_time

    folder = f"{OUTPUT_DIR}/{date}" # 
    os.makedirs(folder, exist_ok=True) # Data directory, create if not exists
    file_path = f"{folder}/crypto_{timestamp}.json" # File path with timestamp

    with open(file_path, "w", encoding="utf-8") as f: # Save data to JSON file
        json.dump(data, f, ensure_ascii=False, indent=2) # ensure_ascii=False để giữ nguyên ký tự Unicode (nếu có) trong dữ liệu, tránh bị mã hóa thành \uXXXX

    print(f"[INFO] Saved {len(data)} records → {file_path}")

    return file_path # Trả về đường dẫn file để task sau (GCS) có thể sử dụng

# Define DAG
default_args = {
    "owner": "airflow", # name
    "retries": 2, # nếu API fail -> tự retry 2 lần
    "retry_delay": timedelta(minutes=1), # thời gian chờ giữa các lần retry
}

with DAG(
    dag_id="crypto_pipeline", # tên DAG (hiện trên UI)
    start_date=datetime(2024, 1, 1), # mốc bắt đầu
    # schedule_interval="*/30 * * * *", # chạy mỗi 30 phút\
    # schedule_interval="@hourly", # chạy mỗi giờ
    schedule_interval="0,30 * * * *", # chạy vào phút 0 và 30 của mỗi giờ
    catchup=False, # không chạy lại quá khứ
) as dag:

    # Task 1: Kéo dữ liệu và lưu local
    fetch_task = PythonOperator( # tạo task để chạy function fetch_crypto
        task_id="fetch_crypto", # tên task (hàm def đã tạo)
        python_callable=fetch_crypto,
    )

    # tạo task:
    # tên: fetch_crypto
    #chạy function fetch_crypto

    # Task 2: Upload file local đó lên GCS
    upload_to_gcs_task = LocalFilesystemToGCSOperator(
        task_id="upload_to_gcs",
        # Dùng XCom để tự động kéo file_path (đã được return ở Task 1) xuống đây
        src="{{ ti.xcom_pull(task_ids='fetch_crypto') }}", 
        # Đặt tên file trên GCS theo template ngày tháng của Airflow cho dễ quản lý
        dst="crypto_data/partition_date={{ ti.xcom_pull(task_ids='fetch_crypto').split('/')[-2] }}/{{ ti.xcom_pull(task_ids='fetch_crypto').split('/')[-1] }}",
        bucket=GCS_BUCKET_NAME,
        gcp_conn_id="google_cloud_default", # Tên connection tạo trên giao diện UI
    )

    # Task 3: Xóa file local sau khi đã upload lên GCS để tiết kiệm dung lượng
    from airflow.operators.bash import BashOperator
    cleanup_task = BashOperator(
        task_id="cleanup_local_files",
        bash_command="rm -rf /opt/airflow/data/raw/{{ ds }}/*", # Xóa hết file của ngày hôm nay
    )

    # THIẾT LẬP LUỒNG CHẠY (Thứ tự thực thi)
    fetch_task >> upload_to_gcs_task >> cleanup_task