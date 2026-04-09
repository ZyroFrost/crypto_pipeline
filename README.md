# Crypto Data Pipeline (End-to-End ETL)

> 🚀 **Live Web UI / Demo:** [http://crypto-data-pipeline.duckdns.org/](http://crypto-data-pipeline.duckdns.org/)
> 
> 🔑 **Guest Account (Read-only):** `account: guest` / `password: guest`

## Overview
This project is an automated ETL pipeline for cryptocurrency data. It extracts data from APIs, processes it locally on a Cloud Virtual Machine (VM) using Apache Airflow, and loads the structured data into a Google Cloud Storage (GCS) Data Lake. The pipeline is fully containerized using Docker and accessible via a custom DuckDNS domain.

## Architecture & Tech Stack
* **Cloud Provider:** Google Cloud Platform (Compute Engine VM).
* **Storage:** Google Cloud Storage (GCS) with Hive Partitioning.
* **Orchestration:** Apache Airflow (LocalExecutor) running on Docker.
* **Database:** PostgreSQL (Airflow Metadata).
* **Networking:** DuckDNS (Free Dynamic DNS).
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
* **Purpose:** To provide a secure "ID card" for Airflow. This JSON key authenticates the `upload_to_gcs` task, allowing the VM to securely write data into the GCS Bucket without needing your personal Google login.
* Go to **IAM & Admin** -> **Service Accounts** -> **Create Service Account**.
* Grant it the **Storage Object Admin** or **Storage Object Creator** role.
* Once created, click on it -> **Keys** tab -> **Add Key** -> **Create new key** -> **JSON**.
* Save this `.json` file to your local computer.
  
<img width="563" height="602" alt="image" src="https://github.com/user-attachments/assets/d4cdca79-0d3c-4923-b1d1-1ba937e40e70" />
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
*(Press Enter to save to default location, leave passphrase empty if desired).*

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
---

### Phase 3: Domain Setup (DuckDNS)

**🚦 Choose your setup path:**
* **👉 For Local Development:** Skip this entire phase. You can access Airflow directly via `http://localhost:8080`.
* **👉 For Cloud Deployment (VM):** Follow the steps below to map your VM's public IP to a free Domain, making it easier to access and preventing issues when the VM restarts.

**1. Register Domain**
* **Purpose:** To provide a static, easy-to-remember web address (like `my-pipeline.duckdns.org`) instead of memorizing a raw IP address.
* Go to [DuckDNS.org](https://www.duckdns.org/) and log in.
* In the "domains" section, type a name and click **add domain**.
* Copy your **token** (a long string of characters at the top of the page).

---

**2. Automate IP Update via Cron Job**
* **Purpose:** Cloud VMs change their IP addresses if restarted. By adding a direct command to the VM's cron table, it will run in the background every 5 minutes to automatically update DuckDNS with your latest IP.
* Open your VM terminal in VS Code and open the crontab editor:
```bash
crontab -e
```
*(If prompted to choose an editor, press `1` for nano).*
* Scroll to the very bottom of the file and paste this exact line (Replace `<YOUR_DOMAIN>` and `<YOUR_TOKEN>` with your details):
```text
*/5 * * * * curl -k "[https://www.duckdns.org/update?domains=](https://www.duckdns.org/update?domains=)<YOUR_DOMAIN>&token=<YOUR_TOKEN>&ip="
```
* Save the file by pressing `Ctrl + O` -> `Enter` *(you should see a "lines written" message)*. Then exit by pressing `Ctrl + X`.
* **Verify your setup:**
  * Check if the cron job saved correctly: `crontab -l`
  * Check your current VM IP: `curl ifconfig.me`
<br>

---
---

### Phase 4: VM Environment & Project Setup
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

### Phase 5: Airflow Deployment

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
