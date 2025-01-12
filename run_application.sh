#!/bin/bash

run_frontend() {
    echo "Starting frontend..."
    cd frontend
    npm run start
}

run_fastapi() {
    echo "Starting FastAPI..."
    cd api
    source env/bin/activate
    fastapi run main.py
}

# Run both functions in parallel
run_frontend &
run_fastapi &

# Wait for the API to be up
while ! curl -s http://localhost:8000/health > /dev/null; do
    echo "Waiting for API to be ready..."
    sleep 2
done

echo ""
echo "API is ready!"

# Call get token endpoint
token_response=$(curl -s -X POST http://localhost:8000/auth/can-create-admin-token \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=admin&password=admin123")

# Extract token (assumes the API returns JSON with a "token" field)
token=$(echo "$token_response" | grep -o '"token":"[^"]*"' | sed -E 's/"token":"(.*)"/\1/')

# Check if token is valid
if [ "$token" == "null" ] || [ -z "$token" ]; then
    echo "Failed to retrieve a valid token. Exiting..."
    kill 0 # Kill all background processes
    exit 1
fi

echo "Token retrieved: $token"

# Call the seed endpoint with the retrieved token
curl -s -X POST http://localhost:8000/seed/create-admin \
    -H "Authorization: Bearer $token"

echo ""
echo "Application is ready!"

# Wait for both processes to finish
wait

echo "Both processes have finished."