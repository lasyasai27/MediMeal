import requests
import streamlit as st

# Update this near the top of your app.py where other constants are defined
API_URL = "http://localhost:8001"  # This should point to your FastAPI backend

# Replace this part in your existing search section
if selected_medication and analyze_button:
    with st.spinner('Analyzing medication...'):
        # Replace the old search_medications call with the new API endpoint
        try:
            response = requests.get(f"{API_URL}/search/medications", params={
                "query": selected_medication,
                "condition": condition
            })
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    # Rest of your existing code for displaying results
                    primary_tab, similar_tab, effects_tab, details_tab = st.tabs([
                        "💊 Primary Details",
                        "🔄 Similar Medications",
                        "⚠️ Side Effects",
                        "📋 Additional Details"
                    ])
                    # ... rest of your existing display code ...
            else:
                st.error("Error connecting to the medication service")
        except Exception as e:
            st.error(f"Error: {str(e)}") 