#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Set IP address for eth0
sudo ifconfig eth0 192.168.0.10/24 up

# Display the current network configuration
echo "Network configuration for eth0:"
ifconfig eth0

# Set IP address for eth1
sudo ifconfig eth1 192.168.1.200/24 up

# Display the current network configuration
echo "Network configuration for eth1:"
ifconfig eth1

echo "Installing python dependencies..."
pip install -r requirements.txt

cd app
echo "Setting up enviornment variables..."
cp example.env .env

echo "Starting the server"

python app.py

echo "Done."

