#!/bin/bash

# Ensure data directory exists
mkdir -p /data/logs

# If config.json doesn't exist, create a default empty one
if [ ! -f /data/config.json ]; then
    echo '{}' > /data/config.json
fi

# Start the Node.js web server
cd /app/webui
exec node server.js