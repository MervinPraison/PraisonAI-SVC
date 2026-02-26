#!/bin/bash

# Setup Script for QR Code Generator Service

set -e

echo "======================================"
echo "QR Code Generator - Setup"
echo "======================================"
echo ""

# Check Python version
echo "1. Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python $PYTHON_VERSION found"
echo ""

# Install dependencies
echo "2. Installing dependencies..."
pip3 install -r requirements.txt 2>/dev/null || pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if .env exists
echo "3. Checking environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.local ]; then
        echo "📝 Copying .env.local to .env..."
        cp .env.local .env
        echo "✅ Environment file created"
    fi
else
    echo "✅ Environment file exists"
fi
echo ""

echo "======================================"
echo "Setup Complete! 🎉"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Start Azurite (in a separate terminal):"
echo "   azurite --silent"
echo ""
echo "2. Run the service:"
echo "   python3 app.py"
echo ""

