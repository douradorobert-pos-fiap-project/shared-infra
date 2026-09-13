#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Installing dependencies..."
pip install -r requirements.txt -t . --quiet

echo "Creating deployment package..."
zip -r ../authorizer.zip . -x "*.pyc" "__pycache__/*" "requirements.txt" "build.sh"

echo "Build complete: ../authorizer.zip"
