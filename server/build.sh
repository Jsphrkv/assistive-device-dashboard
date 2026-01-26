#!/usr/bin/env bash
# build.sh - Run during deployment

set -o errexit  # Exit on error

echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating model directories..."
mkdir -p app/ml_models/saved_models

echo "Training ML models..."
python -c "from app.ml_training.train_on_deploy import train_models_for_production; train_models_for_production()"

echo "Build complete!"