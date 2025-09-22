from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import os
from contextlib import asynccontextmanager

from routers import health, scans, findings
from routers import repositories, webhooks
from core.config import settings
from core.security import verify_token
from storage.db import init_db
from services.scheduler import scheduler_service

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    scheduler_service.start()
    yield
    # Shutdown
    scheduler_service.stop()

app = FastAPI(
    title="SecretHawk API",
    description="Production-ready secret scanner API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(scans.router, prefix="/api/v1", dependencies=[Depends(verify_token)])
app.include_router(findings.router, prefix="/api/v1", dependencies=[Depends(verify_token)])
app.include_router(repositories.router, prefix="/api/v1", dependencies=[Depends(verify_token)])
app.include_router(webhooks.router, prefix="/api/v1")  # No auth for webhooks

@app.get("/")
async def root():
    return {
        "name": "SecretHawk API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True if os.getenv("ENVIRONMENT") == "development" else False
    )