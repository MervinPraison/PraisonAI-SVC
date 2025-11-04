#!/bin/bash
set -e  # Exit on error

echo "🔨 Building praisonai-svc..."
echo ""

cd /Users/praison/praisonai-svc
uv lock
uv build

echo ""
echo "✅ Build complete!"
echo ""
echo "Next steps:"
echo "  Test:    ./publish.sh --test --token YOUR_TOKEN"
echo "  Publish: ./publish.sh --token YOUR_TOKEN"
