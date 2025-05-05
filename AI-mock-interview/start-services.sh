#!/bin/bash

# Start nginx in the background
nginx -g 'daemon off;' &
NGINX_PID=$!

# Start FastAPI server in the background
cd /app
python3 app.py &
FASTAPI_PID=$!

# Log that all services are running
echo "Nginx serving frontend on port 80"
echo "FastAPI server running on port ${PORT:-8080}"

# Handle termination signal
trap "kill $NGINX_PID $FASTAPI_PID; exit" SIGINT SIGTERM

# Wait for processes to exit
wait $NGINX_PID $FASTAPI_PID 