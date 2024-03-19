#!/bin/bash

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)"
  exit 1
fi

# Set IP address for eth0
sudo ifconfig eth0 192.168.0.100/24 up

# Display the current network configuration
echo "Network configuration for eth0:"
ifconfig eth0

echo "Starting postgreSQL"
sudo service postgresql start

echo "Installing python dependencies"
pip install -r requirements.txt

echo "creating .env file"
cp app/example.env app/.env

echo "populating database"
cd app
python init_db.py

echo "Done."
