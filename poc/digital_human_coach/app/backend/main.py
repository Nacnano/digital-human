"""
FastAPI Backend Server for Digital Human Communication Coach
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.backend.api import conversation, evaluation, audio2face
from app.utils.storage import StorageService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for the application"""
    # Startup
    logger.info("Starting Digital Human App API server...")
    
    # Initialize storage
    storage = StorageService()
    storage.initialize()
    
    # Create temp directories
    temp_dir = Path("temp")
    temp_dir.mkdir(exist_ok=True)
    (temp_dir / "sessions").mkdir(exist_ok=True)
    (temp_dir / "uploads").mkdir(exist_ok=True)
    
    logger.info("Server startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down server...")
    # Cleanup old sessions
    storage.cleanup_old_sessions(max_age_hours=24)
    logger.info("Server shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Digital Human Communication Coach API",
    description="Multi-modal AI-powered communication coaching system",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
if os.path.exists("temp"):
    app.mount("/temp", StaticFiles(directory="temp"), name="temp")

# Include routers
app.include_router(conversation.router, prefix="/api/conversation", tags=["conversation"])
app.include_router(evaluation.router, prefix="/api/evaluation", tags=["evaluation"])
app.include_router(audio2face.router, prefix="/api/audio2face", tags=["audio2face"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Digital Human Communication Coach API",
        "version": "0.1.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "services": {
            "api": "operational",
            "storage": "operational"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
