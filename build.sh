#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Build React frontend
cd frontend
npm install
npm run build
cd ..
