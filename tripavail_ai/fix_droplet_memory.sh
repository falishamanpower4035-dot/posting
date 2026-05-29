#!/bin/bash
#
# Fix Memory Issues on TripAvail Droplet
# Adds 2GB swap space and optimizes video generation
#

set -e

echo "========================================="
echo "  TripAvail Droplet Memory Fix"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "ERROR: Please run as root (use sudo)"
    exit 1
fi

# 1. Add 2GB swap space (prevents OOM kills)
echo "📝 Step 1: Adding 2GB swap space..."
if [ ! -f /swapfile ]; then
    # Create swap file
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Make permanent
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    
    # Optimize swap usage
    sysctl vm.swappiness=10
    echo 'vm.swappiness=10' >> /etc/sysctl.conf
    
    echo "✅ Swap space added: 2GB"
else
    echo "✅ Swap file already exists"
fi

# Verify swap
echo ""
echo "Current memory status:"
free -h

echo ""
echo "========================================="
echo "  ✅ Memory fix complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. The swap space will prevent OOM kills"
echo "2. Video generation should complete now"
echo "3. Monitor with: free -h"
echo ""

