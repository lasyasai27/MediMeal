import pandas as pd
import requests
import zipfile
import io
import os
from bs4 import BeautifulSoup

def download_and_format_fda_data():
    # Create data directory if it doesn't exist
    os.makedirs('backend/data', exist_ok=True)
    
    # Download FDA NDC data
    url = "https://www.fda.gov/downloads/Drugs/InformationOnDrugs/UCM527389.zip"
    response = requests.get(url)
    
    # Extract and read the data
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        with z.open('product.txt') as f:
            df = pd.read_csv(f, sep='\t')
    
    # Select relevant columns
    columns = [
        'PROPRIETARYNAME', 'NONPROPRIETARYNAME', 
        'ACTIVE_INGREDIENTS', 'INACTIVE_INGREDIENTS',
        'DOSAGEFORMNAME', 'ROUTENAME'
    ]
    
    df_cleaned = df[columns].copy()
    
    # Save to CSV
    df_cleaned.to_csv('backend/data/FDA_NDC_Product.csv', index=False)
    
    return "FDA data downloaded and formatted successfully"

def create_interactions_database():
    # Create a structured interactions database
    interactions_data = {
        'drug_name': [],
        'interacting_drug': [],
        'effect': [],
        'severity': []
    }
    
    # Read from Medicare data to get drug list
    medicare_data = pd.read_csv('backend/data/DSD_PTD_RY24_P04_V10_DY22_BGM.csv')
    drug_list = medicare_data['Brnd_Name'].unique()
    
    # For each drug, fetch interaction data from DailyMed
    for drug in drug_list:
        try:
            url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={drug}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract interaction information
            # (This is a simplified version - you'd need to adapt based on the actual HTML structure)
            interactions = soup.find_all('div', class_='drug-interaction')
            
            for interaction in interactions:
                interactions_data['drug_name'].append(drug)
                interactions_data['interacting_drug'].append(interaction.get('interacting-drug'))
                interactions_data['effect'].append(interaction.get('effect'))
                interactions_data['severity'].append(interaction.get('severity'))
                
        except Exception as e:
            print(f"Error processing {drug}: {str(e)}")
    
    # Create DataFrame and save
    df = pd.DataFrame(interactions_data)
    df.to_csv('backend/data/drug_interactions.csv', index=False)
    
    return "Interactions database created successfully"

def create_dietary_database():
    # Create a structured dietary restrictions database
    dietary_data = {
        'drug_name': [],
        'foods_to_avoid': [],
        'recommendations': [],
        'timing_recommendations': []
    }
    
    # Read from Medicare data to get drug list
    medicare_data = pd.read_csv('backend/data/DSD_PTD_RY24_P04_V10_DY22_BGM.csv')
    drug_list = medicare_data['Brnd_Name'].unique()
    
    # For each drug, fetch dietary information
    for drug in drug_list:
        try:
            url = f"https://dailymed.nlm.nih.gov/dailymed/search.cfm?labeltype=all&query={drug}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract dietary information
            # (This is a simplified version - you'd need to adapt based on the actual HTML structure)
            dietary_info = soup.find('div', class_='dietary-info')
            
            dietary_data['drug_name'].append(drug)
            dietary_data['foods_to_avoid'].append(dietary_info.get('foods-to-avoid'))
            dietary_data['recommendations'].append(dietary_info.get('recommendations'))
            dietary_data['timing_recommendations'].append(dietary_info.get('timing'))
                
        except Exception as e:
            print(f"Error processing {drug}: {str(e)}")
    
    # Create DataFrame and save
    df = pd.DataFrame(dietary_data)
    df.to_csv('backend/data/dietary_restrictions.csv', index=False)
    
    return "Dietary restrictions database created successfully" 