#!/bin/bash
set -e  # Exit on error

echo "🔨 Building praisonai-svc..."
echo ""

cd /Users/praison/praisonai-svc

# Extract version from pyproject.toml
VERSION=$(grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
echo "📦 Version: $VERSION"
echo ""

# Build
uv lock
uv build

# Git tagging
echo ""
echo "🏷️  Git tagging..."

# Check if tag already exists
if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    echo "⚠️  Tag v$VERSION already exists locally"
    read -p "   Delete and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d "v$VERSION"
        echo "   ✓ Deleted local tag"
    else
        echo "   Skipping tag creation"
    fi
fi

# Create new tag if it doesn't exist
if ! git rev-parse "v$VERSION" >/dev/null 2>&1; then
    git tag -a "v$VERSION" -m "Release v$VERSION"
    echo "✅ Created local tag: v$VERSION"
    echo ""
    echo "💡 When ready to push:"
    echo "   git push origin v$VERSION"
    echo "   # Or to force update remote tag:"
    echo "   git push origin v$VERSION --force"
fi

echo ""
echo "✅ Build complete!"
echo ""
echo "Next steps:"
echo "  Test:    ./publish.sh --test --token YOUR_TOKEN"
echo "  Publish: ./publish.sh --token YOUR_TOKEN"
