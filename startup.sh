#!/bin/bash
apt-get update
apt-get install -y nginx python3 python3-pip

HOSTNAME=$(hostname)

# Simple Python CGI-style script that burns CPU on every request,
# so load testing actually drives CPU utilization up (static HTML doesn't).
mkdir -p /var/www/cpu-app
cat > /var/www/cpu-app/server.py << 'PYEOF'
import http.server
import socketserver
import socket

PORT = 8080

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Burn CPU: do a chunk of busywork on every request
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
        pass  # quiet logs

with socketserver.ThreadingTCPServer(("0.0.0.0", PORT), Handler) as httpd:
    httpd.serve_forever()
PYEOF

# Run it as a systemd service so it survives and restarts on crash
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

# nginx reverse-proxies port 80 -> the python app on 8080
cat > /etc/nginx/sites-available/default << 'EOF3'
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
EOF3

systemctl restart nginx
