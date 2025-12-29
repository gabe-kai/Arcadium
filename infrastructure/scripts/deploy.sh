#!/bin/bash

# Deployment script for Arcadium services

set -e

ENVIRONMENT="${1:-production}"

echo "Deploying Arcadium services to $ENVIRONMENT..."

# Validate environment
if [ "$ENVIRONMENT" != "production" ] && [ "$ENVIRONMENT" != "staging" ]; then
    echo "Error: Environment must be 'production' or 'staging'"
    exit 1
fi

# Build images
echo "Building Docker images..."
docker-compose -f docker-compose.yml -f infrastructure/docker/docker-compose.prod.yml build

# Run migrations
echo "Running database migrations..."
./infrastructure/scripts/migrate.sh

# Deploy services
echo "Deploying services..."
docker-compose -f docker-compose.yml -f infrastructure/docker/docker-compose.prod.yml up -d

echo "Deployment complete!"
