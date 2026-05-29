#!/bin/bash
# TripAvail AI - DigitalOcean Droplet Setup Script
# Run this script on your Ubuntu droplet after initial setup

echo "🚀 Setting up TripAvail AI environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
sudo apt install -y python3 python3-pip python3-venv git ffmpeg curl wget

# Verify installations
echo "✅ Verifying installations..."
python3 --version
pip3 --version
git --version
ffmpeg -version | head -1
curl --version | head -1

# Create project directory
echo "📁 Setting up project structure..."
mkdir -p ~/tripavail_ai/{modules,data,config,logs}

# Navigate to project directory
cd ~/tripavail_ai

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Clone your repository: git clone <your-repo-url> ."
echo "2. Install dependencies: pip install -r requirements.txt"
echo "3. Copy environment template: cp env_template.txt .env"
echo "4. Edit .env file with your API keys"
echo "5. Run your application!"
echo ""
echo "To activate the virtual environment in the future:"
echo "source ~/tripavail_ai/venv/bin/activate"
