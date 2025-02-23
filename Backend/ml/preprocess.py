import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
import re

class DrugDataPreprocessor:
    def __init__(self):
        self.label_encoder = LabelEncoder()
        self.tfidf = TfidfVectorizer(max_features=1000, stop_words='english')
        self.mlb = MultiLabelBinarizer()
        
    def clean_text(self, text):
        if isinstance(text, str):
            # Remove special characters and extra whitespace
            text = re.sub(r'[^\w\s]', ' ', text)
            text = ' '.join(text.split())
            return text.lower()
        return ''

    def preprocess(self, df):
        # Create copy to avoid modifying original data
        df = df.copy()
        
        # Clean text columns
        text_columns = ['side_effects', 'medical_condition_description']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].apply(self.clean_text)
        
        # Convert rating to numeric
        df['rating'] = pd.to_numeric(df['rating'].str.rstrip('%'), errors='coerce')
        
        # Extract drug classes as list
        df['drug_classes'] = df['drug_classes'].fillna('').str.split(', ')
        
        # Create features
        features = {}
        
        # TF-IDF for side effects
        features['side_effects'] = self.tfidf.fit_transform(df['side_effects'])
        
        # One-hot encode drug classes
        drug_classes = self.mlb.fit_transform(df['drug_classes'])
        features['drug_classes'] = drug_classes
        
        # Encode medical condition
        features['medical_condition'] = self.label_encoder.fit_transform(df['medical_condition'])
        
        # Add numeric features
        features['rating'] = df['rating'].values.reshape(-1, 1)
        
        return features 