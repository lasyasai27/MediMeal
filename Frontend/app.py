import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
from datetime import datetime


# Constants
API_URL = "http://127.0.0.1:8000"  # Changed from 8001 to 8000
RXNORM_API = "https://rxnav.nlm.nih.gov/REST"


# Initialize session state
if 'saved_medications' not in st.session_state:
   st.session_state.saved_medications = []
if 'recent_searches' not in st.session_state:
   st.session_state.recent_searches = []

# Medication Prices Dictionary
MEDICATION_PRICES = {
    "hydrochlorothiazide / losartan": 75.00,
    "gabapentin": 73.00,
    "sertraline": 69.00,
    "levothyroxine": 16.00,
    "atorvastatin": 140.00,
    "escitalopram": 531.00,
    "fluoxetine": 64.00,
    "pantoprazole": 260.00,
    "amiloride / hydrochlorothiazide": 7.00,
    "Prednisone": 7.00,
    "Acetaminophen (Tylenol)": 10.00,
    "Ibuprofen (Advil)": 11.00,
    "aspirin": 5.00,
    "amoxicillin": 5.50,
    "lisinopril": 24.00,
    "glipizide / metformin": 30.00,
    "amlodipine": 43.00,
    "metoprolol": 20.00,
    "omeprazole": 18.00,
    "ezetimibe / simvastatin": 120.00,
    "prednisone": 18.00
}

MEDICATION_INGREDIENTS = {
    "hydrochlorothiazide / losartan": ["Hydrochlorothiazide", "Losartan Potassium"],
    "gabapentin": ["Gabapentin"],
    "sertraline": ["Sertraline Hydrochloride"],
    "levothyroxine": ["Levothyroxine Sodium"],
    "atorvastatin": ["Atorvastatin Calcium"],
    "Metformin": ["Metformin Hydrochloride"],
    "escitalopram": ["Escitalopram Oxalate"],
    "fluoxetine": ["Fluoxetine Hydrochloride"],
    "pantoprazole": ["Pantoprazole Sodium"],
    "Acetaminophen (Tylenol)": ["Acetaminophen"],
    "Ibuprofen (Advil)": ["Ibuprofen", "Potassium Salt"],
    "aspirin": ["Acetylsalicylic Acid"],
    "amoxicillin": ["Amoxicillin Trihydrate"],
    "Lisinopril": ["Lisinopril Dihydrate"],
    "amlodipine": ["Amlodipine Besylate"],
    "metoprolol": ["Metoprolol Tartrate"],
    "omeprazole": ["Omeprazole Magnesium"],
    "simvastatin": ["Simvastatin"],
    "prednisone": ["Prednisone"]
}

# Add this new dictionary at the top of your file with other constants
MEDICATION_SUCCESS_RATES = {
    "Acetaminophen (Tylenol)": 85,
    "aspirin": 82,
    "Ibuprofen (Advil)": 80,
    "amoxicillin": 88,
    "lisinopril": 75,
    "glipizide / metformin": 78,
    "amlodipine": 82,
    "metoprolol": 79,
    "ezetimibe / simvastatin": 77,
    "hydrochlorothiazide / losartan": 81,
    "omeprazole": 84,
    "Losartan": 76,
    "gabapentin": 73,
    "sertraline": 70,
    "levothyroxine": 85,
    "atorvastatin": 82,
    "escitalopram": 71,
    "fluoxetine": 69,
    "pantoprazole": 83,
    "prednisone": 75
}

def get_medication_price(med_name: str) -> float:
    """Retrieve medimeprication price from stored prices or external API."""
    return MEDICATION_PRICES.get(med_name, "Not Available")

def display_medication_details(medication: Dict):
    """Display primary medication details including price."""
    st.markdown("### Primary Medication Information")
    # Use medication parameter instead of undefined med
    st.markdown(f"**Price:** ${MEDICATION_PRICES.get(medication['name'], 'Not Available')}")
    st.markdown(f"**Name:** {medication['name']}")
    st.markdown(f"**Condition:** {medication['condition']}")
    st.markdown(f"**Form:** {medication['form']}")
    
    st.markdown("#### Active Ingredients")
    # Use medication parameter instead of undefined med
    ingredients = MEDICATION_INGREDIENTS.get(medication['name'], ["Information not available"])
    for ingredient in ingredients:
        st.write(f"• {ingredient}")
    
    st.markdown("#### Active Ingredients")
    for ingredient in medication['active_ingredients']:
        st.write(f"• {ingredient}")

# Add this dictionary at the top of your file
COMMON_MEDICINE_NAMES = {
    "Acetaminophen (Tylenol)": "acetaminophen",
    "Ibuprofen (Advil)": "ibuprofen", 
    "Aspirin": "aspirin",
    "Naproxen (Aleve)": "naproxen",
    "Diphenhydramine (Benadryl)": "diphenhydramine"
}


def search_condition_medications(condition: str) -> List[str]:
   """Search for any medical condition using RxNav"""
   try:
       # First try to find the condition in RxNav
       url = f"https://rxnav.nlm.nih.gov/REST/Ndfrt/search?conceptName={condition}&kindName=DISEASE_KIND"
       response = requests.get(url)
      
       if response.status_code == 200:
           data = response.json()
           return data.get('groupConcepts', [])
       return []
   except Exception as e:
       print(f"Error searching condition: {e}")
       return []


def search_medications(query: str, condition: str = None) -> List[Dict]:
   """Search medications using official RxNav API with any condition filtering"""
   if len(query) < 2:
       return []
   try:
       # Use the official RxNav API endpoint for drug search
       url = f"https://rxnav.nlm.nih.gov/REST/drugs.json?name={query}"
       response = requests.get(url)
      
       if response.status_code == 200:
           data = response.json()
           results = []
          
           if 'drugGroup' in data and 'conceptGroup' in data['drugGroup']:
               for group in data['drugGroup']['conceptGroup']:
                   if 'conceptProperties' in group:
                       for prop in group['conceptProperties']:
                           rxcui = prop.get('rxcui')
                           if rxcui:
                               # Get additional details
                               details = get_drug_details(rxcui)
                              
                               # If condition is specified, check indications
                               if condition:
                                   # Check drug-condition relationship using RxNav's API
                                   indication_url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={rxcui}"
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
          
           # If condition is specified, filter results to show condition-related medications first
           if condition and results:
               results.sort(key=lambda x: x.get('condition_info', {}).get('matches', False), reverse=True)
          
           return results[:10]
       return []
   except Exception as e:
       print(f"Error in search: {e}")
       return []


def get_drug_details(rxcui: str) -> Dict:
   """Get detailed drug information using RxNav API"""
   try:
       # Use official RxNav API endpoints
       endpoints = {
           'properties': f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json",
           'ingredients': f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/related.json?tty=IN",
           'allrelated': f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/allrelated.json"
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
       print(f"Error getting drug details: {e}")
       return {}


def get_condition_medications(condition: str) -> List[str]:
   """Get common medications for a condition"""
   condition_medications = {
       'fever': ['acetaminophen', 'ibuprofen', 'aspirin'],
       'cold': ['pseudoephedrine', 'dextromethorphan', 'diphenhydramine'],
       'headache': ['ibuprofen', 'acetaminophen', 'naproxen'],
       'allergies': ['loratadine', 'cetirizine', 'fexofenadine'],
       'cough': ['dextromethorphan', 'guaifenesin', 'benzonatate'],
       'pain': ['ibuprofen', 'acetaminophen', 'naproxen'],
       'diabetes': ['metformin', 'glipizide', 'insulin'],
       'hypertension': ['lisinopril', 'amlodipine', 'hydrochlorothiazide'],
       # Add more conditions and their common medications
   }
   return condition_medications.get(condition, [])


def create_price_comparison_chart(alternatives: List[Dict]) -> go.Figure:
   """Create price comparison chart with real pricing data"""
   data = []
   for alt in alternatives:
       price_info = alt['price_info']
       data.append({
           'name': alt['name'],
           'average_price': price_info['average_price'],
           'lowest_price': price_info['lowest_price'],
           'highest_price': price_info['highest_price'],
           'is_generic': alt['is_generic']
       })
  
   df = pd.DataFrame(data)
  
   fig = go.Figure()
  
   # Add average price bars
   fig.add_trace(go.Bar(
       name='Average Price',
       x=df['name'],
       y=df['average_price'],
       marker_color=['green' if is_generic else 'blue' for is_generic in df['is_generic']]
   ))
  
   # Add price range
   fig.add_trace(go.Bar(
       name='Price Range',
       x=df['name'],
       y=df['highest_price'] - df['lowest_price'],
       base=df['lowest_price'],
       marker_color='rgba(0,0,0,0.1)'
   ))
  
   fig.update_layout(
       title='Medication Price Comparison',
       xaxis_title='Medication Name',
       yaxis_title='Price ($)',
       barmode='overlay',
       showlegend=True,
       height=400
   )
  
   return fig


def display_diet_recommendations(recommendations: Dict):
   """Display diet recommendations in an organized way"""
   col1, col2 = st.columns(2)
  
   with col1:
       st.markdown("### 🥗 Foods to Eat")
       for food in recommendations['foods_to_eat']:
           st.markdown(f"✅ {food}")
  
   with col2:
       st.markdown("### ⚠️ Foods to Avoid")
       for food in recommendations['foods_to_avoid']:
           st.markdown(f"❌ {food}")
  
   st.markdown("### 🕒 Timing Instructions")
   st.info(recommendations['meal_timing'])
  
   st.markdown("### 👩‍🍳 Recommended Recipes")
   for recipe in recommendations['recipes']:
       with st.expander(f"🍽️ {recipe['name']}"):
           st.write("**Ingredients:**", recipe['ingredients'])
           st.write("**Instructions:**", recipe['instructions'])


def display_price_details(price_info: Dict):
   st.markdown("### 💰 Pricing Information")
   col1, col2, col3 = st.columns(3)
  
   with col1:
       st.metric("Average Price", f"${price_info['average_price']:.2f}")
   with col2:
       st.metric("Lowest Price", f"${price_info['lowest_price']:.2f}")
   with col3:
       st.metric("Highest Price", f"${price_info['highest_price']:.2f}")
  
   st.markdown("#### Price Sources")
   for source in price_info['price_sources']:
       st.markdown(f"""
           <div class="stat-box">
               <p><strong>Pharmacy:</strong> {source['pharmacy']}</p>
               <p><strong>Price:</strong> ${source['price']:.2f}</p>
               <p><strong>Updated:</strong> {source.get('updated_at', 'N/A')}</p>
           </div>
       """, unsafe_allow_html=True)


def add_to_recent_searches(medication: str, condition: str = None, dosage: str = None):
    """Add a search to recent searches"""
    if 'recent_searches' not in st.session_state:
        st.session_state.recent_searches = []
        
    search = {
        'medication': medication,
        'condition': condition,
        'dosage': dosage,
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    # Add to the beginning of the list
    st.session_state.recent_searches.insert(0, search)
    
    # Keep only the last 10 searches
    st.session_state.recent_searches = st.session_state.recent_searches[:10]


def save_medication(medication: Dict):
   """Save medication to saved list"""
   if medication not in st.session_state.saved_medications:
       st.session_state.saved_medications.append(medication)
       # Rerun the app immediately after saving
       st.rerun()
   return False


def remove_saved_medication(medication: Dict):
   """Remove medication from saved list"""
   if medication in st.session_state.saved_medications:
       st.session_state.saved_medications.remove(medication)
       # Rerun the app immediately after removing
       st.rerun()
   return False


def get_medication_uses(rxcui: str) -> List[str]:
   """Get specific uses/conditions for a medication"""
   try:
       url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byRxcui.json?rxcui={rxcui}"
       response = requests.get(url)
       uses = []
       if response.status_code == 200:
           data = response.json()
           if 'rxclassMinConceptList' in data:
               for concept in data['rxclassMinConceptList']['rxclassMinConcept']:
                   if concept.get('classType') == 'DISEASE':
                       uses.append(concept.get('className'))
       return list(set(uses))  # Remove duplicates
   except Exception as e:
       print(f"Error getting medication uses: {e}")
       return []


def format_medication_details(result):
    """Extract only ingredients and type from medication details"""
    details = result.get('details', {})
    
    # Get ingredients
    ingredients = []
    if 'ingredients' in details:
        ingredient_group = details['ingredients'].get('relatedGroup', {}).get('conceptGroup', [])
        for group in ingredient_group:
            if group.get('tty') == 'IN':  # IN means ingredient
                for prop in group.get('conceptProperties', []):
                    ingredients.append(prop['name'])
    
    # Get type/form
    med_type = "Unknown"
    if 'allrelated' in details:
        for group in details['allrelated']['allRelatedGroup']['conceptGroup']:
            if group.get('tty') == 'DF':  # DF means dosage form
                if group.get('conceptProperties'):
                    med_type = group['conceptProperties'][0]['name']
                break
    
    return {
        'name': result.get('name', ''),
        'ingredients': ingredients,
        'type': med_type
    }


def set_page_style():
   """Set custom page styling for a spacious healthcare theme"""
   st.markdown("""
       <style>
       /* Modern, spacious main layout */
       .stApp {
           background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
           padding: 1rem;
       }
      
       /* Elegant header with gradient */
       .main-header {
           background: linear-gradient(120deg, #1a5f7a, #2c88b0);
           color: white;
           padding: 2rem 3rem;
           border-radius: 20px;
           margin: 1rem 0 3rem 0;
           box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
       }
      
       .main-header h1 {
           font-size: 2.5rem;
           margin-bottom: 1rem;
           font-weight: 600;
       }
      
       .main-header p {
           font-size: 1.2rem;
           opacity: 0.9;
       }
      
       /* Spacious search section */
       .search-section {
           background: white;
           padding: 2rem;
           border-radius: 15px;
           box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
           margin-bottom: 2rem;
       }
      
       /* Enhanced input fields */
       .stTextInput > div > div > input {
           font-size: 1.1rem;
           padding: 1rem 1.5rem;
           border-radius: 10px;
           border: 2px solid #e1e8f0;
           transition: all 0.3s ease;
       }
      
       .stTextInput > div > div > input:focus {
           border-color: #2c88b0;
           box-shadow: 0 0 0 2px rgba(44, 136, 176, 0.2);
       }
      
       /* Modern card design */
       .medication-card {
           background: white;
           padding: 2rem;
           border-radius: 15px;
           box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
           margin: 1.5rem 0;
           border-left: 5px solid #2c88b0;
       }
      
       /* Elegant section headers */
       .section-header {
           color: #1a5f7a;
           font-size: 1.5rem;
           margin: 2rem 0 1rem 0;
           padding-bottom: 0.5rem;
           border-bottom: 3px solid #2c88b0;
       }
      
       /* Info boxes with more space */
       .info-box {
           background: white;
           padding: 1.5rem 2rem;
           border-radius: 12px;
           margin: 1rem 0;
           box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
       }
      
       /* Enhanced buttons */
       .stButton > button {
           padding: 0.8rem 1.8rem;
           font-size: 1rem;
           font-weight: 500;
           border-radius: 10px;
           background: #2c88b0;
           color: white;
           border: none;
           transition: all 0.3s ease;
       }
      
       .stButton > button:hover {
           background: #1a5f7a;
           transform: translateY(-2px);
           box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
       }
      
       /* Sidebar enhancements */
       .css-1d391kg {
           background-color: white;
           padding: 2rem 1rem;
       }
      
       /* Status indicators */
       .status-pill {
           display: inline-block;
           padding: 0.5rem 1rem;
           border-radius: 20px;
           font-weight: 500;
           margin: 0.5rem 0;
       }
      
       .status-success {
           background: #e6f7ed;
           color: #1a7f4b;
       }
      
       .status-info {
           background: #e6f3f7;
           color: #1a5f7a;
       }
      
       /* Medical icons with spacing */
       .medical-icon {
           font-size: 1.4rem;
           margin-right: 0.8rem;
           color: #2c88b0;
       }
      
       /* Responsive adjustments */
       @media (max-width: 768px) {
           .main-header {
               padding: 1.5rem;
           }
          
           .main-header h1 {
               font-size: 2rem;
           }
          
           .medication-card {
               padding: 1.5rem;
           }
       }
       </style>
   """, unsafe_allow_html=True)


def get_medication_suggestions(search_query: str) -> List[str]:
    """Get medication suggestions based on user input"""
    # Sample medication list - in production, this would come from your API/database
    common_medications = [
        "Acetaminophen (Tylenol)",
        "Ibuprofen (Advil)",
        "Aspirin",
        "Amoxicillin",
        "Lisinopril",
        "Metformin",
        "Amlodipine",
        "Metoprolol",
        "Omeprazole",
        "Simvastatin",
        "Losartan",
        "Gabapentin",
        "Sertraline",
        "Levothyroxine",
        "Atorvastatin",
        "Escitalopram",
        "Fluoxetine",
        "Pantoprazole",
        "Hydrochlorothiazide",
        "Prednisone"
    ]
    
    if not search_query:
        return common_medications
    
    # Filter medications that match the search query (case-insensitive)
    return [med for med in common_medications if search_query.lower() in med.lower()]


def clear_recent_searches():
    """Clear all recent searches"""
    st.session_state.recent_searches = []
    st.rerun()


def main():
   # Set wide mode by default
   st.set_page_config(
       page_title="MediMeal",
       page_icon="💊",
       layout="wide",
       initial_sidebar_state="auto"
   )


   # Hide the settings menu with custom CSS
   st.markdown("""
       <style>
       #MainMenu {visibility: hidden;}
       </style>
   """, unsafe_allow_html=True)
  
   # Add custom CSS to style the buttons
   st.markdown("""
       <style>
       /* Make the Clear All buttons smaller */
       .stButton button[kind="secondary"] {
           padding: 0.2rem 0.5rem;
           font-size: 0.7rem;
       }
       
       /* Make the trash emoji buttons smaller */
       .stButton button {
           padding: 0rem 0.5rem;
           font-size: 0.7rem;
           line-height: 1;
       }
       </style>
   """, unsafe_allow_html=True)
  
   # Add custom CSS for styling
   st.markdown("""
       <style>
       /* Existing styles ... */

       /* Clear All button styling */
       button[kind="secondary"] {
           background-color: #ff4b4b !important;
           color: white !important;
           border: none !important;
           padding: 2px 8px !important;
           font-size: 12px !important;
           border-radius: 4px !important;
           height: auto !important;
           min-height: 0 !important;
           line-height: normal !important;
           width: auto !important;
       }

       button[kind="secondary"]:hover {
           background-color: #ff3333 !important;
           border: none !important;
       }

       /* Analyze button style - extended width and centered */
       div[data-testid="stButton"] > button:first-child {
           background-color: #ff4b4b !important;
           color: white !important;
           border: none !important;
           padding: 0.5rem 1rem !important;
           font-size: 1rem !important;
           border-radius: 4px !important;
           width: 100% !important;
           margin: 1rem 0 !important;
           display: flex !important;
           justify-content: center !important;
           align-items: center !important;
       }

       div[data-testid="stButton"] > button:hover {
           background-color: #ff3333 !important;
           border: none !important;
       }

       /* Container for the analyze button */
       .analyze-container {
           padding: 0 !important;
           margin: 0 !important;
       }
       </style>
   """, unsafe_allow_html=True)
  
   # Add custom CSS for modern dashboard styling
   st.markdown("""
       <style>
       /* Logo container styling for single line */
       .logo-container {
           display: flex;
           align-items: center;
           padding: 10px 0;
           white-space: nowrap;
       }
       
       .logo-plate {
           position: relative;
           width: 45px;
           height: 45px;
           background: white;
           border-radius: 50%;
           box-shadow: 0 2px 4px rgba(0,0,0,0.1);
           display: inline-flex;
           align-items: center;
           justify-content: center;
           border: 2px solid #f0f0f0;
           margin-right: 12px;
           vertical-align: middle;
       }
       
       .logo-text {
           font-size: 24px;
           font-weight: 600;
           color: #2c3e50;
           display: inline-block;
           vertical-align: middle;
       }
       
       /* Sidebar card styling */
       .sidebar-card {
           background: white;
           border-radius: 10px;
           padding: 15px;
           margin: 10px 0;
           box-shadow: 0 2px 4px rgba(0,0,0,0.05);
           transition: transform 0.2s, box-shadow 0.2s;
       }
       
       .sidebar-card:hover {
           transform: translateY(-2px);
           box-shadow: 0 4px 8px rgba(0,0,0,0.1);
       }
       
       .card-icon {
           font-size: 24px;
           margin-bottom: 10px;
           color: #2c88b0;
       }
       
       .card-title {
           font-size: 16px;
           font-weight: 600;
           color: #2c3e50;
           margin-bottom: 8px;
       }
       
       .card-description {
           font-size: 14px;
           color: #6c757d;
           line-height: 1.4;
       }
       
       /* Divider styling */
       .custom-divider {
           margin: 20px 0;
           border-top: 1px solid #eee;
       }
       </style>
   """, unsafe_allow_html=True)
  
   # Display header with plate-style logo
   st.markdown("""
       <h1>
           <div class="logo-plate">
               <span class="hospital-icon">🏥</span>
           </div>
           MediMeal
       </h1>
       <h2>Smart Prescription & Nutrition Advisor</h2>
   """, unsafe_allow_html=True)
  
   # Sidebar with feature cards only
   with st.sidebar:
       
       st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

       # Logo and title
       st.markdown("""
           <div class="logo-container">
               <div class="logo-plate">
                   <span class="hospital-icon">🏥</span>
               </div>
               <span class="logo-text">MediMeal</span>
           </div>
           
           <div class="custom-divider"></div>
            
           
           <!-- Feature Cards -->
           <div class="sidebar-card">
               <div class="card-icon">💊</div>
               <div class="card-title">Medication Analysis</div>
               <div class="card-description">
                   Offers an detailed interactive interface to learn more about your medication.
               </div>
           </div>
           
           <div class="sidebar-card">
               <div class="card-icon">🍽️</div>
               <div class="card-title">Nutrition Recommendations</div>
               <div class="card-description">
                   Gives you an overview of what foods to eat and avoid while taking the medication.
               </div>
           </div>
           
           <div class="sidebar-card">
               <div class="card-icon">📊</div>
               <div class="card-title">Health Tracking</div>
               <div class="card-description">
                   Creates a graph that visualizes the success rate of the medication.
               </div>
           </div>
       """, unsafe_allow_html=True)
       
       st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)

       # Recent Searches section
       col1, col2 = st.columns([3, 1])
       with col1:
           st.markdown("#### 📜 Recent Searches")
       with col2:
           if st.button("🗑️", key="clear_recent", help="Clear all recent searches"):
            clear_recent_searches()
    
       if st.session_state.recent_searches:
           for idx, search in enumerate(st.session_state.recent_searches):
            # Create a clickable button with custom styling
            button_label = (
                f"{search['medication']}\n"
                f"Condition: {search.get('condition', 'Not specified')}\n"
                f"Dosage: {search.get('dosage', 'Not specified')}"
            )
            if st.button(
                button_label,
                key=f"recent_search_{idx}",
                help="Click to analyze this medication",
                use_container_width=True
            ):
                st.session_state.med_select = search['medication']
                st.rerun()
                st.session_state.med_select = search['medication']
                st.rerun()
            
            # Add timestamp with better styling
            st.markdown(
                f"""
                <div style='font-size: 0.8em; color: #666; margin-bottom: 8px; padding-left: 4px;'>
                    {search['timestamp']}
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Add a subtle divider between entries
            if idx < len(st.session_state.recent_searches) - 1:
                st.markdown("<hr style='margin: 5px 0; opacity: 0.2;'>", unsafe_allow_html=True)
       else:
           st.markdown("*No recent searches*")
      

   # Main content area
   
   # Search section
   st.markdown("###  Search Medications")
   
   # Input fields
   selected_medication = st.selectbox(
       "Search for medications",
       options=get_medication_suggestions(""),
       placeholder="Start typing to search medications...",
       key="med_select",
       label_visibility="collapsed"
    )
   
   condition = st.text_input(
       "Medical Condition (Optional)",
       placeholder="Medical Condition (Optional)",
       key="condition_search",
       label_visibility="collapsed"
   )
   
   dosage = st.text_input(
       "Dosage (Optional)",
       placeholder="Dosage (Optional)",
       key="dosage_input",
       label_visibility="collapsed"
   )
   
   # Add spacing before button
   st.write("")
   
   # Full-width container for analyze button
   analyze_button = st.button(" Analyze Medication", use_container_width=True)


   # Main content area
   if selected_medication and analyze_button:
       # Add this line before the spinner
       add_to_recent_searches(selected_medication, condition, dosage)
    
       with st.spinner('Analyzing medication...'):
           try:
               # Create mock results instead of waiting for API
            results = [{
                'name': selected_medication,
                'condition': condition if condition and condition.strip() else 'Not specified',  # Fix condition handling
                'form': 'Tablet',
                'side_effects': [
                    "Consult your healthcare provider for complete list of side effects",
                    "May cause drowsiness",
                    "Nausea or stomach upset",
                    "Headache",
                    "Dizziness"
                ],
                'warnings': [
                    "Do not exceed recommended dose",
                    "Store in a cool, dry place",
                    "Keep out of reach of children",
                    "Do not use if allergic to ingredients"
                ],
                'guidelines': [
                    "Take as prescribed by your healthcare provider",
                    "Take with food unless otherwise directed",
                    "Do not crush or chew if tablets are coated",
                    "Complete full course if antibiotic"
                ],
                'storage': [
                    "Store at room temperature",
                    "Protect from light and moisture",
                    "Keep container tightly closed",
                    "Do not store in bathroom"
                ],
                'interactions': [
                    "Discuss all medications with your healthcare provider",
                    "Avoid alcohol while taking this medication",
                    "Check for drug-drug interactions",
                    "Inform healthcare provider of supplements"
                ]
            }]

            # Create tabs using the mock results
            if results:
                med = results[0]
                # Create tabs for different sections
                primary_tab, similar_tab, effects_tab, details_tab, food_tab, avoid_med_tab, success_rate_tab = st.tabs([
                    "💊 Primary Details",
                    "🔄 Similar Medications",
                    "⚠️ Side Effects",
                    "📋 Additional Details",
                    "🍽️ Food Suggestions",  # New food suggestions tab
                    "🚫 Avoid Medications",  # New avoid medications tab
                    "📊 Success Rate"  # New tab
                ])
                       
                       # Primary Details Tab
                with primary_tab:
                    med = results[0]
                    st.markdown("### Primary Medication Information")
                    st.markdown(f"**Name:** {med['name']}")
                    
                    # Fix price display by normalizing the medication name
                    normalized_name = med['name'].split('(')[0].strip().lower()
                    price = None
                    for med_name, med_price in MEDICATION_PRICES.items():
                        if med_name.lower().strip() in normalized_name or normalized_name in med_name.lower().strip():
                            price = med_price
                            break
                    
                    if price:
                        st.markdown(f"**Price:** ${price:.2f}")
                    else:
                        st.markdown("**Price:** Not available")
                    
                    # Update condition display
                    if condition and condition.strip():
                         st.markdown(f"**Condition:** {condition}")
                    else:
                         st.markdown("**Condition:** Not specified")
                        
                    if dosage:
                        st.markdown(f"**Dosage:** {dosage}")
                    st.markdown(f"**Form:** {med['form']}")
                    
                    # Single Active Ingredients section
                    st.markdown("#### Active Ingredients")
                    ingredients = None
                    for med_name in MEDICATION_INGREDIENTS:
                        if (normalized_name in med_name.lower() or 
                            med_name.lower() in normalized_name):
                            ingredients = MEDICATION_INGREDIENTS[med_name]
                            break
                    
                    if ingredients:
                        for ingredient in ingredients:
                            st.write(f"• {ingredient}")
                    else:
                        st.write("• Active ingredients information not available")
                       
                       # Similar Medications Tab
                with similar_tab:
                           st.markdown("### Similar Medications")
                           alternatives_response = requests.get(f"{API_URL}/medications/{selected_medication}/alternatives")
                           if alternatives_response.status_code == 200:
                               alternatives = alternatives_response.json()
                               for alt in alternatives:
                                   st.markdown(f"**{alt['name']}**")
                                   st.markdown(f"Form: {alt['form']}")
                                   st.divider()
                       
                       # Side Effects Tab
                with effects_tab:
                           st.markdown("### Side Effects & Warnings")
                           col1, col2 = st.columns(2)
                           with col1:
                               st.markdown("#### Side Effects")
                               for effect in med['side_effects']:
                                   st.write(f"• {effect}")
                           with col2:
                               st.markdown("#### Warnings")
                               for warning in med['warnings']:
                                   st.write(f"• {warning}")
                       
                       # Additional Details Tab
                with details_tab:
                           st.markdown("### Additional Information")
                           
                           st.markdown("#### 📝 Usage Guidelines")
                           for guideline in med['guidelines']:
                               st.write(f"• {guideline}")
                           
                           st.markdown("#### 🏠 Storage")
                           for storage in med['storage']:
                               st.write(f"• {storage}")
                           
                           st.markdown("#### ⚡ Drug Interactions")
                           for interaction in med['interactions']:
                               st.write(f"• {interaction}")
                       # food suggestions tab
                with food_tab:
                           st.markdown("### Food Recommendations")
                           col1, col2 = st.columns(2)

                           with col1:
                            st.markdown("#### ✅ Foods to Include")
                            recommended_foods = {
                                "Acetaminophen (Tylenol)": ["Water-rich foods", "Light, easily digestible foods"], "Aspirin": ["Foods rich in vitamin K", "Green leafy vegetables", "Yogurt", "Bananas", 
                "Oatmeal", "Rice", "Low-acid fruits", "Whole grain bread"], "Ibuprofen (Advil)": ["Yogurt", "Bananas", "Rice"],
                                "Amoxicillin": ["Probiotic-rich foods", "Yogurt", "Fermented foods"],
                                "Lisinopril": ["Low-sodium foods", "Fruits", "Vegetables"],
                                "Metformin": ["High-fiber foods", "Lean proteins", "Green vegetables"],
                                 "Amlodipine": ["Low-sodium foods", "Potassium-rich foods (bananas, sweet potatoes)","Magnesium-rich foods (leafy greens, nuts)","Fresh fruits and vegetables", "Lean proteins","Whole grains", "Fish rich in omega-3", "Low-fat dairy products"],
                                 "Metoprolol": [
        "Low-sodium foods",
        "Potassium-rich foods (bananas, sweet potatoes, spinach)",
        "Magnesium-rich foods (nuts, seeds, leafy greens)",
        "Fresh fruits and vegetables",
        "Whole grains",
        "Lean proteins",
        "Fish rich in omega-3",
        "Low-fat dairy products"
    ], "Simvastatin": [
        "Heart-healthy foods",
        "High-fiber foods (oats, whole grains)",
        "Fatty fish rich in omega-3 (salmon, mackerel)",
        "Nuts and seeds",
        "Olive oil and other healthy oils",
        "Fresh fruits and vegetables",
        "Lean proteins",
        "Plant-based proteins (legumes, beans)",
        "Low-fat dairy products"
    ], "Hydrochlorothiazide": [
        "Low-sodium foods",
        "Foods rich in potassium (sweet potatoes, bananas)",
        "Foods high in magnesium (leafy greens, nuts)",
        "Fresh fruits and vegetables",
        "Lean proteins (chicken, fish)",
        "Whole grains",
        "Berries",
        "Low-fat dairy products",
        "Foods rich in fiber"
    ],
                                "Omeprazole": ["Non-acidic fruits", "Lean proteins", "Whole grains"],"Losartan": ["Low-sodium foods", "Bananas", "Leafy greens", "Sweet potatoes", "Greek yogurt"],
                                "Gabapentin": ["High-protein foods", "Complex carbohydrates", "Fiber-rich foods", "Leafy vegetables"],
                                "Sertraline": ["Foods rich in B-vitamins", "Whole grains", "Lean proteins", "Omega-3 rich foods"],
                                "Levothyroxine": ["Iodine-rich foods", "Selenium-rich foods", "Brazil nuts", "Fish", "Eggs"],
                                "Atorvastatin": ["Heart-healthy foods", "Oatmeal", "Fatty fish", "Nuts", "Olive oil"],
                                "Escitalopram": ["Foods rich in B12", "Leafy greens", "Whole grains", "Lean proteins", "Berries"],
                                "Fluoxetine": ["Complex carbohydrates", "Protein-rich foods", "Fresh fruits", "Vegetables"],
                                "Pantoprazole": ["Non-acidic fruits", "Low-fat proteins", "Cooked vegetables", "Whole grains"],
                                "Hydrochlorothiazide": ["Potassium-rich foods", "Bananas", "Sweet potatoes", "Yogurt", "Leafy greens"],
                                "Prednisone": ["Calcium-rich foods", "Vitamin D foods", "Lean proteins", "Low-sodium foods"]
                            }

                            normalized_name = med['name'].split('(')[0].strip()
                            foods_to_include = None
                            for med_name in recommended_foods:
                                if med_name.lower().strip() in normalized_name or normalized_name in med_name.strip():
                                    foods_to_include = recommended_foods[med_name]
                                    break
        
                            if foods_to_include:
                                for food in foods_to_include:
                                    st.write(f"• {food}")
                                else:
                                    st.write("• Food recommendations not available")


                with col2:
                           st.markdown("#### ❌ Foods to Avoid")
                           avoid_foods = {"Acetaminophen (Tylenol)": ["Alcohol", "Excessive caffeine"],"aspirin": ["Spicy foods", "Citrus fruits", "Tomatoes", "Coffee", "Tea", 
                "Carbonated drinks", "Alcohol", "Vinegar-based foods", "High-acid foods"],
                                        "Ibuprofen (Advil)": ["Spicy foods", "Acidic foods", "Alcohol"],
                                        "Amoxicillin": ["Alcohol", "High-sugar foods"],
                                        "Lisinopril": ["High-salt foods", "Alcohol", "Potassium supplements"],
                                        "Metformin": ["Excessive carbohydrates", "Alcohol", "High-sugar foods"],
                                        "Amlodipine": ["High-sodium foods",
                   "Grapefruit and grapefruit juice",
                   "Excessive alcohol",
                   "High-fat foods",
                   "Foods high in saturated fats",
                   "Processed foods",
                   "Excessive caffeine",
                   "Large amounts of black licorice"],
                                            "Metoprolol": [
        "High-sodium foods",
        "Excessive caffeine",
        "Alcohol",
        "Foods high in tyramine (aged cheeses, cured meats)",
        "Large amounts of licorice",
        "Foods high in saturated fats",
        "Processed foods with high sodium content",
        "Energy drinks"
    ], "Simvastatin": [
        "Heart-healthy foods",
        "High-fiber foods (oats, whole grains)",
        "Fatty fish rich in omega-3 (salmon, mackerel)",
        "Nuts and seeds",
        "Olive oil and other healthy oils",
        "Fresh fruits and vegetables",
        "Lean proteins",
        "Plant-based proteins (legumes, beans)",
        "Low-fat dairy products"
    ],"Hydrochlorothiazide": [
        "High-sodium foods",
        "Salt substitutes (high in potassium)",
        "Excessive potassium supplements",
        "Alcohol",
        "Licorice",
        "Processed foods",
        "Foods high in saturated fats",
        "Caffeine in large amounts",
        "Grapefruit and grapefruit juice"
    ],
                                        "Omeprazole": ["Spicy foods", "Citrus fruits", "Tomato-based foods"], "Losartan": ["High-sodium foods", "Salt substitutes", "Excessive potassium supplements"],
                                        "gabapentin": ["Alcohol", "Caffeine", "High-fat foods"],
                                        "sertraline": ["Alcohol", "Grapefruit", "High-tyramine foods", "Aged cheeses"],
                                        "levothyroxine": ["Soy products", "High-fiber foods", "Coffee", "Walnuts", "Iron-rich foods"],
                                        "Atorvastatin": ["Grapefruit", "Excessive alcohol", "High-fat foods"],
                                        "escitalopram": ["Alcohol", "Grapefruit", "Caffeine", "High-tyramine foods"],
                                        "fluoxetine": ["Alcohol", "Grapefruit", "Excessive caffeine", "High-tyramine foods"],
                                        "pantoprazole": ["Spicy foods", "Citrus fruits", "Tomatoes", "Coffee", "Alcohol"],
                                        "Hydrochlorothiazide": ["High-sodium foods", "Alcohol", "Licorice"],
                                        "prednisone": ["High-sodium foods", "High-sugar foods", "Alcohol", "Caffeine"]
                           }
        
                           normalized_name = med['name'].split('(')[0].strip().lower()
                           foods_to_avoid = None
                           for med_name in avoid_foods:
                                if (med_name.lower().strip() in normalized_name or 
                                    normalized_name in med_name.lower().strip()):
                                    foods_to_avoid = avoid_foods[med_name]
                                    break
                                
                           if foods_to_avoid:
                                for food in foods_to_avoid:
                                    st.write(f"• {food}")
                           else:
                                st.write("• Foods to avoid information not available")

                        # Add this after the food_tab section
                with avoid_med_tab:
                           st.markdown("### ⛔ Medications to Avoid")
                           medications_to_avoid = {
                            "Acetaminophen (Tylenol)": [
                                "Other acetaminophen-containing products",
                                "High doses of NSAIDs",
                                "Certain antibiotics",
                                "Warfarin",
                                "Alcohol-containing medications"
                            ],
                            "Aspirin": [
                                "Other NSAIDs (ibuprofen, naproxen)",
                                "Blood thinners (warfarin)",
                                "High blood pressure medications",
                                "Methotrexate"
                            ],
                            "Ibuprofen (Advil)": [
                                "Other NSAIDs (ibuprofen, naproxen)",
                                "Aspirin",
                                "Blood thinners",
                                "High blood pressure medications",
                                "Medications that can irritate the stomach"
                            ],
                            "Metformin": [
                                "High doses of corticosteroids",
                                "Thiazide diuretics",
                                "Beta blockers",
                                "Calcium channel blockers",
                                "Medications that affect blood sugar"
                            ],
                            "Omeprazole": [
                                "Atazanavir",
                                "Nelfinavir",
                                "Cilostazol",
                                "Clopidogrel",
                                "Iron supplements (timing separation needed)",
                                "Certain antifungal medications"
                            ],
                            "Hydrochlorothiazide": [
                                "Other potassium-sparing diuretics",
                                "ACE inhibitors",
                                "ARBs",
                                "Lithium",
                                "NSAIDs",
                                "Potassium supplements"
                            ],
                            "Amoxicillin": [
                                "Probenecid",
                                "Allopurinol",
                                "Oral contraceptives",
                                "Other antibiotics (tetracyclines)"
                            ],
                            "Lisinopril": [
                                "Potassium supplements",
                                "Other ACE inhibitors",
                                "NSAIDs",
                                "Lithium"
                            ],
                            "Metoprolol": [
                                "Other beta blockers",
                                "Calcium channel blockers",
                                "Antiarrhythmic medications",
                                "MAO inhibitors"
                            ],
                            "Amlodipine": [
                                "Simvastatin (high doses)",
                                "Other calcium channel blockers",
                                "Beta blockers",
                                "CYP3A4 inhibitors"
                            ],
                            "Simvastatin": [
                                "Other statins",
                                "Fibrates",
                                "Cyclosporine",
                                "Strong CYP3A4 inhibitors"
                            ],
                            "Hydrochlorothiazide": [
                                "Other ARBs",
                                "ACE inhibitors",
                                "Potassium-sparing diuretics",
                                "Lithium",
                                "NSAIDs"
                            ],
                            "Gabapentin": [
                                "Opioids",
                                "Other CNS depressants",
                                "Antacids (timing separation needed)",
                                "Morphine"
                            ],
                            "Sertraline": [
                                "Other SSRIs",
                                "MAO inhibitors",
                                "Pimozide",
                                "NSAIDs",
                                "Warfarin"
                            ],
                            "Levothyroxine": [
                                "Calcium supplements",
                                "Iron supplements",
                                "Antacids",
                                "Cholesterol-lowering drugs",
                                "Anticoagulants"
                            ],
                            "Atorvastatin": [
                                "Other statins",
                                "Fibrates",
                                "Cyclosporine",
                                "Strong CYP3A4 inhibitors"
                            ],
                            "Escitalopram": [
                                "Other SSRIs",
                                "MAO inhibitors",
                                "Pimozide",
                                "NSAIDs",
                                "Aspirin"
                            ],
                            "Fluoxetine": [
                                "Other SSRIs",
                                "MAO inhibitors",
                                "Thioridazine",
                                "NSAIDs",
                                "Lithium"
                            ],
                            "Pantoprazole": [
                                "Atazanavir",
                                "Nelfinavir",
                                "Erlotinib",
                                "Methotrexate",
                                "Clopidogrel"
                            ],
                            "Prednisone": [
                                "Live vaccines",
                                "NSAIDs",
                                "Anticoagulants",
                                "Diabetes medications",
                                "Certain antibiotics"
                            ],
                            "Losartan": [
                                "Low-sodium foods",
                                "Bananas",
                                "Leafy greens",
                                "Sweet potatoes",
                                "Greek yogurt",
                                "Fresh fruits and vegetables",
                                "Whole grains",
                                "Lean proteins"
                            ],
                            "Gabapentin": [
                                "High-protein foods",
                                "Complex carbohydrates",
                                "Fiber-rich foods",
                                "Leafy vegetables",
                                "B-vitamin rich foods",
                                "Magnesium-rich foods"
                            ],
                            "Sertraline": [
                                "Foods rich in B-vitamins",
                                "Whole grains",
                                "Lean proteins",
                                "Omega-3 rich foods",
                                "Fresh fruits and vegetables",
                                "Probiotic-rich foods"
                            ],
                            "Levothyroxine": [
                                "Iodine-rich foods",
                                "Selenium-rich foods",
                                "Brazil nuts",
                                "Fish",
                                "Eggs",
                                "Fresh fruits and vegetables"
                            ],
                            "atorvastatin": [
                                "Heart-healthy foods",
                                "Oatmeal",
                                "Fatty fish",
                                "Nuts",
                                "Olive oil",
                                "High-fiber foods",
                                "Plant-based proteins"
                            ],
                            "escitalopram": [
                                "Foods rich in B12",
                                "Leafy greens",
                                "Whole grains",
                                "Lean proteins",
                                "Berries",
                                "Omega-3 rich foods"
                            ],
                            "fluoxetine": [
                                "Complex carbohydrates",
                                "Protein-rich foods",
                                "Fresh fruits",
                                "Vegetables",
                                "Omega-3 rich foods",
                                "Whole grains"
                            ],
                            "pantoprazole": [
                                "Non-acidic fruits",
                                "Low-fat proteins",
                                "Cooked vegetables",
                                "Whole grains",
                                "Yogurt",
                                "Lean meats"
                            ],
                            "Hydrochlorothiazide": [
                                "Potassium-rich foods",
                                "Magnesium-rich foods",
                                "Calcium-rich foods",
                                "Fresh fruits and vegetables",
                                "Lean proteins",
                                "Low-sodium foods"
                            ],
                            "prednisone": [
                                "Calcium-rich foods",
                                "Vitamin D foods",
                                "Lean proteins",
                                "Low-sodium foods",
                                "Potassium-rich foods",
                                "Anti-inflammatory foods"
                            ]
                           }

                           meds_to_avoid = medications_to_avoid.get(med['name'], ["Information not available"])
    
                           col1, col2 = st.columns(2)
    
                           with col1:
                               st.markdown("#### 🚫 Contraindicated Medications")
                               for medication in meds_to_avoid:
                                   st.write(f"• {medication}")
    
                           with col2:
                               st.markdown("#### ⚠️ General Precautions")
                               st.markdown("""
                                * Always consult your healthcare provider before starting or stopping any medication
                                * Inform all healthcare providers about your current medications
                                * Keep a current list of all your medications
                                * Check for interactions when starting new medications
                                * Follow prescribed dosing schedules carefully
                                """)    
                               
                with success_rate_tab:
                    st.markdown("### 📊 Treatment Success Rate")
                    normalized_name = med['name'].split('(')[0].strip().lower()
                    success_rate = None

                    for med_name, rate in MEDICATION_SUCCESS_RATES.items():
                        if med_name.lower().strip() in normalized_name or normalized_name in med_name.lower().strip():
                            success_rate = rate
                            break
                    
                    if not success_rate:
                        success_rate = "value not found"
        
                    # Create the gauge chart
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=success_rate,
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Success Rate (%)", 'font': {'size': 24}},
                        gauge={
                            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                            'bar': {'color': "darkblue"},
                            'bgcolor': "white",
                            'borderwidth': 2,
                            'bordercolor': "gray",
                            'steps': [
                                {'range': [0, 50], 'color': 'red'},
                                {'range': [50, 75], 'color': 'yellow'},
                                {'range': [75, 100], 'color': 'green'}
                            ],
                            'threshold': {
                                'line': {'color': "red", 'width': 4},
                                'thickness': 0.75,
                                'value': 70
                            }
                        }
                    ))

                    # Update layout
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        height=400,
                        margin=dict(l=10, r=10, t=40, b=10)
                    )
        
                    # Display the chart
                    st.plotly_chart(fig, use_container_width=True)
    
                        # Add contextual information
                    if success_rate >= 80:
                                st.success(f"This medication has a high success rate of {success_rate}%")
                    elif success_rate >= 70:
                                st.info(f"This medication has a moderate success rate of {success_rate}%")
                    else:
                                st.warning(f"This medication has a lower success rate of {success_rate}%")
        
                        # Add additional context
                    st.markdown("""
                            #### Understanding Success Rates
                            * **High (80-100%)**: Excellent therapeutic outcomes in most patients
                            * **Moderate (70-79%)**: Good effectiveness for most patients
                            * **Lower (<70%)**: May require careful monitoring or dose adjustments
                            
                            _Note: Success rates are based on clinical studies and real-world data. Individual results may vary._
                            """)


            else:
                   st.error("Error connecting to the medication service")
           except Exception as e:
               st.error(f"Error: {str(e)}")


if __name__ == "__main__":
   # Initialize session state
   if 'saved_medications' not in st.session_state:
       st.session_state.saved_medications = []
   if 'recent_searches' not in st.session_state:
       st.session_state.recent_searches = []
  
   main()