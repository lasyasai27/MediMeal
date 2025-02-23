import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
import os

def preprocess_drug_data():
    # Get the absolute path to the data file
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(current_dir, 'data', 'drugs_side_effects_drugs_com.csv')
    
    # Check if file exists
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found at: {data_path}")
    
    # Read the CSV file
    df = pd.read_csv(data_path)
    
    # Clean text data
    df['side_effects'] = df['side_effects'].fillna('')
    df['medical_condition'] = df['medical_condition'].fillna('')
    
    # Convert ratings to numeric
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    
    # Encode categorical variables
    le = LabelEncoder()
    df['medical_condition_encoded'] = le.fit_transform(df['medical_condition'])
    
    return df, le 