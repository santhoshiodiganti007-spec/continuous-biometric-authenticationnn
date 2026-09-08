"""Main FastAPI application entry point."""

import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api import auth, sessions, behavior, prediction, explainability

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("continuous_auth_api")

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Explainable Transformer-based continuous biometric authentication backend.",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please consult backend logs."}
    )

# Health endpoint (Phase 2 requirement)
@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint confirming system operational status."""
    return {"status": "running"}

# Register API Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(sessions.router, prefix=settings.API_V1_STR)
app.include_router(behavior.router, prefix=settings.API_V1_STR)
app.include_router(prediction.router, prefix=settings.API_V1_STR)
app.include_router(explainability.router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
