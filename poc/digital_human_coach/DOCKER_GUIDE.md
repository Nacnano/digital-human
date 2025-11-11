# Docker Setup Guide

This guide explains how to run the Digital Human Coach using Docker and Docker Compose.

## 📋 Prerequisites

- Docker Desktop installed ([Download](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)
- At least 4GB RAM available for containers

## 🚀 Quick Start

### 1. Configure Environment Variables

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
OPENAI_API_KEY=your_actual_key_here
GOOGLE_API_KEY=your_actual_key_here
# ... other keys
```

### 2. Start the Application

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode (background)
docker-compose up -d --build
```

### 3. Access the Application

- **Frontend UI**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Stop the Application

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## 📦 Docker Services

### Backend Service

- **Container**: `digital-human-backend`
- **Port**: 8000
- **Image**: Built from `Dockerfile.backend`
- **Purpose**: FastAPI REST API server

### Frontend Service

- **Container**: `digital-human-frontend`
- **Port**: 8501
- **Image**: Built from `Dockerfile.frontend`
- **Purpose**: Streamlit web interface

## 🔧 Docker Commands

### View Logs

```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart backend only
docker-compose restart backend

# Restart frontend only
docker-compose restart frontend
```

### Check Service Status

```bash
docker-compose ps
```

### Rebuild After Code Changes

```bash
# Rebuild and restart
docker-compose up --build

# Rebuild specific service
docker-compose build backend
docker-compose up -d backend
```

### Execute Commands in Container

```bash
# Backend shell
docker-compose exec backend bash

# Frontend shell
docker-compose exec frontend bash

# Run Python in backend
docker-compose exec backend python -c "print('Hello')"
```

## 🔍 Health Checks

The containers include health checks:

- **Backend**: `GET /health` endpoint
- **Frontend**: Streamlit health endpoint

Check health status:

```bash
docker-compose ps
```

## 🛠️ Development Mode

For development with hot-reload, mount your code as volumes:

```yaml
# In docker-compose.yml, add under backend service:
volumes:
  - ./app:/app/app
  - ./temp:/app/temp
```

Then restart:

```bash
docker-compose down
docker-compose up
```

## 📊 Resource Management

### View Resource Usage

```bash
docker stats
```

### Set Resource Limits

Edit `docker-compose.yml`:

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "1.0"
          memory: 1G
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs backend

# Rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up
```

### Permission Issues

```bash
# Fix temp directory permissions
chmod -R 777 temp/
```

### Network Issues

```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up
```

### Port Already in Use

```bash
# Find process using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Kill the process or change port in docker-compose.yml
```

### Clear Everything and Start Fresh

```bash
# Remove containers, networks, and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Remove all Docker data (CAUTION!)
docker system prune -a --volumes
```

## 🔒 Security Notes

### For Production:

1. **Never commit `.env` file** with real API keys
2. **Use Docker secrets** for sensitive data
3. **Set proper CORS origins** in backend
4. **Use HTTPS** with reverse proxy (nginx/traefik)
5. **Limit container resources**
6. **Regular security updates**:
   ```bash
   docker-compose pull
   docker-compose up --build
   ```

## 🚢 Production Deployment

### Using Docker Compose in Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Or specify env file
docker-compose --env-file .env.production up -d
```

### Deploy to Cloud

#### Docker Hub

```bash
# Tag images
docker tag digital-human-backend:latest yourusername/digital-human-backend:latest
docker tag digital-human-frontend:latest yourusername/digital-human-frontend:latest

# Push to Docker Hub
docker push yourusername/digital-human-backend:latest
docker push yourusername/digital-human-frontend:latest
```

#### AWS ECS, Google Cloud Run, Azure Container Instances

- Build and push images to respective container registries
- Configure environment variables in cloud console
- Deploy using cloud-specific tools

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

## 🆚 Docker vs Local Development

| Feature        | Docker             | Local         |
| -------------- | ------------------ | ------------- |
| Setup Time     | 5 minutes          | 15-30 minutes |
| Dependencies   | Isolated           | System-wide   |
| Consistency    | Guaranteed         | May vary      |
| Resource Usage | Higher             | Lower         |
| Hot Reload     | Yes (with volumes) | Yes           |
| Debugging      | More complex       | Easier        |

Choose Docker for:

- ✅ Consistent environments
- ✅ Easy deployment
- ✅ Team collaboration
- ✅ CI/CD pipelines

Choose Local for:

- ✅ Active development
- ✅ Debugging
- ✅ Lower resource usage
- ✅ Faster iteration
