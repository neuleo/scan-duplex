#!/bin/bash

while true; do
    echo "[$(date)] - Running duplex merge script..."
    python /app/merge_duplex.py
    echo "[$(date)] - Script finished. Waiting 30 seconds..."
    sleep 30
done
