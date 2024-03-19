#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Set IP address for eth0
sudo ifconfig eth0 192.168.1.50/24 up

# Display the current network configuration
echo "Network configuration for eth0:"
ifconfig eth0

echo "Installing python dependencies..."
pip install -r requirements.txt

cd app
echo "Setting up enviornment variables..."
cp example.env cli/.env

cd cli
echo "Making keys directory"
mkdir -p keys

echo "Starting the client"
echo "Done. You can start the client by going to app/cli and doing python client.py <your_family_key>.pem"
