import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict
import os

class MedicineRecommender:
    def __init__(self):
        # Get absolute path to the data file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_path = os.path.join(current_dir, 'data', 'medicines_dataset.csv')
        
        # Load the dataset
        self.df = pd.read_csv(data_path)
        
        # Print first few medicine names to see the format
        print("First few medicine names:", self.df['name'].head().tolist())
        
        # Clean and preprocess the data using actual column names
        self.df['combined_features'] = self.df['name'].fillna('') + ' ' + \
                                     self.df['Chemical Class'].fillna('') + ' ' + \
                                     self.df['Therapeutic Class'].fillna('') + ' ' + \
                                     self.df['Action Class'].fillna('') + ' ' + \
                                     self.df['use0'].fillna('') + ' ' + \
                                     self.df['use1'].fillna('') + ' ' + \
                                     self.df['use2'].fillna('')
        
        # Create TF-IDF vectorizer
        self.tfidf = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = self.tfidf.fit_transform(self.df['combined_features'])
        
    def clean_float(self, value: float) -> float:
        """Clean float values to ensure JSON compatibility"""
        if pd.isna(value) or np.isinf(value):
            return 0.0
        return float(min(max(value, -1e300), 1e300))
    
    def find_medicine_index(self, medicine_name: str) -> int:
        """Find the index of a medicine using flexible matching"""
        # Clean the search term - remove parentheses and content within
        clean_search = medicine_name.split('(')[0].strip().lower()
        
        # Try basic contains match first
        contains_match = self.df[self.df['name'].str.lower().str.contains(
            clean_search, na=False
        )]
        
        if not contains_match.empty:
            return contains_match.index[0]
        
        # If no match, try with individual words
        search_words = clean_search.split()
        for word in search_words:
            if len(word) > 3:  # Only search for words longer than 3 characters
                word_match = self.df[self.df['name'].str.lower().str.contains(
                    word, na=False
                )]
                if not word_match.empty:
                    return word_match.index[0]
        
        # If still no match, try searching in other columns
        for column in ['Chemical Class', 'Therapeutic Class', 'Action Class']:
            column_match = self.df[self.df[column].str.lower().str.contains(
                clean_search, na=False
            )]
            if not column_match.empty:
                return column_match.index[0]
        
        raise ValueError(f"Medicine '{medicine_name}' not found")

    def get_similar_medicines(self, medicine_name: str, n_recommendations: int = 5) -> List[Dict]:
        """Get similar medicines based on name and features"""
        try:
            # Find medicines containing the search term
            matches = self.df[self.df['name'].str.contains(medicine_name, case=False, na=False)]
            
            if matches.empty:
                return []
            
            # Get the first matching medicine
            med_idx = matches.index[0]
            
            # Calculate similarity scores
            similarity_scores = cosine_similarity(
                self.tfidf_matrix[med_idx:med_idx+1], 
                self.tfidf_matrix
            ).flatten()
            
            # Get indices of similar medicines
            similar_indices = similarity_scores.argsort()[::-1][1:n_recommendations+1]
            
            # Get similar medicines details
            recommendations = []
            for idx in similar_indices:
                recommendations.append({
                    'name': str(self.df.iloc[idx]['name']),
                    'chemical_class': str(self.df.iloc[idx]['Chemical Class']),
                    'therapeutic_class': str(self.df.iloc[idx]['Therapeutic Class']),
                    'action_class': str(self.df.iloc[idx]['Action Class']),
                    'uses': [
                        str(self.df.iloc[idx]['use0']),
                        str(self.df.iloc[idx]['use1']),
                        str(self.df.iloc[idx]['use2'])
                    ],
                    'similarity_score': self.clean_float(similarity_scores[idx])
                })
            
            return recommendations
            
        except Exception as e:
            print(f"Error in get_similar_medicines: {e}")
            return []
    
    def get_side_effects(self, medicine_name: str) -> Dict:
        """Get side effects for a specific medicine"""
        try:
            matches = self.df[self.df['name'].str.contains(medicine_name, case=False, na=False)]
            
            if matches.empty:
                return {
                    'name': medicine_name,
                    'side_effects': [],
                    'habit_forming': 'No information',
                    'chemical_class': 'No information',
                    'therapeutic_class': 'No information',
                    'substitutes': []
                }
            
            medicine_data = matches.iloc[0]
            
            # Collect all side effects
            side_effects = []
            for i in range(42):  # sideEffect0 to sideEffect41
                effect = medicine_data.get(f'sideEffect{i}')
                if pd.notna(effect) and effect and str(effect).strip():
                    side_effects.append(str(effect).strip())
            
            # Clean substitutes
            substitutes = []
            for i in range(5):
                sub = medicine_data.get(f'substitute{i}')
                if pd.notna(sub) and sub and str(sub).strip():
                    substitutes.append(str(sub).strip())
            
            return {
                'name': str(medicine_data['name']),
                'side_effects': side_effects,
                'habit_forming': str(medicine_data.get('Habit Forming', 'No information')),
                'chemical_class': str(medicine_data.get('Chemical Class', 'No information')),
                'therapeutic_class': str(medicine_data.get('Therapeutic Class', 'No information')),
                'substitutes': substitutes
            }
        except Exception as e:
            print(f"Error in get_side_effects: {e}")
            return {
                'name': medicine_name,
                'side_effects': [],
                'habit_forming': 'No information',
                'chemical_class': 'No information',
                'therapeutic_class': 'No information',
                'substitutes': []
            } 