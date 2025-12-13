#!/bin/bash

# Initial setup script for Arcadium project

set -e

echo "Setting up Arcadium project..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Database
POSTGRES_USER=arcadium
POSTGRES_PASSWORD=arcadium_dev
POSTGRES_DB=arcadium

# Service URLs
AUTH_SERVICE_URL=http://auth:8000
GAME_SERVER_URL=http://game-server:8080
EOF
    echo ".env file created. Please review and update as needed."
fi

# Build Docker images
echo "Building Docker images..."
docker-compose build

# Start services
echo "Starting services..."
docker-compose up -d postgres

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Run migrations
echo "Running database migrations..."
./infrastructure/scripts/migrate.sh

echo "Setup complete!"
echo "You can now start all services with: docker-compose up"

