#!/bin/bash

# Setup Script for Email Template Renderer Service

set -e

echo "======================================"
echo "Email Template Renderer - Setup"
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
    else
        echo "⚠️  No .env file found. Creating default configuration..."
        cat > .env << 'EOF'
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;
EOF
        echo "✅ Default environment file created"
    fi
else
    echo "✅ Environment file exists"
fi
echo ""

# Check for Azurite
echo "4. Checking Azurite (Azure Storage Emulator)..."
if command -v azurite &> /dev/null; then
    echo "✅ Azurite is installed"
else
    echo "⚠️  Azurite is not installed"
    echo "Install with: npm install -g azurite"
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



