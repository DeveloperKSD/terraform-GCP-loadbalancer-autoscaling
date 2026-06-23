# Autoscaling GCP Infrastructure with Terraform

A production-style Infrastructure-as-Code project that deploys a scalable web application on Google Cloud Platform using Terraform. The infrastructure includes a Global HTTP Load Balancer, Regional Managed Instance Group (MIG), CPU-based Autoscaling, Health Checks, Auto-Healing, and a custom live monitoring dashboard for visualizing scaling events in real time.

## Features

* Infrastructure fully provisioned using Terraform
* Custom VPC and Subnet configuration
* Regional Managed Instance Group (MIG)
* CPU-based Autoscaling (1–5 instances)
* Global HTTP Load Balancer
* Health Checks and Auto-Healing
* Nginx reverse proxy deployment
* CPU-intensive Python application for autoscaling demonstrations
* PowerShell-based load testing utility
* Real-time Flask monitoring dashboard
* Live visualization of instance creation and removal events

---

## Architecture

```text
Internet Users
       │
       ▼
Global HTTP Load Balancer
       │
       ▼
Backend Service
       │
       ▼
Regional Managed Instance Group
       │
 ┌─────┴─────┐
 ▼           ▼
VM 1       VM 2
(Nginx)    (Nginx)
   │          │
   ▼          ▼
Python CPU-Intensive Service
```

---

## Project Structure

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

## Technologies Used

* Terraform
* Google Cloud Platform (GCP)
* Google Compute Engine
* Managed Instance Groups (MIG)
* Global HTTP Load Balancing
* Google Cloud CLI (gcloud)
* Linux
* Nginx
* Python
* Flask
* Chart.js
* PowerShell

---

## Infrastructure Configuration

| Setting         | Value                     |
| --------------- | ------------------------- |
| Region          | asia-south1 (Mumbai)      |
| Machine Type    | e2-small                  |
| Min Replicas    | 1                         |
| Max Replicas    | 5                         |
| CPU Target      | 60%                       |
| Cooldown Period | 60 Seconds                |
| Health Check    | HTTP Port 80              |
| Load Balancer   | Global HTTP Load Balancer |

---

## Prerequisites

* Google Cloud Project
* Billing Enabled
* Terraform Installed
* Google Cloud CLI Installed
* Compute Engine API Enabled

---

## Authentication

```bash
gcloud auth login
gcloud auth application-default login
```

Verify project:

```bash
gcloud config get-value project
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

Review deployment plan:

```bash
terraform plan
```

Deploy infrastructure:

```bash
terraform apply
```

Type:

```text
yes
```

when prompted.

---

## Access the Application

Retrieve outputs:

```bash
terraform output
```

Open the Load Balancer IP address in your browser:

```text
http://<LOAD_BALANCER_IP>
```

The application response displays the hostname of the serving instance, allowing load-balancing behavior to be observed directly.

---

## Live Monitoring Dashboard

A custom Flask dashboard was developed to visualize Managed Instance Group activity in real time.

Features:

* Current instance count
* Instance count history graph
* Active instance names
* Automatic refresh every 5 seconds
* Live scaling event visualization

Install dependencies:

```bash
pip install flask
```

Run dashboard:

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

---

## Load Testing

The repository includes a PowerShell-based stress testing utility designed to generate enough CPU load to trigger autoscaling events.

Example:

```powershell
.\loadtest.ps1
```

Custom parameters:

```powershell
.\loadtest.ps1 -Url http://<LOAD_BALANCER_IP>/ -Concurrency 50 -DurationMinutes 8
```

The script generates concurrent requests against the load balancer and displays:

* Total requests
* Requests per second
* Active worker count
* Test duration

---

## Demonstrating Autoscaling

1. Deploy infrastructure using Terraform.
2. Start the Flask monitoring dashboard.
3. Open the dashboard in a browser.
4. Run the load testing script.
5. Observe CPU utilization increase.
6. Watch the Managed Instance Group scale from 1 instance up to multiple instances.
7. Stop the load test.
8. Observe automatic scale-down after demand decreases.

---

## Learning Outcomes

This project demonstrates:

* Infrastructure as Code (IaC)
* GCP Networking
* Load Balancing
* Health Checks
* Auto-Healing
* Managed Instance Groups
* Autoscaling Strategies
* Cloud Monitoring
* Infrastructure Automation
* Terraform Resource Management

---

## Cleanup

Destroy all resources:

```bash
terraform destroy
```

This removes all provisioned cloud resources and prevents further billing.
