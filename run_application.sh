#!/bin/bash

docker compose up -d --build

# Wait for the API to be up
while ! curl -s http://localhost:8000/health; do
    echo "Waiting for API to be ready..."
    sleep 2
done

echo ""
echo "API is ready!"

# Call the seed endpoint
curl -X POST http://localhost:8000/seed/create-admin \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjYW5DcmVhdGVBZG1pbiI6dHJ1ZX0.zvuMD2LN2EhoAGFWRST8Szspg5K8klvT0aZDqgyKB6w"

echo ""
echo "Application is ready!"
