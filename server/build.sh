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

# Create necessary directories
echo ""
echo "📁 Creating model directories..."
mkdir -p server/app/ml_models/saved_models
mkdir -p server/app/ml_training

# Train ML models (don't fail build if this fails)
echo ""
echo "🤖 Training ML models..."
python train_on_deploy.py || echo "⚠ Model training skipped - will use fallback predictions"

echo ""
echo "======================================"
echo "✅ Build Complete!"
echo "======================================"