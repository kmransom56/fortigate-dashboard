#!/bin/bash

# Script to set FortiSwitch environment variables and restart the application

# Prompt for FortiSwitch connection details
echo "Please enter your FortiSwitch connection details:"
read -p "FortiSwitch Host (e.g., https://192.168.0.1): " FORTISWITCH_HOST
read -p "FortiSwitch Username: " FORTISWITCH_USERNAME
read -p "FortiSwitch Password: " -s FORTISWITCH_PASSWORD
echo ""

# Create or update .env file
echo "Updating .env file with FortiSwitch connection details..."
if [ -f .env ]; then
    # Remove existing FortiSwitch variables if they exist
    sed -i '/FORTISWITCH_HOST/d' .env
    sed -i '/FORTISWITCH_USERNAME/d' .env
    sed -i '/FORTISWITCH_PASSWORD/d' .env
    
    # Add new FortiSwitch variables
    echo "FORTISWITCH_HOST=$FORTISWITCH_HOST" >> .env
    echo "FORTISWITCH_USERNAME=$FORTISWITCH_USERNAME" >> .env
    echo "FORTISWITCH_PASSWORD=$FORTISWITCH_PASSWORD" >> .env
else
    # Create new .env file
    echo "FORTISWITCH_HOST=$FORTISWITCH_HOST" > .env
    echo "FORTISWITCH_USERNAME=$FORTISWITCH_USERNAME" >> .env
    echo "FORTISWITCH_PASSWORD=$FORTISWITCH_PASSWORD" >> .env
fi

echo "Environment variables set successfully!"

# Ask if the user wants to restart the application
read -p "Do you want to restart the application now? (y/n): " RESTART
if [[ $RESTART == "y" || $RESTART == "Y" ]]; then
    echo "Restarting the application..."
    
    # Check if Docker is being used
    if [ -f docker-compose.yml ]; then
        docker-compose down
        docker-compose up -d
    else
        # Restart using the build_and_run.sh script if it exists
        if [ -f build_and_run.sh ]; then
            ./build_and_run.sh
        else
            echo "Could not find a way to restart the application automatically."
            echo "Please restart the application manually."
        fi
    fi
else
    echo "Please restart the application manually when ready."
fi

echo "Done!"