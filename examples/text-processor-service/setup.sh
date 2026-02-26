#!/bin/bash

# Setup Script for Text Processor Service
# This script helps you get started quickly

set -e

echo "======================================"
echo "Text Processor Service - Setup"
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

# Check if pip is available
echo "2. Checking pip..."
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed"
    exit 1
fi
echo "✅ pip is available"
echo ""

# Install dependencies
echo "3. Installing dependencies..."
pip3 install -r requirements.txt 2>/dev/null || pip install -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if .env exists
echo "4. Checking environment configuration..."
if [ ! -f .env ]; then
    if [ -f .env.local ]; then
        echo "📝 Copying .env.local to .env..."
        cp .env.local .env
        echo "✅ Environment file created"
    else
        echo "⚠️  No .env file found. Creating default configuration..."
        cat > .env << 'EOF'
# Azure Storage Connection String (for Azurite local testing)
PRAISONAI_AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;TableEndpoint=http://127.0.0.1:10002/devstoreaccount1;
EOF
        echo "✅ Default environment file created"
    fi
else
    echo "✅ Environment file exists"
fi
echo ""

# Check for Azurite
echo "5. Checking Azurite (Azure Storage Emulator)..."
if command -v azurite &> /dev/null; then
    echo "✅ Azurite is installed"
else
    echo "⚠️  Azurite is not installed"
    echo ""
    echo "For local testing, you need Azurite (Azure Storage Emulator)"
    echo "Install with: npm install -g azurite"
    echo ""
    echo "Or use real Azure Storage by updating .env with your connection string"
fi
echo ""

# Check if jq is installed (for testing scripts)
echo "6. Checking jq (for test scripts)..."
if command -v jq &> /dev/null; then
    echo "✅ jq is installed"
else
    echo "⚠️  jq is not installed (optional, needed for test scripts)"
    echo "Install with:"
    echo "  - macOS: brew install jq"
    echo "  - Linux: apt-get install jq or yum install jq"
    echo "  - Windows: choco install jq"
fi
echo ""

# Make scripts executable
echo "7. Making scripts executable..."
chmod +x test_workflow.sh quick-test.sh setup.sh 2>/dev/null || true
echo "✅ Scripts are executable"
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
echo "3. In another terminal, test the service:"
echo "   bash quick-test.sh"
echo ""
echo "4. Or run the full workflow test:"
echo "   bash test_workflow.sh"
echo ""
echo "5. Or run unit tests:"
echo "   pytest test_app.py -v"
echo ""
echo "For more information, see README.md"
echo ""

