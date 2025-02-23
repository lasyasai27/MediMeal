from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import uvicorn
from typing import Dict
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import requests
import os
from nutritional_model import nutritional_model
from ml.preprocess_drugs import preprocess_drug_data
from ml.drug_recommender import DrugRecommender
from ml.medicare_drug_analysis import MedicareDrugAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="MediMeal API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log requests
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

@app.on_event("startup")
async def startup_event():
    logger.info("=== Starting MediMeal API Server ===")
    logger.info("Initializing server components...")
    try:
        # Add any initialization code here
        logger.info("✓ Server components initialized successfully")
        # Initialize the analyzer when the server starts
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, 'data', 'DSD_PTD_RY24_P04_V10_DY22_BGM.csv')
        
        analyzer = MedicareDrugAnalyzer()
        analyzer.train_model(data_path)
        logger.info("Medicare Drug Analyzer initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize server: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=== Shutting down MediMeal API Server ===")
    # Add any cleanup code here

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

class ModelTrainer:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.models = {}
        
    def train_all_models(self):
        print("Training models for available datasets...")
        self.train_medication_model()
        self.train_side_effects_model()
        self.train_interactions_model()

    def train_medication_model(self):
        try:
            print("\n1. Training Medication Search Model...")
            df = pd.read_csv(os.path.join(self.data_dir, 'drugs_side_effects_drugs_com.csv'))
            
            text_data = df['drug_name'].fillna('') + ' ' + \
                       df['medical_condition'].fillna('') + ' ' + \
                       df['side_effects'].fillna('')
            
            vectorizer = TfidfVectorizer(max_features=5000)
            vectors = vectorizer.fit_transform(text_data)
            
            model = NearestNeighbors(n_neighbors=5, metric='cosine')
            model.fit(vectors)
            
            self.models['medication'] = {
                'vectorizer': vectorizer,
                'model': model,
                'data': df
            }
            print("✓ Medication Search Model trained")
            
        except Exception as e:
            print(f"Error training medication model: {e}")

    def train_side_effects_model(self):
        try:
            print("\n2. Training Side Effects Model...")
            df = pd.read_csv(os.path.join(self.data_dir, 'drugs_side_effects_drugs_com.csv'))
            
            X = df['side_effects'].fillna('')
            y = df['medical_condition'].fillna('')
            
            vectorizer = TfidfVectorizer(max_features=5000)
            X_vec = vectorizer.fit_transform(X)
            
            model = RandomForestClassifier(n_estimators=100)
            model.fit(X_vec, y)
            
            self.models['side_effects'] = {
                'vectorizer': vectorizer,
                'model': model
            }
            print("✓ Side Effects Model trained")
            
        except Exception as e:
            print(f"Error training side effects model: {e}")

    def train_interactions_model(self):
        try:
            print("\n3. Training Drug Interactions Model...")
            # Add your interactions model training here
            print("✓ Drug Interactions Model placeholder")
            
        except Exception as e:
            print(f"Error training interactions model: {e}")

    def search_medications(self, query: str, condition: Optional[str] = None) -> List[MedicationDetails]:
        try:
            if 'medication' not in self.models:
                raise ValueError("Medication model not trained")
            
            model_dict = self.models['medication']
            df = model_dict['data']
            
            vector = model_dict['vectorizer'].transform([query])
            _, indices = model_dict['model'].kneighbors(vector)
            
            results = []
            for idx in indices[0]:
                med = df.iloc[idx]
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
            print(f"Error searching medications: {e}")
            return []

# Initialize trainer
trainer = ModelTrainer()
trainer.train_all_models()

# Initialize the drug recommender
try:
    df, label_encoder = preprocess_drug_data()
    drug_recommender = DrugRecommender(df)
    logger.info("Successfully initialized drug recommender")
except Exception as e:
    logger.error(f"Failed to initialize drug recommender: {str(e)}")
    # Initialize with empty dataframe as fallback
    df = pd.DataFrame()
    drug_recommender = None

# Define the DrugFeatures class first
class DrugFeatures(BaseModel):
    total_claims: float
    total_beneficiaries: float
    total_dosage_units: float
    avg_spending_per_claim: float
    avg_spending_per_beneficiary: float

@app.get("/")
async def root():
    logger.info("Processing root endpoint request")
    return {
        "status": "online",
        "message": "MediMeal API is running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check() -> Dict:
    logger.info("Processing health check request")
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "uptime": "available"  # You can add actual uptime calculation here
    }

@app.get("/search/medications")
async def search_medications(query: str, condition: str = None):
    logger.info(f"Searching medications with query: {query}, condition: {condition}")
    try:
        results = trainer.search_medications(query, condition)
        return results
    except Exception as e:
        logger.error(f"Error searching medications: {str(e)}")
        raise

@app.get("/medications/{medication_name}/alternatives")
async def get_alternatives(medication_name: str) -> List[MedicationDetails]:
    try:
        results = trainer.search_medications(medication_name)
        return results[1:] if len(results) > 1 else []
    except Exception as e:
        raise

@app.get("/health/predict")
async def predict_health_metrics(
    weight: float,
    bmi: float,
    fat_mass: float,
    muscle_mass: float,
    visceral_fat: float,
    metabolism: float,
    waist: float,
    hip: float
):
    """Predict health metrics based on current measurements"""
    input_data = {
        'current_weight_kg': weight,
        'bmi_kg_m2': bmi,
        'fat_mass_perc': fat_mass,
        'muscle_mass_perc': muscle_mass,
        'visceral_fat_level': visceral_fat,
        'basal_metabolism': metabolism,
        'waist_cm': waist,
        'hip_cm': hip
    }
    
    predictions = nutritional_model.predict_metrics(input_data)
    return predictions

@app.get("/health/trends/{user_id}")
async def get_health_trends(user_id: int):
    """Get health trends for a specific user"""
    trends = nutritional_model.analyze_trends(user_id)
    return trends

@app.get("/api/drug-recommendations/{drug_name}")
async def get_drug_recommendations(drug_name: str):
    if drug_recommender is None:
        return {
            "status": "error",
            "message": "Drug recommender not initialized"
        }
    try:
        recommendations = drug_recommender.get_recommendations(drug_name)
        return {
            "status": "success",
            "recommendations": recommendations.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error getting drug recommendations: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/api/predict-spending")
async def predict_spending(features: DrugFeatures):
    try:
        result = analyzer.predict_spending(features.dict())
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['error'])
        return result
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {str(exc)}")
    return {
        "status": "error",
        "message": str(exc),
        "path": str(request.url)
    }

if __name__ == "__main__":
    logger.info("Starting uvicorn server...")
    try:
        uvicorn.run("server:app",
            app,
            host="127.0.0.1",
            port=3000,
            log_level="info"
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")