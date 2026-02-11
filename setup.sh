#!/bin/bash

# SecureVote - Blockchain Voting System Setup Script

echo "==========================================="
echo "  SecureVote - Blockchain Voting System  "
echo "==========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "==========================================="
echo "  Installation Complete!                  "
echo "==========================================="
echo ""
echo "To start the application:"
echo "  python3 app.py"
echo ""
echo "Then open your browser and navigate to:"
echo "  http://localhost:5000"
echo ""
echo "Default Admin Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo "  MFA Code: 123456"
echo ""
echo "⚠️  IMPORTANT: Change these credentials in production!"
echo ""
echo "==========================================="
