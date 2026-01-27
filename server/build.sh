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

# DELETE OLD MODEL FILES (this is the key fix!)
echo ""
echo "🗑️  Removing old model files..."
rm -f server/app/ml_models/saved_models/*.pkl
rm -f server/app/ml_models/saved_models/*.joblib
echo "✓ Old models removed"

# Train ML models (don't fail build if this fails)
echo ""
echo "🤖 Training ML models..."
python train_on_deploy.py || echo "⚠ Model training skipped - will use fallback predictions"

echo ""
echo "======================================"
echo "✅ Build Complete!"
echo "======================================"