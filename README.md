# Crypto Data Pipeline

## Overview
This project is an automated ETL pipeline for cryptocurrency data. Deployed on a Cloud VM and fully containerized with Docker, it uses Apache Airflow to schedule tasks, extract data from APIs, and load it directly into Google Cloud Storage (GCS).

## Tech Stack
* **Google Cloud Storage (GCS)**: Cloud data lake.
* **Apache Airflow**: Workflow orchestration (LocalExecutor).
* **PostgreSQL**: Metadata database for Airflow.
* **Docker & Docker Compose**: Containerization.
* **Python 3**: ETL scripts and GCS integration.

## Project Structure
```text
crypto_pipeline/
├── airflow/
│   └── dags/              # Python DAG files for Airflow
├── data/                  # Local storage for temporary data processing
├── .env                   # Environment variables
├── docker-compose.yml     # Docker services (Webserver, Scheduler, Postgres, Init)
├── Dockerfile             # Custom Airflow image build
├── requirements.txt       # Python dependencies
└── README.md              # Project documentation
```

## Prerequisites
* **Docker & Docker Compose** installed on VM.
* **GCP Service Account Key (JSON)**: Required for GCS access. Place your key in the root directory as `service-account.json`.

## Installation & Setup

**1. Clone the repository**
```bash
git clone https://github.com/ZyroFrost/crypto_pipeline.git
cd crypto_pipeline
```

**2. Set directory permissions**
```bash
sudo chown -R 50000:0 .
```

**3. Start the system**
```bash
docker-compose up -d --build
```

**4. Verify running containers**
```bash
docker ps
```

## Usage & Configuration

### 1. Access Airflow UI
* **URL:** `http://<VM_Public_IP>` (Mapped to port 80)
* **Default Credentials:**
  * **Username:** `admin`
  * **Password:** `yourpassword`

### 2. Google Cloud Connection
The connection is automatically configured via environment variables in `docker-compose.yml` using the `AIRFLOW_CONN_GOOGLE_CLOUD_DEFAULT` variable. It points to `/opt/airflow/service-account.json` inside the container.

## Maintenance Commands

* **View container logs:**
```bash
docker logs -f crypto-airflow
```
* **Restart services:**
```bash
docker-compose restart
```
* **Stop services:**
```bash
docker-compose stop
```
* **Teardown completely (Remove volumes):**
```bash
docker-compose down -v
```
