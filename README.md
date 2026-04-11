# Crypto Data Pipeline (End-to-End ETL)

## Overview
This project is an automated ETL pipeline for cryptocurrency data. It extracts data from APIs, processes it locally on a Cloud Virtual Machine (VM) using Apache Airflow, and loads the structured data into a Google Cloud Storage (GCS) Data Lake. The pipeline is fully containerized using Docker and accessible via a custom DuckDNS domain.

## Architecture & Tech Stack
* **Cloud Provider:** Google Cloud Platform (Compute Engine VM).
* **Storage:** Google Cloud Storage (GCS) with Hive Partitioning.
* **Orchestration:** Apache Airflow (LocalExecutor) running on Docker.
* **Database:** PostgreSQL (Airflow Metadata).
* **Development:** VS Code (Remote-SSH).

---

## Complete Setup Guide (From Scratch)

### Phase 1: Google Cloud Platform (GCP) Provisioning

**1. Create a Compute Engine VM**
* **Purpose:** To act as the main server hosting our Docker containers, Airflow orchestration, and running the Python ETL scripts.
* Go to GCP Console -> **Compute Engine** -> **VM instances** -> **Create Instance**.
* Choose Region/Zone.
* Machine type: **Shared core, 4GB RAM** (e.g., `e2-medium`).
* Boot disk: Debian 12 Bookworm (or Ubuntu 22.04 LTS) with 10GB storage.
* Firewall: Check **Allow HTTP traffic** and **Allow HTTPS traffic**.
* Click **Create** and note the **External Public IP**.

<img width="558" height="244" alt="image" src="https://github.com/user-attachments/assets/f1335be1-7393-4adb-9bce-6095e2d44eac" />

---

**2. Create a GCS Bucket**
* **Purpose:** To act as our Cloud Data Lake. This is where the pipeline will permanently store the extracted cryptocurrency JSON files for future analytics (e.g., querying with BigQuery).
* Go to **Cloud Storage** -> **Buckets** -> **Create**.
* Name it (e.g., `crypto-pipeline-store`), choose Region, and click Create.

<img width="862" height="439" alt="image" src="https://github.com/user-attachments/assets/6fbd6c5b-6c33-4972-9327-8d7c919b407c" />

---

**3. Create a Service Account & JSON Key**
* **Purpose:** To provide a secure "ID card" for Airflow. This JSON key authenticates your local WSL2 system, allowing it to securely write data to GCP without needing your personal Google login.
* **Step 1:** Go to **IAM & Admin** -> **Service Accounts** -> Click **+ CREATE SERVICE ACCOUNT**.
* **Step 2:** Enter a name (e.g., `airflow-gcp-zyro`) and click **CREATE AND CONTINUE**.
* **Step 3:** Under "Grant this service account access to project", assign roles based on your deployment strategy:
  * 🚀 **For Quick Testing (Current Setup):** Select **Storage Object Admin** and **BigQuery Admin**. 
    *(Note: This grants full control to bypass permission errors during local development, but is strictly for testing).*
  * 🛡️ **For Production (Best Practice):** Apply the *Principle of Least Privilege* by assigning exactly what the pipeline needs to operate safely: 
    **Storage Object Creator** (to write files to GCS), **BigQuery Data Editor** (to insert data into tables), and **BigQuery Job User** (to execute the load jobs).
  * Choose your preferred roles, click **CONTINUE**, and then **DONE**.
* **Step 4:** In the Service Accounts list, click on the **Email** of the account you just created.
* **Step 5:** Go to the **Keys** tab -> Click **ADD KEY** -> Select **Create new key**.
* **Step 6:** Choose **JSON** as the key type and click **CREATE**.
* **Step 7:** A `.json` file will automatically download to your computer. **This is your only copy of the key.**
* **Step 8:** Move or copy the content of this file to `~/projects/crypto_pipeline/service-account.json` on your WSL/Ubuntu system.
  
<img width="577" height="453" alt="Screenshot 2026-04-11 010513" src="https://github.com/user-attachments/assets/d9a9d463-6010-42e0-8dc0-3c2bdacab411" />

<br>

---
---

### Phase 2: Remote Connection via VS Code

**1. Generate SSH Key (Local Machine)**
* **Purpose:** To establish a secure, passwordless connection between your local computer and the Cloud VM.
* Open your local terminal (Command Prompt/PowerShell) and run:
```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

---

**2. Add SSH Key to GCP VM**
* **Purpose:** To authorize your specific local computer to access the VM.
* View your public key locally: `cat ~/.ssh/id_rsa.pub` (Linux/Mac) or open it in Notepad (Windows). Copy the entire output.
* Go to GCP Console -> **Compute Engine** -> **Metadata** -> **SSH Keys** tab -> **Add SSH Key**. Paste your key and save.

---

**3. Connect using VS Code**
* **Purpose:** To write code and run terminal commands directly on the server using an integrated development environment (IDE).
* Open VS Code, install the **Remote - SSH** extension.
* Press `Ctrl+Shift+P` (or `Cmd+Shift+P`), type `Remote-SSH: Open SSH Configuration File`, and add:
```text
Host Crypto-VM
    HostName <YOUR_VM_EXTERNAL_IP>
    User <YOUR_GCP_USERNAME>
    IdentityFile ~/.ssh/id_rsa
```
* Press `Ctrl+Shift+P` -> `Remote-SSH: Connect to Host` -> select `Crypto-VM`. You are now inside the VM.
<br>

---

**4. Set up BigQuery (Data Warehouse)**
* **Purpose:** To create a structured database (Dataset) where your processed crypto/stock data will be stored, allowing you to run SQL queries for analysis.
* **1: Create Dataset:**
    * Go to **BigQuery** in the Google Cloud Console.
    * In the **Explorer** panel, click the three vertical dots next to your **Project ID** and select **Create dataset**.
    * **Dataset ID:** Enter a name (e.g., `crypto_market_data`).
    * **Location type:** Select **Region** and choose **us-central1 (Iowa)**. 
      *(Note: This MUST match your GCS Bucket location to stay in the Free Tier and avoid data transfer costs).*
    * Click **CREATE DATASET**.
* **2: Update Service Account Roles:**
    * Go to **IAM & Admin** -> **IAM**.
    * Find your existing Service Account (the one created in step 3) and click the **Edit** (pencil) icon.
    * Click **ADD ANOTHER ROLE** and search for: **BigQuery Admin**.
    * *(Note: This gives Airflow permission to create tables and load data into BigQuery).*
    * Click **SAVE**.
* **3: Enable BigQuery API:**
    * Go to **APIs & Services** -> **Library**.
    * Search for **BigQuery API**.
    * Ensure it is **Enabled** (usually enabled by default, but worth checking).
* **4: Table Schema (Optional for now):**
    * You don't need to create tables manually; the Airflow DAG will automatically create them using the `GoogleCloudStorageToBigQueryOperator` when it runs for the first time.

---
---

### Phase 3: VM Environment & Project Setup
Open the VS Code integrated terminal (you are now operating on the VM).

**1. Install Docker & Docker Compose**
* **Purpose:** To run Airflow and its database in isolated containers, avoiding messy local installations and dependency conflicts.
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER
```
*(Note: You might need to disconnect and reconnect your SSH session for the Docker group change to take effect).*

---

**2. Clone the Repository**
* **Purpose:** To download the pipeline code (DAGs, configuration) to the VM.
```bash
git clone [https://github.com/ZyroFrost/crypto_pipeline.git](https://github.com/ZyroFrost/crypto_pipeline.git)
cd crypto_pipeline
```

---

**3. Add the GCP Service Account Key**
* **Purpose:** To physically place the authentication key inside the project folder so Docker can mount it into the Airflow container.
* Drag and drop the `.json` file you downloaded in Phase 1 into the `crypto_pipeline` folder in VS Code.
* Rename it EXACTLY to: `service-account.json`.
<br>

---
---

### Phase 4: Airflow Deployment

**1. Set Directory Permissions**
* **Purpose:** Docker containers for Airflow run under user ID `50000`. This command grants that specific user permission to read the DAGs and write temporary data to the local disk.
```bash
sudo chown -R 50000:0 .
```

---

**2. Start the System**
* **Purpose:** To build the custom Airflow image (installing required Python packages) and spin up the Webserver, Scheduler, and Database in detached mode (background).
```bash
docker-compose up -d --build
```

---

**3. Verify**
* **Purpose:** To ensure no containers crashed during startup.
```bash
docker ps
```
Make sure `postgres`, `airflow-scheduler`, and `crypto-airflow` (webserver) are running.

---

## Usage
1. Open your browser and navigate to your DuckDNS domain:
   * **Port 80:** `http://<your-domain>.duckdns.org`
   * **Port 8080 (if configured):** `http://<your-domain>.duckdns.org:8080/`
2. Log in with the credentials set in your `.env` or `docker-compose.yml`:
   * **Username:** `admin`
   * **Password:** `<YOUR_SECURE_PASSWORD>`
3. Unpause the `crypto_pipeline` DAG. It will run tasks in this order:
   * **fetch_crypto:** Hits the API, adds execution timestamps, saves JSON locally.
   * **upload_to_gcs:** Pushes the local JSON to the GCS bucket using Hive partitioning (`partition_date=YYYY-MM-DD`).
   * **cleanup_local_files:** Deletes the temporary local JSON files to save VM disk space.

---

## Pipeline in Action (Airflow Orchestration)

<img width="1387" height="1034" alt="image" src="https://github.com/user-attachments/assets/7e5f78be-0b30-4e0a-bee3-221432efe93d" />

---

## Maintenance & Troubleshooting
* **View Webserver Logs:**
  ```bash
  docker logs -f crypto-airflow
  ```
* **View Scheduler Logs:**
  ```bash
  docker logs -f airflow-scheduler
  ```
* **Stop Services (Keep Data):**
  ```bash
  docker-compose stop
  ```
* **Wipe Everything (Including Database Volume):**
  ```bash
  docker-compose down -v
  ```
