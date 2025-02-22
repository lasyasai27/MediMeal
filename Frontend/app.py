import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
from datetime import datetime


# Constants
API_URL = "http://localhost:8000"
RXNORM_API = "https://rxnav.nlm.nih.gov/REST"


# Initialize session state
if 'saved_medications' not in st.session_state:
   st.session_state.saved_medications = []
if 'recent_searches' not in st.session_state:
   st.session_state.recent_searches = []


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
   search = {
       'medication': medication,
       'condition': condition,
       'dosage': dosage,
       'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M")
   }
   if search not in st.session_state.recent_searches:
       st.session_state.recent_searches.insert(0, search)
       # Keep only last 10 searches
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
  
   # Rest of your main code
   with st.sidebar:
       # Saved Medications section
       col1, col2 = st.columns([3, 1])
       with col1:
           st.markdown("## 📋 Saved Medications")
       with col2:
           if st.session_state.saved_medications:
               if st.button("Clear All", key="clear_saved", type="secondary", use_container_width=True):
                   st.session_state.saved_medications = []
                   st.rerun()
       
       if st.session_state.saved_medications:
           for med in st.session_state.saved_medications:
               col1, col2 = st.columns([4, 1])
               with col1:
                   st.write(f"• {med['name']}")
                   if med.get('dosage'):
                       st.caption(f"📊 Dosage: {med['dosage']}")
               with col2:
                   if st.button("🗑️", key=f"remove_saved_{med['name']}", help="Remove medication"):
                       remove_saved_medication(med)
       else:
           st.info("No saved medications yet")
       
       # Recent Searches section
       col1, col2 = st.columns([3, 1])
       with col1:
           st.markdown("## 🔍 Recent Searches")
       with col2:
           if st.session_state.recent_searches:
               if st.button("Clear All", key="clear_recent", type="secondary", use_container_width=True):
                   clear_recent_searches()
       
       if st.session_state.recent_searches:
           for idx, search in enumerate(st.session_state.recent_searches):
               col1, col2 = st.columns([4, 1])
               with col1:
                   st.write(f"• {search['medication']}")
                   if search['dosage']:
                       st.caption(f"📊 Dosage: {search['dosage']}")
                   if search['condition']:
                       st.caption(f"🏥 For: {search['condition']}")
                   st.caption(f"⏰ {search['timestamp']}")
               with col2:
                   if st.button("🗑️", key=f"remove_recent_{idx}", help="Remove from history"):
                       st.session_state.recent_searches.pop(idx)
                       st.rerun()
       else:
           st.info("No recent searches")

       # Add information section to sidebar
       st.markdown("### ✍️ How it Works")
       st.markdown("""
       1. Search for your medication
       2. Select from the suggestions
       3. View detailed analysis
       4. Save medications for later
       """)
       
       st.markdown("### ✨ Features")
       st.markdown("""
       - 💰 Find cheaper alternatives
       - 🌿 Get dietary recommendations
       - ⚠️ View important interactions
       - 📊 Track your medications
       """)
       
       st.markdown("### 💡 Tips")
       st.markdown("""
       - Use generic names for better results
       - Add conditions for targeted results
       - Save medications for quick access
       - Check interactions before combining medications
       """)

   # Main content area
   # Logo and title
   st.markdown("# 💊 MediMeal")
   st.markdown("# MediMeal: Smart Prescription & Nutrition Advisor")
  
   # Search section - Modified to use a single searchable selectbox
   st.markdown("### 🔍 Search Medications")
   
   # Create the selectbox with search functionality
   selected_medication = st.selectbox(
       "Search for medications",
       options=get_medication_suggestions(""),  # Get all medications initially
       placeholder="Start typing to search medications...",
       key="med_select"
   )
   
   condition = st.text_input(
       "Medical Condition (Optional)",
       placeholder="e.g., fever",
       key="condition_search"
   )
   
   dosage = st.text_input(
       "Dosage (Optional)",
       placeholder="e.g., 500mg",
       key="dosage_input"
   )


   # Main content and info columns
   main_col, info_col = st.columns([2, 1])
  
   with main_col:
       if selected_medication:
           # Add to recent searches with dosage
           add_to_recent_searches(selected_medication, condition, dosage)
           
           # Search for medications
           results = search_medications(selected_medication, condition)
           
           if results:
               if condition:
                   matching_results = [r for r in results if r.get('condition_info', {}).get('matches', False)]
                   st.write(f"Found {len(matching_results)} medications indicated for {condition}")
                   st.write(f"(Showing all {len(results)} related medications)")
              
               for idx, result in enumerate(results):
                   formatted_details = format_medication_details(result)
                  
                   with st.expander(f"{formatted_details['name']}"):
                       # Save button and dosage display in top row
                       col1, col2, col3 = st.columns([3, 2, 1])
                       with col1:
                           if dosage:
                               st.markdown(f"**📊 Dosage:** {dosage}")
                       with col3:
                           if st.button("Save", key=f"save_{idx}", type="primary"):
                               result['dosage'] = dosage  # Add dosage to saved medication
                               save_medication(result)
                      
                       # Medication details
                       st.markdown("### 💊 Medication Details")
                       st.write(f"**Form:** {formatted_details['type']}")
                      
                       # Active ingredients
                       st.markdown("### 🧪 Active Ingredients")
                       for ing in formatted_details['ingredients']:
                           st.write(f"• {ing}")
           else:
               st.info("No medications found. Try a different search term.")
  
   # Right info column removed as content moved to sidebar
   with info_col:
       pass  # Empty column for spacing, or you can remove this section entirely


if __name__ == "__main__":
   # Initialize session state
   if 'saved_medications' not in st.session_state:
       st.session_state.saved_medications = []
   if 'recent_searches' not in st.session_state:
       st.session_state.recent_searches = []
  
   main()
