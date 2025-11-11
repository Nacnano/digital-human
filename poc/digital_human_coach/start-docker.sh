#!/bin/bash
# Quick start script for Digital Human App with Docker

echo "================================================"
echo "Digital Human App - Docker Quick Start"
echo "================================================"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker Desktop first."
    echo "   Download: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

echo "✅ Docker is installed and running"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please edit it with your API keys."
    echo ""
    echo "📝 Required steps:"
    echo "   1. Open .env file in a text editor"
    echo "   2. Add your API keys (OPENAI_API_KEY, etc.)"
    echo "   3. Run this script again"
    echo ""
    exit 0
fi

echo "✅ .env file found"
echo ""

# Ask user what to do
echo "Choose an action:"
echo "1) Start services (first time / rebuild)"
echo "2) Start services (quick start)"
echo "3) Stop services"
echo "4) View logs"
echo "5) Restart services"
echo "6) Clean up everything"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo "🔨 Building and starting services..."
        docker-compose up --build -d
        ;;
    2)
        echo ""
        echo "🚀 Starting services..."
        docker-compose up -d
        ;;
    3)
        echo ""
        echo "🛑 Stopping services..."
        docker-compose down
        ;;
    4)
        echo ""
        echo "📋 Viewing logs (Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
    5)
        echo ""
        echo "🔄 Restarting services..."
        docker-compose restart
        ;;
    6)
        echo ""
        read -p "⚠️  This will remove all containers, volumes, and data. Continue? [y/N]: " confirm
        if [[ $confirm == [yY] ]]; then
            echo "🧹 Cleaning up..."
            docker-compose down -v --rmi all
            echo "✅ Cleanup complete"
        else
            echo "❌ Cancelled"
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

# Show status and access info
if [[ $choice != "3" && $choice != "6" ]]; then
    echo ""
    echo "⏳ Waiting for services to be ready..."
    sleep 5
    
    echo ""
    echo "================================================"
    echo "🎉 Services Status:"
    echo "================================================"
    docker-compose ps
    
    echo ""
    echo "📍 Access Points:"
    echo "   Frontend UI:  http://localhost:8501"
    echo "   Backend API:  http://localhost:8000"
    echo "   API Docs:     http://localhost:8000/docs"
    echo ""
    echo "📊 View logs:     docker-compose logs -f"
    echo "🛑 Stop services: docker-compose down"
    echo ""
fi
