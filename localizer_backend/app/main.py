"""
Main FastAPI application - Indian Language Localizer Backend
Production-ready AI-powered multilingual translation system
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time
import os
from app.core.config import get_settings
from app.core.db import init_db
from app.utils.logger import app_logger
from app.utils.metrics import get_metrics
from app.utils.performance import perf_monitor, cleanup_resources
from app.routes import content, translation, speech, feedback, logs
from app.middleware.request_logger import RequestLoggingMiddleware
from app.utils.server_logger import server_logger

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    """
    # Startup
    app_logger.info("Starting Indian Language Localizer Backend...")
    
    # Initialize database
    try:
        init_db()
        app_logger.info("Database initialized")
    except Exception as e:
        app_logger.error(f"Database initialization error: {e}")
    
    # Create storage directories
    storage_dirs = [
        settings.UPLOAD_DIR,
        settings.OUTPUT_DIR,
        "logs",
        "data/vocabs"
    ]
    
    for directory in storage_dirs:
        os.makedirs(directory, exist_ok=True)
    
    app_logger.info("Storage directories initialized")
    
    app_logger.info("Application startup complete")
    
    # Log server startup
    server_logger.log_server_activity(
        activity_type="startup",
        description="Indian Language Localizer Backend started successfully",
        details={
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "supported_languages": 22
        }
    )
    
    yield
    
    # Shutdown
    app_logger.info("Shutting down application...")
    
    # Log server shutdown
    server_logger.log_server_activity(
        activity_type="shutdown",
        description="Indian Language Localizer Backend shutting down",
        details={
            "uptime_seconds": time.time() - start_time if 'start_time' in locals() else 0
        }
    )
    
    cleanup_resources()
    app_logger.info("Resources cleaned up")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Multilingual Translation & Localization for 22 Indian Languages",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
app.add_middleware(
    RequestLoggingMiddleware,
    log_request_body=False,  # Set to True for debugging
    log_response_body=False  # Set to True for debugging
)


# Performance monitoring middleware
@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """Performance monitoring and request timing middleware"""
    start_time = time.time()
    perf_monitor.start_request()
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add timing headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = str(id(request))
        
        # Record metrics
        perf_monitor.end_request(process_time)
        
        return response
    except Exception as e:
        perf_monitor.end_request()
        raise e


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    app_logger.warning(f"Validation error: {exc}")
    
    # Convert errors to JSON-serializable format
    serializable_errors = []
    for error in exc.errors():
        serializable_error = {
            "type": error.get("type", "unknown"),
            "loc": error.get("loc", []),
            "msg": str(error.get("msg", "Validation error")),
            "input": str(error.get("input", ""))
        }
        serializable_errors.append(serializable_error)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "details": serializable_errors
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    app_logger.error("Unexpected error: {}", str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# Health check endpoint
@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - health check"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": time.time()
    }


@app.get("/health/db", tags=["Health"])
async def health_check_db():
    """Database health check"""
    try:
        from app.core.db import get_db
        from sqlalchemy import text
        
        # Test database connection
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": time.time()
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": time.time()
            }
        )


@app.get("/health/detailed", tags=["Health"])
async def health_check_detailed():
    """Detailed health check"""
    try:
        from app.core.db import get_db
        from sqlalchemy import text
        import psutil
        
        # Test database connection
        db_status = "unknown"
        try:
            db = next(get_db())
            db.execute(text("SELECT 1"))
            db.close()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Get system metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "status": "healthy" if db_status == "connected" else "degraded",
            "timestamp": time.time(),
            "database": db_status,
            "system": {
                "memory_usage": f"{memory.percent}%",
                "disk_usage": f"{disk.percent}%",
                "cpu_count": psutil.cpu_count()
            },
            "services": {
                "translation": "available",
                "speech": "available",
                "file_upload": "available"
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
        )


# Metrics endpoint
@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus metrics"""
    return get_metrics()


# Performance metrics endpoint
@app.get("/performance", tags=["Monitoring"])
async def performance_metrics():
    """Get current performance metrics"""
    return {
        "status": "ok",
        "metrics": perf_monitor.get_metrics(),
        "memory": perf_monitor.get_memory_info(),
        "system": perf_monitor.get_system_info()
    }


# System information endpoint
@app.get("/system/info", tags=["Monitoring"])
async def system_info():
    """Get comprehensive system information"""
    try:
        import psutil
        import torch
        from pathlib import Path
        
        # GPU Information
        gpu_info = {}
        if torch.cuda.is_available():
            gpu_info = {
                "available": True,
                "device_count": torch.cuda.device_count(),
                "current_device": torch.cuda.current_device(),
                "device_name": torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "Unknown",
                "memory_allocated_gb": f"{torch.cuda.memory_allocated() / 1024**3:.2f}" if torch.cuda.device_count() > 0 else "0",
                "memory_reserved_gb": f"{torch.cuda.memory_reserved() / 1024**3:.2f}" if torch.cuda.device_count() > 0 else "0"
            }
        else:
            gpu_info = {"available": False, "reason": "CUDA not available"}
        
        # Storage Information
        storage_info = {}
        storage_paths = ["storage/uploads", "storage/outputs", "logs"]
        for path_str in storage_paths:
            path = Path(path_str)
            if path.exists():
                try:
                    total_size = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
                    file_count = len([f for f in path.rglob('*') if f.is_file()])
                    storage_info[path_str] = {
                        "size_mb": f"{total_size / 1024**2:.2f}",
                        "file_count": file_count,
                        "exists": True
                    }
                except Exception:
                    storage_info[path_str] = {"exists": True, "error": "Cannot calculate size"}
            else:
                storage_info[path_str] = {"exists": False}
        
        # System Resources
        memory = psutil.virtual_memory()
        
        return {
            "system": {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory": {
                    "total_gb": f"{memory.total / 1024**3:.2f}",
                    "available_gb": f"{memory.available / 1024**3:.2f}",
                    "used_percent": f"{memory.percent}%"
                }
            },
            "gpu": gpu_info,
            "storage": storage_info,
            "environment": {
                "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}.{__import__('sys').version_info.micro}",
                "pytorch_version": torch.__version__,
                "cuda_version": torch.version.cuda if torch.cuda.is_available() else "N/A",
                "fastapi_environment": settings.ENVIRONMENT
            },
            "supported_languages_count": 22
        }
        
    except Exception as e:
        app_logger.error(f"System info error: {e}")
        return {
            "error": "Failed to retrieve system information",
            "details": str(e)
        }


# Include routers - No authentication required
app.include_router(content.router)
app.include_router(content.upload_router)  # Add simple upload router
app.include_router(translation.router)
app.include_router(speech.router)
app.include_router(feedback.simple_router)  # Add simple feedback router first
app.include_router(feedback.router)

# Add missing evaluation router (commented due to dependency conflicts)
# from app.routes import evaluation
# app.include_router(evaluation.router)

# Add jobs/background task router
from app.routes import jobs
app.include_router(jobs.router)

# Add new functionality routers
from app.routes import video, assessment, integration
app.include_router(video.router)
app.include_router(assessment.router)
app.include_router(integration.router)

# Add optimized routes for better performance
from app.routes import optimized_video
app.include_router(optimized_video.router)

# Add logging routes
app.include_router(logs.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )

