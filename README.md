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

Detailed Commands & Scripts Reference
Phase 0 — Local Environment Setup
Installing Terraform (Windows 11)

Downloaded from https://developer.hashicorp.com/terraform/install
Extracted the zip, placed terraform.exe in C:\terraform
Added C:\terraform to system PATH via Environment Variables
Verified in a new terminal:

terraform -version
Installing Google Cloud CLI

Downloaded the Windows installer from https://cloud.google.com/sdk/docs/install
Ran the installer, kept "Run gcloud init" checked on completion
Authenticated:

gcloud auth login
gcloud config set project applied-polymer-413109
gcloud auth application-default login

Enabled the Compute Engine API:

gcloud services enable compute.googleapis.com
Installing PowerShell 7 (needed for ForEach-Object -Parallel)
The default Windows PowerShell is version 5, which doesn't support parallel execution. PowerShell 7 was installed via winget (simpler than hunting for the correct .msi asset on GitHub):
winget install --id Microsoft.PowerShell --source winget
After installation, opened a new terminal and launched PowerShell 7 specifically with:
pwsh
Verified the version:
powershell$PSVersionTable.PSVersion
Confirmed it returned Major version 7 (specifically 7.6.3).

Phase 1 — Terraform Project Files
Project folder:
C:\Users\Shivaami_User\Desktop\gcp-terraform-mig-lb
variables.tf
hclvariable "project_id" {
  description = "Your GCP project ID"
  type        = string
}

variable "region" {
  default = "asia-south1"
}

variable "zone" {
  default = "asia-south1-a"
}
terraform.tfvars
hclproject_id = "applied-polymer-413109"
provider.tf
hclterraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
network.tf
hclresource "google_compute_network" "vpc" {
  name                    = "mig-lb-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "mig-lb-subnet"
  ip_cidr_range = "10.0.1.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}
firewall.tf
hclresource "google_compute_firewall" "allow_http" {
  name    = "web-mig-allow-http"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["http-server"]
}

resource "google_compute_firewall" "allow_health_check" {
  name    = "allow-health-check"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }

  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
  target_tags   = ["http-server"]
}
Note: allow_http's name was changed from allow-http to web-mig-allow-http after a naming collision with a pre-existing rule in the shared GCP project (see Problem 1 in the project report).
startup.sh — final version (CPU-intensive demo endpoint)
bash#!/bin/bash
apt-get update
apt-get install -y nginx python3 python3-pip

HOSTNAME=$(hostname)

mkdir -p /var/www/cpu-app
cat > /var/www/cpu-app/server.py << 'PYEOF'
import http.server
import socketserver
import socket

PORT = 8080

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        total = 0
        for i in range(2_000_000):
            total += i * i
        hostname = socket.gethostname()
        body = f"<h1>Hello from {hostname}</h1><p>Computed: {total}</p>".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass

with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
PYEOF

cat > /etc/systemd/system/cpu-app.service << 'EOF2'
[Unit]
Description=CPU load demo app
After=network.target

[Service]
ExecStart=/usr/bin/python3 /var/www/cpu-app/server.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF2

systemctl daemon-reload
systemctl enable cpu-app
systemctl start cpu-app

cat > /etc/nginx/sites-available/default << 'EOF3'
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
EOF3

systemctl restart nginx
Note: the original version of this file served a static HTML page directly via nginx (no Python app, no reverse proxy). It was rewritten to the version above after discovering that static content does not generate meaningful CPU load (see Problem 3 in the project report).
instance_template.tf
hclresource "google_compute_instance_template" "web_template" {
  name_prefix  = "web-template-"
  machine_type = "e2-small"
  region       = var.region
  tags         = ["http-server"]

  disk {
    source_image = "debian-cloud/debian-12"
    auto_delete  = true
    boot         = true
  }

  network_interface {
    network    = google_compute_network.vpc.id
    subnetwork = google_compute_subnetwork.subnet.id
    access_config {}
  }

  metadata_startup_script = file("${path.module}/startup.sh")

  lifecycle {
    create_before_destroy = true
  }
}
health_check.tf
hclresource "google_compute_health_check" "http_hc" {
  name = "http-health-check"

  http_health_check {
    port = 80
  }

  check_interval_sec  = 5
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 3
}
mig.tf — final version
hclresource "google_compute_region_instance_group_manager" "mig" {
  name   = "web-mig"
  region = var.region

  base_instance_name = "web"

  version {
    instance_template = google_compute_instance_template.web_template.id
  }

  named_port {
    name = "http"
    port = 80
  }

  auto_healing_policies {
    health_check      = google_compute_health_check.http_hc.id
    initial_delay_sec = 60
  }
}
Note: this originally included target_size = 2. That line was removed after it conflicted with the attached autoscaler (see Problem 2 in the project report).
autoscaler.tf
hclresource "google_compute_region_autoscaler" "autoscaler" {
  name   = "web-autoscaler"
  region = var.region
  target = google_compute_region_instance_group_manager.mig.id

  autoscaling_policy {
    max_replicas    = 5
    min_replicas    = 1
    cooldown_period = 60

    cpu_utilization {
      target = 0.6
    }
  }
}
loadbalancer.tf
hclresource "google_compute_backend_service" "backend" {
  name          = "web-backend"
  protocol      = "HTTP"
  port_name     = "http"
  health_checks = [google_compute_health_check.http_hc.id]

  backend {
    group = google_compute_region_instance_group_manager.mig.instance_group
  }
}

resource "google_compute_url_map" "url_map" {
  name            = "web-url-map"
  default_service = google_compute_backend_service.backend.id
}

resource "google_compute_target_http_proxy" "proxy" {
  name    = "web-proxy"
  url_map = google_compute_url_map.url_map.id
}

resource "google_compute_global_forwarding_rule" "fr" {
  name       = "web-forwarding-rule"
  target     = google_compute_target_http_proxy.proxy.id
  port_range = "80"
}
outputs.tf
hcloutput "load_balancer_ip" {
  value = google_compute_global_forwarding_rule.fr.ip_address
}

Phase 2 — Deployment Commands
terraform init
terraform validate
terraform plan
terraform apply
(typed yes when prompted at apply)
Retrieving the load balancer's public IP:
terraform output load_balancer_ip
Forcing a new instance template after the startup script was rewritten:
terraform apply -replace="google_compute_instance_template.web_template"
Forcing an already-running VM to pick up the new template (since startup scripts only run at boot, not retroactively):
gcloud compute instance-groups managed delete-instances web-mig --instances=web-nr45 --region=asia-south1 --project=applied-polymer-413109
Tearing the whole project down when finished:
terraform destroy

Phase 3 — Verification Commands
Checking instance group membership and health:
gcloud compute instance-groups managed list-instances web-mig --region asia-south1 --project applied-polymer-413109 --format json
Testing the load balancer endpoint directly:
powershellInvoke-WebRequest -Uri "http://34.8.223.80/" -UseBasicParsing
Timing a single request (used to confirm the CPU-intensive app was actually live, since it should respond noticeably slower than static content):
powershellMeasure-Command { Invoke-WebRequest -Uri "http://34.8.223.80/" -UseBasicParsing }
Cloud Logging query for autoscaler resize events (run via Console → Logs Explorer, or via CLI):
gcloud logging read "resource.type=gce_instance_group_manager AND resource.labels.instance_group_manager_name=web-mig" --limit=50 --format=json

Phase 4 — Load Testing Script
loadtest.ps1 — final working version
powershell# loadtest.ps1
# Stress test for GCP Load Balancer -> MIG autoscaling demo
# Prints live request counter to the terminal using a thread-safe in-memory
# counter (no shared file I/O, which was bottlenecking an earlier version).

param(
    [string]$Url = "http://34.8.223.80/",
    [int]$Concurrency = 50,
    [int]$DurationMinutes = 8
)

# Raise the .NET ThreadPool minimum so all $Concurrency threads can actually start.
# Without this, PowerShell's default thread pool (sized to CPU core count) silently
# queues excess parallel jobs forever instead of running them or erroring.
[System.Threading.ThreadPool]::SetMinThreads($Concurrency + 10, $Concurrency + 10) | Out-Null

Write-Host "=================================================="
Write-Host " GCP Load Balancer Stress Test"
Write-Host " Target:       $Url"
Write-Host " Concurrency:  $Concurrency"
Write-Host " Duration:     $DurationMinutes minute(s)"
Write-Host "=================================================="
Write-Host ""

$startTime = Get-Date
$endTime = $startTime.AddMinutes($DurationMinutes)

$sync = [hashtable]::Synchronized(@{ Count = 0 })

$jobs = 1..$Concurrency | ForEach-Object {
    Start-ThreadJob -ThrottleLimit ($Concurrency + 10) -ScriptBlock {
        param($u, $endTime, $sync)
        while ((Get-Date) -lt $endTime) {
            try {
                Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 5 | Out-Null
                $sync.Count = $sync.Count + 1
            } catch {}
        }
    } -ArgumentList $Url, $endTime, $sync
}

Write-Host "Load test running... press Ctrl+C to stop early."
Write-Host ""

while ((Get-Date) -lt $endTime) {
    Start-Sleep -Seconds 5
    $total = $sync.Count
    $elapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds)
    $rps = if ($elapsed -gt 0) { [math]::Round($total / $elapsed, 1) } else { 0 }
    $running = (Get-Job | Where-Object { $_.State -eq 'Running' }).Count
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Requests: $total  |  Elapsed: ${elapsed}s  |  ~$rps req/sec  |  Active workers: $running/$Concurrency"
}

Write-Host ""
Write-Host "Duration reached. Stopping workers..."
$jobs | Stop-Job -ErrorAction SilentlyContinue
$jobs | Remove-Job -ErrorAction SilentlyContinue
Write-Host "Total requests sent: $($sync.Count)"
Write-Host "Done."
Running it
powershellSet-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\loadtest.ps1
The Set-ExecutionPolicy line was required because Windows blocks unsigned .ps1 scripts by default. -Scope Process limits the policy change to that single terminal session only, rather than weakening security machine-wide.
Cleaning up stuck jobs (used while debugging the thread pool issue)
powershellGet-Job
Get-Job | Stop-Job
Get-Job | Remove-Job
Get-Job | Receive-Job -Keep -ErrorAction SilentlyContinue | Select-Object -First 10

Phase 5 — Local Monitoring Dashboard
Setup
pip install flask
python app.py
Dashboard accessed at:
http://localhost:5000
Raw polling data inspected directly at:
http://localhost:5000/api/history
app.py — key excerpt (Windows-specific subprocess fix)
pythonimport platform
gcloud_cmd = "gcloud.cmd" if platform.system() == "Windows" else "gcloud"
result = subprocess.run(
    [
        gcloud_cmd, "compute", "instance-groups", "managed",
        "list-instances", MIG_NAME,
        "--region", REGION,
        "--project", PROJECT,
        "--format", "json",
    ],
    capture_output=True, text=True, timeout=20, shell=False
)
This explicit gcloud.cmd reference was required because Python's subprocess.run() calls the Windows process launcher directly, which does not automatically resolve .cmd batch files the way PowerShell's own command resolution does — calling plain "gcloud" failed with WinError 2: The system cannot find the file specified.

That's every command and script in the order they were actually run, including the ones that initially failed and what replaced them. Want this merged into the Word report as an appendix section, or kept as a separate document?You said: what is the role of loadbalancer and autoscaling here?what is the role of loadbalancer and autoscaling here?
generate a readme.md file for this project which has architecture and steps to run it2:13 PMClaude responded: Quick answer on rolesQuick answer on roles
Load balancer's role: it's the single public entry point. It receives all incoming traffic on one IP address and decides which healthy backend VM should handle each request, spreading load across the group rather than letting all traffic hit one machine. It also continuously runs health checks — any VM that fails them gets pulled out of rotation automatically, so users never get routed to a broken instance.
Autoscaler's role: it's the capacity-management layer sitting on top of the instance group. It watches average CPU usage across all VMs in the group and adjusts how many VMs exist — adding more when load is high, removing them when load drops — between your configured min (1) and max (5). The load balancer doesn't create or destroy VMs; it only routes traffic to whatever VMs currently exist. The autoscaler is what changes how many targets the load balancer even has to choose from.
Put together: autoscaler decides capacity, load balancer decides distribution. They're deliberately separate, decoupled resources in Terraform — the load balancer would work fine with a fixed-size group, and the autoscaler would still resize a group even with no load balancer in front of it at all (e.g., for a backend worker pool). Here they're combined so that as the autoscaler adds VMs, the load balancer automatically starts sending them traffic the moment they pass health checks, with zero manual wiring required.
Now let's build the README.



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
