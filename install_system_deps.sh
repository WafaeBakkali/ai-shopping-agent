#!/bin/bash
# Install system dependencies for AI Shopping Assistant

echo "📦 Installing system dependencies..."

sudo apt update
sudo apt install -y \
    python3-venv \
    python3-dev \
    build-essential \
    libevent-2.1-7t64 \
    libglib2.0-0 \
    libnss3 \
    libatk1.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2

echo "✅ System dependencies installed!"
