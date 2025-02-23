from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import Dict, List, Optional
import logging
import time
import uvicorn
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import RandomForestClassifier
import os
from functools import lru_cache

# =====================================
# Configuration and Settings
# =====================================
class Settings(BaseSettings):
    APP_NAME: str = "MediMeal API"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    DATA_DIR: str = "data"
    MODEL_DIR: str = "models"
    
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()

# Load settings and construct the full path for the CSV file
settings = get_settings()
data_file_path = os.path.join(settings.DATA_DIR, "nadac-national-average-drug-acquisition-cost-12-25-2024.csv")
df_prices = pd.read_csv(data_file_path)

def get_medication_prices(medication_name):
    """
    Returns a DataFrame filtered for a given medication name.
    Adjust column names to match your CSV file.
    """
    filtered = df_prices[df_prices['medication'].str.lower() == medication_name.lower()]
    return filtered[['provider', 'price']]

# =====================================
# Logging Configuration
# =====================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# =====================================
# Data Models
# =====================================
class MedicationDetails(BaseModel):
    name: str
    condition: Optional[str]
    side_effects: List[str]
    active_ingredients: List[str]
    form: Optional[str]
    interactions: List[str]
    storage: List[str]
    guidelines: List[str]
    warnings: List[str]

class DrugFeatures(BaseModel):
    total_claims: float
    total_beneficiaries: float
    total_dosage_units: float
    avg_spending_per_claim: float
    avg_spending_per_beneficiary: float

class HealthMetrics(BaseModel):
    weight: float
    bmi: float
    fat_mass: float
    muscle_mass: float
    visceral_fat: float
    metabolism: float
    waist: float
    hip: float

# =====================================
# Service Classes
# =====================================
class MedicationService:
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.vectorizer = None
        self.model = None
        self.data = None
        self._initialize_models()
    
    def _initialize_models(self):
        try:
            logger.info("Initializing medication models...")
            df = pd.read_csv(os.path.join(self.data_dir, 'drugs_side_effects_drugs_com.csv'))
            
            # Prepare text data for vectorization
            text_data = df['drug_name'].fillna('') + ' ' + \
                        df['medical_condition'].fillna('') + ' ' + \
                        df['side_effects'].fillna('')
            
            # Initialize and fit vectorizer
            self.vectorizer = TfidfVectorizer(max_features=5000)
            vectors = self.vectorizer.fit_transform(text_data)
            
            # Initialize and fit nearest neighbors model
            self.model = NearestNeighbors(n_neighbors=5, metric='cosine')
            self.model.fit(vectors)
            
            self.data = df
            logger.info("Medication models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing medication models: {e}")
            raise

    def search_medications(self, query: str, condition: Optional[str] = None) -> List[MedicationDetails]:
        try:
            if not self.model or not self.vectorizer:
                raise ValueError("Models not initialized")
            
            # Transform query and find nearest neighbors
            vector = self.vectorizer.transform([query])
            _, indices = self.model.kneighbors(vector)
            
            results = []
            for idx in indices[0]:
                med = self.data.iloc[idx]
                result = MedicationDetails(
                    name=med['drug_name'],
                    condition=med['medical_condition'],
                    side_effects=med['side_effects'].split(',') if isinstance(med['side_effects'], str) else [],
                    active_ingredients=['Active ingredient information not available'],
                    form='Tablet',
                    interactions=['Avoid alcohol', 'Check with your doctor about other medications'],
                    storage=[
                        'Store between 68-77°F (20-25°C)',
                        'Keep away from moisture',
                        'Keep in original container'
                    ],
                    guidelines=[
                        'Take as prescribed',
                        'Complete the full course',
                        'Take at regular intervals'
                    ],
                    warnings=[
                        'May cause drowsiness',
                        'Take with food',
                        'Keep out of reach of children'
                    ]
                )
                results.append(result)
            
            return results
        except Exception as e:
            logger.error(f"Error searching medications: {e}")
            return []

class HealthPredictor:
    def predict_metrics(self, metrics: HealthMetrics) -> Dict:
        # Placeholder for health prediction logic
        return {
            "predicted_weight": metrics.weight * 0.95,
            "predicted_bmi": metrics.bmi * 0.95,
            "health_score": 85,
            "recommendations": [
                "Maintain regular exercise",
                "Keep a balanced diet",
                "Stay hydrated"
            ]
        }

# =====================================
# FastAPI Application
# =====================================
app = FastAPI(title="MediMeal API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================
# Dependencies
# =====================================
@lru_cache
def get_medication_service() -> MedicationService:
    settings = get_settings()
    return MedicationService(settings.DATA_DIR)

@lru_cache
def get_health_predictor() -> HealthPredictor:
    return HealthPredictor()

# =====================================
# Middleware
# =====================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Starting request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Request completed in {process_time:.2f} seconds")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise

# =====================================
# Event Handlers
# =====================================
@app.on_event("startup")
async def startup_event():
    logger.info("=== Starting MediMeal API Server ===")
    # Initialize services
    get_medication_service()
    get_health_predictor()
    logger.info("✓ Server components initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=== Shutting down MediMeal API Server ===")

# =====================================
# API Endpoints
# =====================================
@app.get("/")
async def root(settings: Settings = Depends(get_settings)):
    return {
        "status": "online",
        "message": f"{settings.APP_NAME} is running",
        "version": settings.VERSION
    }

@app.get("/health")
async def health_check() -> Dict:
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": "available"
    }

@app.get("/search/medications")
async def search_medications(
    query: str,
    condition: Optional[str] = None,
    med_service: MedicationService = Depends(get_medication_service)
):
    logger.info(f"Searching medications with query: {query}, condition: {condition}")
    try:
        results = med_service.search_medications(query, condition)
        return results
    except Exception as e:
        logger.error(f"Error searching medications: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/medications/{medication_name}/alternatives")
async def get_alternatives(
    medication_name: str,
    med_service: MedicationService = Depends(get_medication_service)
) -> List[MedicationDetails]:
    try:
        results = med_service.search_medications(medication_name)
        return results[1:] if len(results) > 1 else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/health/predict")
async def predict_health_metrics(
    metrics: HealthMetrics,
    predictor: HealthPredictor = Depends(get_health_predictor)
):
    try:
        predictions = predictor.predict_metrics(metrics)
        return predictions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# =====================================
# Exception Handlers
# =====================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {str(exc)}")
    return {
        "status": "error",
        "message": str(exc),
        "path": str(request.url)
    }

# =====================================
# Main Entry Point
# =====================================
if __name__ == "__main__":
    logger.info("Starting uvicorn server...")
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=3000,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
