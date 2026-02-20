#!/usr/bin/env bash
# Build script for Render deployment

set -o errexit  # Exit on error

echo "======================================"
echo "Starting Build Process"
echo "======================================"

# Install Python dependencies
echo ""
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "======================================"
echo "✅ Build Complete!"
echo "======================================"