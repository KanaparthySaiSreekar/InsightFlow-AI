#!/bin/bash

echo "==================================="
echo "  InsightFlow AI - Quick Start"
echo "==================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Check if encryption key is set
if grep -q "your-fernet-key-change-in-production" docker-compose.yml; then
    echo "⚠️  Warning: You need to configure the encryption key in docker-compose.yml"
    echo ""
    echo "Generating a new encryption key..."
    python3 -c "from cryptography.fernet import Fernet; print('Your encryption key:', Fernet.generate_key().decode())"
    echo ""
    echo "Please edit docker-compose.yml and replace:"
    echo "  - your-secret-key-change-in-production"
    echo "  - your-fernet-key-change-in-production"
    echo ""
    read -p "Have you updated the keys? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🚀 Starting InsightFlow AI..."
echo ""

# Start Docker containers
docker-compose up -d

echo ""
echo "✅ InsightFlow AI is starting!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
echo ""
