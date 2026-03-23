# Dockerfile: build this first before running docker-compose up

# Use the latest Airflow image as the base image (use a specific version for stability)
FROM apache/airflow:2.9.0

# Switch to root user to install system packages
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    apt-get clean
    
    # --no-install-recommends: avoid installing unnecessary extra packages
    # apt-get clean: reduce image size by cleaning cache

# Switch back to airflow user (important for security & Airflow compatibility)
USER airflow

# Install Python dependencies (if any)
RUN pip install requests