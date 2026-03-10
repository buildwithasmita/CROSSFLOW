# CROSSFLOW

CROSSFLOW is a cross-sell propensity engine for identifying which American Express GCS corporate cardholders are most likely to adopt personal Amex products. It combines synthetic corporate card behavior, life event detection, feature engineering, XGBoost scoring, and a React dashboard to prioritize the highest-value customer segments.

## Overview

- Objective: improve personal card conversion from broad marketing to targeted outreach
- Approach: detect life events and personal spend leakage on corporate cards, then score propensity with XGBoost
- Business framing: focus campaigns on the highest-propensity 30% of customers to improve conversion efficiency and reduce wasted outreach

## Tech Stack

- Backend: FastAPI, Pydantic, pandas, scikit-learn, XGBoost, SHAP
- Frontend: React, TypeScript, Tailwind CSS, Recharts
- Data: synthetic GCS customer generation with life-event and spend-pattern signals

## Repository Structure

- `Backend/` FastAPI services, models, notebooks, tests, and data
- `frontend/` React dashboard and API client
- `screenshots/` project visuals

## Environment

- Python: `3.13.4`
- Node.js: `20.x` recommended

## Local Setup

### Backend

```powershell
cd Backend
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm start
```

## Data Generation

```powershell
cd Backend
python -c "from app.utils.data_generator import generate_crossflow_customers; generate_crossflow_customers()"
```

This writes the dataset to `Backend/data/raw/gcs_customers.csv`.

## Model Training

Use the notebook at `Backend/notebooks/train_model.ipynb` or train directly from the backend environment. The trained model is expected at:

`Backend/data/models/crossflow_model.joblib`

## API

- Root: `http://localhost:8000/`
- Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/v1/health`

## Frontend

- App: `http://localhost:3000`
- Backend base URL configured in `frontend/.env`

## Docker

```powershell
docker compose up
```
