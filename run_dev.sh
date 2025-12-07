#!/bin/bash
echo "Starting RAG Application..."

# Start Infrastructure
echo "Starting Docker Containers (DB, Redis, Chroma)..."
docker-compose up -d db redis chromadb

# Start Backend
echo "Starting Backend..."
cd backend
# Assume env is active or poetry/pip used directly
# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null
then
    echo "Uvicorn could not be found. Please activate your python environment."
    exit
fi
# Run in background
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..

# Start Worker
echo "Starting Celery Worker..."
cd backend
celery -A app.worker worker --loglevel=info &
WORKER_PID=$!
cd ..

# Start Frontend
echo "Starting Frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "Application running!"
echo "Backend: http://localhost:8000/docs"
echo "Frontend: http://localhost:3000"

# Cleanup trap
trap "kill $BACKEND_PID $WORKER_PID $FRONTEND_PID; docker-compose down" INT

wait
