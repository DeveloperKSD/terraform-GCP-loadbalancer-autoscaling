"""
Live Autoscaling Demo Dashboard
--------------------------------
Run this locally (on the same machine where gcloud is authenticated).
It polls your GCP Managed Instance Group every few seconds and serves
a live-updating webpage showing instance count and load test status.

Usage:
    pip install flask
    python app.py

Then open http://localhost:5000 in your browser.
"""

import subprocess
import json
import time
import threading
from datetime import datetime
from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# ---- CONFIG: change these to match your project ----
MIG_NAME = "web-mig"
REGION = "asia-south1"
PROJECT = "applied-polymer-413109"
# ------------------------------------------------------

history = []  # list of {time, count, instances}
lock = threading.Lock()


def poll_instances():
    """Background thread: polls gcloud every 5 seconds and stores history."""
    while True:
        try:
            import platform
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
            instances = json.loads(result.stdout) if result.stdout.strip() else []
            names = [i.get("name") or i.get("instance", "").split("/")[-1] for i in instances]
            status = [i.get("instanceStatus", "UNKNOWN") for i in instances]

            entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "count": len(names),
                "names": names,
                "status": status,
            }
        except Exception as e:
            entry = {
                "time": datetime.now().strftime("%H:%M:%S"),
                "count": 0,
                "names": [],
                "status": [],
                "error": f"{type(e).__name__}: {e}",
            }

        with lock:
            history.append(entry)
            # keep last 200 points so the page doesn't grow forever
            if len(history) > 200:
                history.pop(0)

        time.sleep(5)


@app.route("/api/history")
def api_history():
    with lock:
        return jsonify(history)


@app.route("/")
def index():
    return render_template_string(PAGE)


PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Autoscaling Live Demo</title>
<style>
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 32px; }
  h1 { font-size: 22px; font-weight: 600; margin-bottom: 4px; }
  .sub { color: #94a3b8; font-size: 14px; margin-bottom: 28px; }
  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }
  .card { background: #1e293b; border-radius: 12px; padding: 20px 24px; border: 1px solid #334155; }
  .label { color: #94a3b8; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; }
  .big { font-size: 42px; font-weight: 700; margin-top: 6px; }
  .green { color: #4ade80; }
  .amber { color: #fbbf24; }
  canvas { width: 100% !important; height: 260px !important; }
  .chart-card { background: #1e293b; border-radius: 12px; padding: 20px 24px; border: 1px solid #334155; margin-bottom: 20px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid #334155; }
  th { color: #94a3b8; font-weight: 500; }
  .dot { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:6px; }
  .running { background:#4ade80; }
  .other { background:#fbbf24; }
  #log { max-height: 220px; overflow-y: auto; }
</style>
</head>
<body>
  <h1>GCP Autoscaling — Live Demo</h1>
  <div class="sub">Managed Instance Group: web-mig &nbsp;|&nbsp; Region: asia-south1 &nbsp;|&nbsp; Polling every 5s</div>

  <div class="grid">
    <div class="card">
      <div class="label">Current Instance Count</div>
      <div class="big green" id="currentCount">-</div>
    </div>
    <div class="card">
      <div class="label">Last Updated</div>
      <div class="big" id="lastUpdated" style="font-size:28px;">-</div>
    </div>
  </div>

  <div class="chart-card">
    <div class="label" style="margin-bottom:10px;">Instance Count Over Time</div>
    <canvas id="chart"></canvas>
  </div>

  <div class="chart-card">
    <div class="label" style="margin-bottom:10px;">Live Instance Log</div>
    <div id="log">
      <table>
        <thead><tr><th>Time</th><th>Count</th><th>Instances</th></tr></thead>
        <tbody id="logBody"></tbody>
      </table>
    </div>
  </div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>
<script>
const ctx = document.getElementById('chart').getContext('2d');
const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [{
      label: 'Instance count',
      data: [],
      borderColor: '#4ade80',
      backgroundColor: 'rgba(74, 222, 128, 0.15)',
      stepped: true,
      fill: true,
      tension: 0
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { beginAtZero: true, ticks: { stepSize: 1, color: '#94a3b8' }, grid: { color: '#334155' } },
      x: { ticks: { color: '#94a3b8', maxRotation: 0 }, grid: { color: '#334155' } }
    },
    plugins: { legend: { labels: { color: '#e2e8f0' } } }
  }
});

async function poll() {
  try {
    const res = await fetch('/api/history');
    const data = await res.json();
    if (!data.length) return;

    chart.data.labels = data.map(d => d.time);
    chart.data.datasets[0].data = data.map(d => d.count);
    chart.update();

    const latest = data[data.length - 1];
    document.getElementById('currentCount').textContent = latest.count;
    document.getElementById('lastUpdated').textContent = latest.time;

    const logBody = document.getElementById('logBody');
    logBody.innerHTML = data.slice().reverse().slice(0, 30).map(d =>
      `<tr><td>${d.time}</td><td>${d.count}</td><td>${(d.names||[]).join(', ') || '-'}</td></tr>`
    ).join('');
  } catch (e) {
    console.error(e);
  }
}

poll();
setInterval(poll, 5000);
</script>
</body>
</html>
"""

if __name__ == "__main__":
    t = threading.Thread(target=poll_instances, daemon=True)
    t.start()
    app.run(host="0.0.0.0", port=5000, debug=False)
