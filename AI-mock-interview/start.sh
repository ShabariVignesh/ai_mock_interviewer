#!/bin/bash

echo "Starting backend API server..."
cd AI-mock-interview/rag
pkill -f "python -m uvicorn api_server:app"
python -m uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

echo "Starting frontend development server..."
cd ../../3cf9f4ea-644d-446c-9e93-d72bd1fd11e0
npm run dev &
FRONTEND_PID=$!

echo "Both servers are running!"
echo "Frontend: http://localhost:5173"
echo "Backend: http://localhost:8000"
echo "Press Ctrl+C to stop both servers"

trap "echo 'Stopping servers...'; kill $FRONTEND_PID $BACKEND_PID; exit 0" INT TERM EXIT

wait 