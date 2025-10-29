#!/bin/bash
# Script to start the backend server

cd "$(dirname "$0")/backend"

echo "Starting Python backend server..."
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
