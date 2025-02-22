from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import uvicorn
from pricing_service import PricingService
from ml_service import MedicineRecommender

app = FastAPI(title="MediMeal API")
ml_service = MedicineRecommender()

# RxNorm API base URL
RXNORM_API_BASE = "https://rxnav.nlm.nih.gov/REST"

# Data Models
class MedicationRequest(BaseModel):
    drug_name: str
    dosage: Optional[str] = None
    condition: Optional[str] = None
    dietary_restrictions: Optional[List[str]] = None
    current_diet: Optional[List[str]] = None

class MedicationInfo(BaseModel):
    name: str
    rxcui: str
    dosage: Optional[str] = None
    details: Dict  # To store all RxNav API responses
    condition_info: Optional[Dict] = None  # For condition matching

class DietRecommendation(BaseModel):
    foods_to_eat: List[str]
    foods_to_avoid: List[str]
    meal_timing: str
    special_instructions: str
    recipes: List[Dict[str, str]]

class DrugInteraction(BaseModel):
    severity: str
    description: str
    recommendation: str

class AnalysisResponse(BaseModel):
    medication_details: MedicationInfo
    alternatives: List[MedicationInfo]
    diet_recommendations: DietRecommendation
    interactions: List[DrugInteraction]
    condition_specific_diet: Optional[Dict[str, List[str]]]

async def get_rxnorm_details(drug_name: str) -> Dict:
    """Get detailed drug information from RxNorm"""
    try:
        # Search for drug
        search_url = f"{RXNORM_API_BASE}/drugs?name={drug_name}"
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()

        if 'drugGroup' not in data or 'conceptGroup' not in data['drugGroup']:
            return None

        # Get first matching drug
        for group in data['drugGroup']['conceptGroup']:
            if 'conceptProperties' in group:
                drug = group['conceptProperties'][0]
                rxcui = drug['rxcui']

                # Get additional details
                details_url = f"{RXNORM_API_BASE}/rxcui/{rxcui}/allrelated"
                ingredients_url = f"{RXNORM_API_BASE}/rxcui/{rxcui}/ingredients"
                
                details_response = requests.get(details_url)
                ingredients_response = requests.get(ingredients_url)

                return {
                    "basic_info": drug,
                    "details": details_response.json(),
                    "ingredients": ingredients_response.json()
                }

        return None
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to MediMeal API"}

@app.get("/search")
async def search_medications(query: str, condition: Optional[str] = None):
    """Search medications with optional condition filtering"""
    try:
        # Use RxNav API for drug search
        url = f"{RXNORM_API_BASE}/drugs.json?name={query}"
        response = requests.get(url)
        response.raise_for_status()
        
        results = []
        if 'drugGroup' in response.json() and 'conceptGroup' in response.json()['drugGroup']:
            for group in response.json()['drugGroup']['conceptGroup']:
                if 'conceptProperties' in group:
                    for prop in group['conceptProperties']:
                        rxcui = prop.get('rxcui')
                        if rxcui:
                            # Get additional details
                            details = await get_drug_details(rxcui)
                            
                            # If condition is specified, check indications
                            if condition:
                                indication_url = f"{RXNORM_API_BASE}/rxclass/class/byRxcui.json?rxcui={rxcui}"
                                ind_response = requests.get(indication_url)
                                
                                condition_info = {
                                    'matches': False,
                                    'indications': []
                                }
                                
                                if ind_response.status_code == 200:
                                    ind_data = ind_response.json()
                                    if 'rxclassMinConceptList' in ind_data:
                                        for concept in ind_data['rxclassMinConceptList']['rxclassMinConcept']:
                                            class_name = concept.get('className', '').lower()
                                            condition_info['indications'].append(class_name)
                                            if condition.lower() in class_name:
                                                condition_info['matches'] = True
                                
                                results.append({
                                    'name': prop.get('name', ''),
                                    'rxcui': rxcui,
                                    'details': details,
                                    'condition_info': condition_info
                                })
                            else:
                                results.append({
                                    'name': prop.get('name', ''),
                                    'rxcui': rxcui,
                                    'details': details
                                })
            
            # If condition is specified, sort results to show condition-related medications first
            if condition and results:
                results.sort(key=lambda x: x.get('condition_info', {}).get('matches', False), reverse=True)
            
            return results[:10]  # Limit to 10 results
        return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def get_drug_details(rxcui: str) -> Dict:
    """Get detailed drug information using RxNav API"""
    try:
        endpoints = {
            'properties': f"{RXNORM_API_BASE}/rxcui/{rxcui}/properties.json",
            'ingredients': f"{RXNORM_API_BASE}/rxcui/{rxcui}/related.json?tty=IN",
            'allrelated': f"{RXNORM_API_BASE}/rxcui/{rxcui}/allrelated.json"
        }
        
        results = {}
        for key, url in endpoints.items():
            response = requests.get(url)
            if response.status_code == 200:
                results[key] = response.json()
            else:
                results[key] = {}
                
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_medication(request: MedicationRequest):
    """Analyze medication and provide recommendations"""
    try:
        # Get drug details from RxNorm
        drug_data = await get_rxnorm_details(request.drug_name)
        if not drug_data:
            raise HTTPException(status_code=404, detail="Medication not found")

        # Extract basic medication info
        basic_info = drug_data["basic_info"]
        
        # Get pricing data
        pricing_data = await PricingService.get_combined_pricing(request.drug_name)
        
        # Create medication info
        medication_details = MedicationInfo(
            name=basic_info["name"],
            rxcui=basic_info["rxcui"],
            dosage=request.dosage,
            details=drug_data["details"],
            condition_info={
                "matches": False,
                "indications": []
            }
        )

        # Get alternatives with pricing
        alternatives = []
        if "allRelatedGroup" in drug_data["details"]:
            for group in drug_data["details"]["allRelatedGroup"].get("conceptGroup", []):
                if group.get("tty") in ["SBD", "SCD"]:  # Brand and Clinical Drugs
                    for prop in group.get("conceptProperties", []):
                        alt_pricing = await PricingService.get_combined_pricing(prop["name"])
                        alternatives.append(
                            MedicationInfo(
                                name=prop["name"],
                                rxcui=prop["rxcui"],
                                details=drug_data["details"],
                                condition_info={
                                    "matches": False,
                                    "indications": []
                                }
                            )
                        )

        # Generate diet recommendations
        diet_rec = DietRecommendation(
            foods_to_eat=[
                "Whole grains",
                "Leafy vegetables",
                "Lean proteins",
                "Fresh fruits",
                "Low-fat dairy"
            ],
            foods_to_avoid=[
                "Grapefruit (may interact with medication)",
                "High-sodium foods",
                "Processed sugars",
                "Alcohol"
            ],
            meal_timing="Take medication 1 hour before meals or 2 hours after meals",
            special_instructions="Stay hydrated and maintain consistent meal times",
            recipes=[
                {
                    "name": "Mediterranean Quinoa Bowl",
                    "ingredients": "Quinoa, vegetables, olive oil",
                    "instructions": "Cook quinoa, add vegetables..."
                }
            ]
        )

        # Generate interactions
        interactions = [
            DrugInteraction(
                severity="High",
                description="Avoid grapefruit juice",
                recommendation="Do not consume grapefruit or its juice"
            ),
            DrugInteraction(
                severity="Medium",
                description="Take with food",
                recommendation="Take medication with meals to reduce stomach upset"
            )
        ]

        return AnalysisResponse(
            medication_details=medication_details,
            alternatives=alternatives,
            diet_recommendations=diet_rec,
            interactions=interactions,
            condition_specific_diet={
                "recommended": ["Low-sodium options", "High-fiber foods"],
                "avoid": ["Processed foods", "Added sugars"]
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/recommendations/{medicine_name}")
async def get_recommendations(medicine_name: str):
    """Get similar medicine recommendations"""
    recommendations = ml_service.get_similar_medicines(medicine_name)
    if not recommendations:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return recommendations

@app.get("/side-effects/{medicine_name}")
async def get_side_effects(medicine_name: str):
    """Get side effects for a medicine"""
    side_effects = ml_service.get_side_effects(medicine_name)
    if not side_effects['side_effects']:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return side_effects

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)