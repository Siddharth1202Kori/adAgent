#!/bin/bash

export PYTHONPATH=$(pwd)

# Start backend
echo "Starting FastAPI backend..."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 &

# Wait a moment for backend to initialize
sleep 3

# Start frontend
echo "Starting Streamlit frontend..."
streamlit run app/streamlit_app.py
