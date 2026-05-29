#!/bin/bash
# TripAvail AI - Automated Server-Side Deployment
# This script does everything on the server - no large uploads needed!

echo "======================================"
echo "  TripAvail AI - Auto Deploy"
echo "======================================"
echo ""

# Update system
echo "[1/6] Updating system..."
apt update -qq && apt upgrade -y -qq

# Install dependencies
echo "[2/6] Installing dependencies..."
apt install -y -qq python3 python3-pip python3-venv git ffmpeg curl wget

# Setup Python environment
echo "[3/6] Setting up Python environment..."
cd /opt/tripavail_ai
python3 -m venv venv
source venv/bin/activate

# Install Python packages
echo "[4/6] Installing Python packages..."
cat > requirements.txt << 'EOF'
google-cloud-aiplatform
google-generativeai
elevenlabs
stability-sdk
requests
pillow
python-dotenv
moviepy
pydub
loguru
schedule
instagrapi
facebook-sdk
google-auth
google-auth-oauthlib
google-auth-httplib2
google-api-python-client
EOF

pip install --upgrade pip -q
pip install -r requirements.txt -q

# Create systemd service
echo "[5/6] Creating systemd service..."
cat > /etc/systemd/system/tripavail-scheduler.service << 'EOF'
[Unit]
Description=TripAvail AI Scheduler
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tripavail_ai
Environment="PATH=/opt/tripavail_ai/venv/bin"
ExecStart=/opt/tripavail_ai/venv/bin/python smart_scheduler.py --run
Restart=always
RestartSec=10
StandardOutput=append:/opt/tripavail_ai/logs/scheduler.log
StandardError=append:/opt/tripavail_ai/logs/scheduler_error.log

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable tripavail-scheduler

echo "[6/6] Creating directories..."
mkdir -p /opt/tripavail_ai/logs
mkdir -p /opt/tripavail_ai/data

echo ""
echo "======================================"
echo "  Server Setup Complete!"
echo "======================================"
echo ""
echo "Next: Upload only your code files:"
echo "  - smart_scheduler.py"
echo "  - bot.py"
echo "  - .env"
echo "  - config/, core/, scripts/ folders"
echo ""
echo "Then run: systemctl start tripavail-scheduler"
echo ""


