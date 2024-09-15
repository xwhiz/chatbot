#!/bin/sh

# Start the FastAPI application in the background
uvicorn main:app --host 0.0.0.0 --port 8000 &

# Wait for the API to be up
while ! curl -s http://localhost:8000/health; do
    echo "Waiting for API to be ready..."
    sleep 2
done

# Call the seed endpoint
curl -X POST http://localhost:8000/seed/create-admin \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjYW5DcmVhdGVBZG1pbiI6dHJ1ZX0.zvuMD2LN2EhoAGFWRST8Szspg5K8klvT0aZDqgyKB6w"

# Keep the script running to keep the container alive
wait
