"""Main application entry point."""
import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
from dotenv import load_dotenv

from app.api.routes import router
from app.core.config import settings

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("compliance-verification")

# Create FastAPI app
app = FastAPI(
    title="Prompt Compliance Verification API",
    description="API for verifying if prompts comply with policies and regulations",
    version="1.0.0",
)

# Configure CORS
if settings.allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API routes
app.include_router(router)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Check if the API is healthy."""
    return {"status": "ok"}

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Prompt Compliance Verification API")
    logger.info(f"API running on {settings.api_host}:{settings.api_port}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Ensure directories exist
    os.makedirs(settings.policies_dir, exist_ok=True)
    os.makedirs(settings.policies_db_dir, exist_ok=True)
    os.makedirs("temp", exist_ok=True)

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Prompt Compliance Verification API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )