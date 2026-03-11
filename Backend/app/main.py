from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routes import scoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crossflow")

app = FastAPI(
    title="CROSSFLOW - Cross-Sell Propensity Engine",
    description="Predict personal card adoption for GCS corporate cardholders",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:8501",
        "https://crossflow-iota.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scoring.router)


@app.get("/")
def root() -> dict:
    return {
        "message": "CROSSFLOW API - Cross-Sell Propensity Engine",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "Predict which GCS corporate cardholders will adopt personal Amex cards",
    }


@app.on_event("startup")
def startup_event() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    env_path = base_dir / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    model_path = os.getenv("MODEL_PATH", "data/models/crossflow_model.joblib")
    resolved_model_path = (base_dir / model_path).resolve()
    model_exists = resolved_model_path.exists()

    logger.info("Starting CROSSFLOW API")
    logger.info("Environment: %s", os.getenv("ENVIRONMENT", "development"))
    logger.info("Model path: %s", resolved_model_path)
    if model_exists:
        logger.info("Model file found")
    else:
        logger.warning("Model file not found. Scoring endpoints will return 503 until model is available.")
