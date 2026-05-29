#!/bin/bash
# TripAvail AI - DigitalOcean Droplet Setup Script
# Run this on your droplet: bash droplet_setup.sh

echo "======================================"
echo "  TripAvail AI - Droplet Setup"
echo "  Server: 138.68.141.3"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print status
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_info() {
    echo -e "${YELLOW}[i]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    print_error "Please run as root (use: sudo bash droplet_setup.sh)"
    exit 1
fi

print_info "Starting deployment process..."
echo ""

# Step 1: Update system
print_info "Step 1/8: Updating system packages..."
apt update -qq && apt upgrade -y -qq
if [ $? -eq 0 ]; then
    print_status "System updated successfully"
else
    print_error "System update failed"
    exit 1
fi
echo ""

# Step 2: Install dependencies
print_info "Step 2/8: Installing Python and required tools..."
apt install -y -qq python3 python3-pip python3-venv git ffmpeg curl wget gnupg

if [ $? -eq 0 ]; then
    print_status "Dependencies installed"
else
    print_error "Failed to install dependencies"
    exit 1
fi
echo ""

# Step 3: Install Google Chrome (for Selenium if needed)
print_info "Step 3/8: Installing Google Chrome..."
if ! command -v google-chrome &> /dev/null; then
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - 2>/dev/null
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list
    apt update -qq
    apt install -y -qq google-chrome-stable
    print_status "Google Chrome installed"
else
    print_status "Google Chrome already installed"
fi
echo ""

# Step 4: Create application directory
print_info "Step 4/8: Creating application directory..."
mkdir -p /opt/tripavail_ai
mkdir -p /opt/tripavail_ai/logs
mkdir -p /opt/tripavail_ai/data
print_status "Directories created: /opt/tripavail_ai"
echo ""

# Step 5: Check if project files exist
print_info "Step 5/8: Checking project files..."
cd /opt/tripavail_ai

if [ -f "requirements.txt" ] && [ -f "smart_scheduler.py" ]; then
    print_status "Project files found"
else
    print_error "Project files not found in /opt/tripavail_ai"
    print_info "Please upload your project files using:"
    print_info "  scp -r * root@138.68.141.3:/opt/tripavail_ai/"
    exit 1
fi
echo ""

# Step 6: Setup Python virtual environment
print_info "Step 6/8: Setting up Python virtual environment..."
python3 -m venv venv
if [ $? -eq 0 ]; then
    print_status "Virtual environment created"
else
    print_error "Failed to create virtual environment"
    exit 1
fi

# Activate venv and install packages
source venv/bin/activate
print_info "Installing Python packages..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

if [ $? -eq 0 ]; then
    print_status "Python packages installed"
else
    print_error "Failed to install Python packages"
    exit 1
fi
echo ""

# Step 7: Run system check
print_info "Step 7/8: Running system check..."
if [ -f "system_check.py" ]; then
    python system_check.py
    if [ $? -eq 0 ]; then
        print_status "System check passed"
    else
        print_error "System check failed - please review errors above"
        exit 1
    fi
else
    print_info "system_check.py not found, skipping..."
fi
echo ""

# Step 8: Create systemd service
print_info "Step 8/8: Creating systemd service..."

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

if [ $? -eq 0 ]; then
    print_status "Systemd service created"
else
    print_error "Failed to create systemd service"
    exit 1
fi

# Reload systemd and enable service
systemctl daemon-reload
systemctl enable tripavail-scheduler

if [ $? -eq 0 ]; then
    print_status "Service enabled (will start on boot)"
else
    print_error "Failed to enable service"
    exit 1
fi
echo ""

# Setup log rotation
print_info "Setting up log rotation..."
cat > /etc/logrotate.d/tripavail << 'EOF'
/opt/tripavail_ai/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF
print_status "Log rotation configured"
echo ""

# Setup firewall (basic)
print_info "Configuring firewall..."
if command -v ufw &> /dev/null; then
    ufw --force enable
    ufw allow 22/tcp
    print_status "Firewall configured (SSH allowed)"
else
    apt install -y -qq ufw
    ufw --force enable
    ufw allow 22/tcp
    print_status "Firewall installed and configured"
fi
echo ""

# Final status
echo "======================================"
echo "  🎉 DEPLOYMENT COMPLETE! 🎉"
echo "======================================"
echo ""
print_info "Next Steps:"
echo ""
echo "1. Start the scheduler:"
echo "   systemctl start tripavail-scheduler"
echo ""
echo "2. Check status:"
echo "   systemctl status tripavail-scheduler"
echo ""
echo "3. View logs:"
echo "   tail -f /opt/tripavail_ai/logs/scheduler.log"
echo ""
echo "4. Check statistics:"
echo "   cd /opt/tripavail_ai && source venv/bin/activate"
echo "   python smart_scheduler.py --stats"
echo ""
echo "======================================"
echo "  Management Commands:"
echo "======================================"
echo ""
echo "  Start:   systemctl start tripavail-scheduler"
echo "  Stop:    systemctl stop tripavail-scheduler"
echo "  Restart: systemctl restart tripavail-scheduler"
echo "  Status:  systemctl status tripavail-scheduler"
echo "  Logs:    tail -f /opt/tripavail_ai/logs/scheduler.log"
echo ""
print_status "Your bot is ready to run 24/7!"
echo ""

