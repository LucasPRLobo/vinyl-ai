#!/bin/bash
# Start Cloudflare quick tunnels for Crate
# Run this AFTER docker compose up and uvicorn are running

echo "Starting Cloudflare tunnels..."
echo "Make sure these are running first:"
echo "  1. docker compose up (in crate/)"
echo "  2. uvicorn app.main:app --reload (in crate/backend/)"
echo "  3. npm run dev (in crate/frontend/)"
echo ""

# Start API tunnel in background, capture URL
echo "Starting API tunnel (port 8000)..."
cloudflared tunnel --url http://localhost:8000 2>&1 | tee /tmp/crate-api-tunnel.log &
API_PID=$!

sleep 5

# Extract the API tunnel URL
API_URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /tmp/crate-api-tunnel.log | head -1)
echo ""
echo "============================================"
echo "API URL: $API_URL"
echo "============================================"
echo ""

if [ -z "$API_URL" ]; then
    echo "ERROR: Could not get API tunnel URL. Check /tmp/crate-api-tunnel.log"
    kill $API_PID 2>/dev/null
    exit 1
fi

echo "Now update your frontend .env.local:"
echo "  echo 'NEXT_PUBLIC_API_URL=$API_URL' > ../frontend/.env.local"
echo ""
echo "Then restart the frontend (npm run dev) and start the frontend tunnel:"
echo "  cloudflared tunnel --url http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the API tunnel."
wait $API_PID
