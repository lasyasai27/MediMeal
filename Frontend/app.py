import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
from datetime import datetime


# Constants
API_URL = "http://127.0.0.1:3000"  # Changed from 8001 to 8000
RXNORM_API = "https://rxnav.nlm.nih.gov/REST"


# Initialize session state
if 'saved_medications' not in st.session_state:
   st.session_state.saved_medications = []
if 'recent_searches' not in st.session_state:
   st.session_state.recent_searches = []


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
   return condition_medications.get(condition.lower(), [])


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
                   Analyze your medications for interactions and get personalized insights
               </div>
           </div>
           
           <div class="sidebar-card">
               <div class="card-icon">🍽️</div>
               <div class="card-title">Nutrition Recommendations</div>
               <div class="card-description">
                   Get dietary suggestions based on your medications and health conditions
               </div>
           </div>
           
           <div class="sidebar-card">
               <div class="card-icon">📊</div>
               <div class="card-title">Health Tracking</div>
               <div class="card-description">
                   Monitor your medication schedule and health metrics in one place
               </div>
           </div>
       """, unsafe_allow_html=True)
       
       st.markdown("<div class='custom-divider'></div>", unsafe_allow_html=True)
       

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
       with st.spinner('Analyzing medication...'):
           try:
               response = requests.get(f"{API_URL}/search/medications", params={
                   "query": selected_medication,
                   "condition": condition
               })
               
               if response.status_code == 200:
                   results = response.json()
                   if results:
                       # Create tabs for different sections
                       primary_tab, similar_tab, effects_tab, details_tab = st.tabs([
                           "💊 Primary Details",
                           "🔄 Similar Medications",
                           "⚠️ Side Effects",
                           "📋 Additional Details"
                       ])
                       
                       # Primary Details Tab
                       with primary_tab:
                           med = results[0]
                           st.markdown("### Primary Medication Information")
                           st.markdown(f"**Name:** {med['name']}")
                           st.markdown(f"**Condition:** {med['condition']}")
                           if dosage:
                               st.markdown(f"**Dosage:** {dosage}")
                           st.markdown(f"**Form:** {med['form']}")
                           
                           st.markdown("#### Active Ingredients")
                           for ingredient in med['active_ingredients']:
                               st.write(f"• {ingredient}")
                       
                       # Similar Medications Tab
                       with similar_tab:
                           st.markdown("### Similar Medications")
                           alternatives_response = requests.get(f"{API_URL}/medications/{selected_medication}/alternatives")
                           if alternatives_response.status_code == 200:
                               alternatives = alternatives_response.json()
                               for alt in alternatives:
                                   st.markdown(f"**{alt['name']}**")
                                   st.markdown(f"Form: {alt['form']}")
                                   st.markdown("Active Ingredients:")
                                   for ing in alt['active_ingredients']:
                                       st.write(f"• {ing}")
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