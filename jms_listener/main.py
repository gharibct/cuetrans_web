"""
FastAPI JMSServlet Migration
Migrates from Java servlet to Python FastAPI
"""

from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import yaml
import logging.config
from pathlib import Path
from api.routes.JMSServlet import router as jms_router
from contextlib import asynccontextmanager
from utils.db.pool_manager import PoolManager
import uvicorn

import os
from dotenv import load_dotenv

# Explicitly load .env file (or use system env vars in production)
load_dotenv()  # This works everywhere, not just VS Code

BASE_DIR = Path(__file__).resolve().parent
logging_config_path = BASE_DIR / "core" / "config" / "logging.yaml"

# Load logging config from YAML
with open(logging_config_path, 'r') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)

routes = [
    jms_router,
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create pools
    await PoolManager().get_oracle_pool()
    yield
    # Shutdown: close pools
    await PoolManager().close_pools()

app = FastAPI(title="JMSServlet Migration", version="1.0.0", lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specify allowed origins: ["https://example.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
for route in routes:
    app.include_router(route)


@app.post("/test-jms")
async def test_jms(
    workFlowName: str = Form(...),
    workFlowParams: str = Form(...)
):
    return {"test": "success"}

# ============== Health Check ==============
@app.get("/health")
async def health():
    logger.info("Health check requested")
    return {"status": "ok", "service": "JMSServlet Migration"}

# ============== Run ==============
if __name__ == "__main__":
    
    # run with reloading option
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    # watchfiles --verbose . echo "Change detected"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_includes=["*.py", "*.yaml"],
        reload_excludes=["*.log", "*.log.*", "__pycache__/*"],
    )
    
