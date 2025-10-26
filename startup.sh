#!/bin/bash
# Azure App Service startup script for FastAPI backend

# Install dependencies if needed
if [ ! -d "venv" ]; then
    python3 -m venv antenv
    source antenv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source antenv/bin/activate
fi

# Add gunicorn to requirements if not present
pip install gunicorn

# Start the FastAPI application with Gunicorn
python -m gunicorn src.api.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
