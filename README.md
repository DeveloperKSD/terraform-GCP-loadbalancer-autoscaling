# GCP Autoscaling Infrastructure with Terraform

Provision a fully automated autoscaling web application infrastructure on Google Cloud Platform using Terraform. The project deploys a Global HTTP Load Balancer, Regional Managed Instance Group (MIG), CPU-based Autoscaler, Health Checks, Auto-Healing policies, and includes custom tools for load generation and live monitoring.

## Overview

This project demonstrates how cloud infrastructure can automatically scale in response to traffic without manual intervention.

A CPU-intensive Python application runs on each VM behind Nginx. Incoming traffic is distributed through a Global HTTP Load Balancer while a Regional Autoscaler continuously monitors CPU utilization and adjusts the number of running instances between configured minimum and maximum limits.

A custom Flask dashboard provides live visibility into scaling events by displaying instance counts, instance names, and historical scaling activity in real time.

---

## Architecture

```text
                     Internet
                         |
                         v
          +-----------------------------+
          | Global HTTP Load Balancer   |
          +-----------------------------+
                         |
                         v
               +------------------+
               | Backend Service  |
               +------------------+
                         |
                         v
      +---------------------------------------+
      | Regional Managed Instance Group (MIG) |
      +---------------------------------------+
             |          |          |
             v          v          v
          VM-1       VM-2       VM-N
          Nginx      Nginx      Nginx
             |          |          |
             v          v          v
      CPU Intensive Python Service

                     ^
                     |
             Regional Autoscaler
             (CPU Target = 60%)
```

---

## How It Works

### Load Balancer

The Global HTTP Load Balancer acts as the public entry point for the application.

Responsibilities:

* Provides a single public IP address
* Distributes traffic across healthy instances
* Performs health checks
* Removes unhealthy instances from rotation
* Automatically begins sending traffic to newly created instances

### Autoscaler

The Regional Autoscaler manages application capacity.

Responsibilities:

* Monitors average CPU utilization across all instances
* Creates additional instances during periods of high load
* Removes instances when load decreases
* Maintains configured minimum and maximum replica counts

Configuration:

| Setting          | Value      |
| ---------------- | ---------- |
| Minimum Replicas | 1          |
| Maximum Replicas | 5          |
| CPU Target       | 60%        |
| Cooldown Period  | 60 Seconds |

---

## Technologies Used

* Terraform
* Google Cloud Platform (GCP)
* Google Compute Engine
* Managed Instance Groups (MIG)
* Google Cloud Load Balancing
* Google Cloud CLI (gcloud)
* Python
* Flask
* Nginx
* PowerShell
* Chart.js

---

## Repository Structure

```text
.
├── provider.tf
├── variables.tf
├── terraform.tfvars
├── network.tf
├── firewall.tf
├── instance_template.tf
├── health_check.tf
├── mig.tf
├── autoscaler.tf
├── loadbalancer.tf
├── outputs.tf
├── startup.sh
├── loadtest.ps1
├── app.py
└── README.md
```

---

## Prerequisites

### Terraform

Verify installation:

```bash
terraform -version
```

### Google Cloud CLI

Verify installation:

```bash
gcloud version
```

### Authentication

```bash
gcloud auth login
gcloud auth application-default login
```

Set your project:

```bash
gcloud config set project YOUR_PROJECT_ID
```

Enable Compute Engine API:

```bash
gcloud services enable compute.googleapis.com
```

---

## Deployment

Initialize Terraform:

```bash
terraform init
```

Validate configuration:

```bash
terraform validate
```

Review execution plan:

```bash
terraform plan
```

Deploy infrastructure:

```bash
terraform apply
```

Confirm with:

```text
yes
```

Retrieve the Load Balancer IP:

```bash
terraform output load_balancer_ip
```

Allow several minutes for load balancer propagation before testing.

---

## Verify Deployment

Open the Load Balancer IP in a browser:

```text
http://LOAD_BALANCER_IP
```

The response displays the hostname of the backend instance serving the request.

Refreshing repeatedly should eventually return responses from different instances as traffic is distributed across the Managed Instance Group.

---

## Live Monitoring Dashboard

The project includes a local Flask dashboard that continuously polls the Managed Instance Group and visualizes scaling activity.

### Install Dependencies

```bash
pip install flask
```

### Run Dashboard

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

Dashboard Features:

* Current instance count
* Instance count history graph
* Active instance names
* Scaling event timeline
* Automatic refresh every 5 seconds

---

## Load Testing

The included PowerShell script generates sustained traffic against the Load Balancer to trigger autoscaling events.

Allow PowerShell scripts for the current session:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

Run the load test:

```powershell
.\loadtest.ps1
```

Custom example:

```powershell
.\loadtest.ps1 -Url http://LOAD_BALANCER_IP/ -Concurrency 50 -DurationMinutes 8
```

The script displays:

* Requests sent
* Requests per second
* Active worker count
* Elapsed test duration

---

## Observe Autoscaling

1. Deploy infrastructure.
2. Start the Flask dashboard.
3. Open the dashboard in a browser.
4. Run the load testing script.
5. Watch CPU utilization increase.
6. Observe new instances being created automatically.
7. Stop the load test.
8. Observe scale-down as demand decreases.

---

## Monitoring Commands

List current instances:

```bash
gcloud compute instance-groups managed list-instances web-mig \
--region asia-south1
```

View autoscaler-related logs:

```bash
gcloud logging read \
"resource.type=gce_instance_group_manager AND resource.labels.instance_group_manager_name=web-mig" \
--limit=50
```

---

## Cleanup

Destroy all infrastructure resources:

```bash
terraform destroy
```

---

## Learning Outcomes

This project demonstrates:

* Infrastructure as Code (IaC)
* Terraform Resource Management
* GCP Networking
* Managed Instance Groups
* Global Load Balancing
* Health Checks and Auto-Healing
* Autoscaling Strategies
* Cloud Monitoring
* Infrastructure Automation
* Load Testing Methodologies

<img width="1339" height="556" alt="image" src="https://github.com/user-attachments/assets/ac37a96c-b89c-412c-9916-edb674e52c76" />
