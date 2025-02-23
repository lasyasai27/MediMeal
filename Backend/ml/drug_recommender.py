from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class DrugRecommender:
    def __init__(self, df):
        self.df = df
        self.tfidf = TfidfVectorizer(stop_words='english')
        
        # Create TF-IDF matrix from side effects
        self.tfidf_matrix = self.tfidf.fit_transform(df['side_effects'])
        
        # Calculate similarity matrix
        self.cosine_sim = cosine_similarity(self.tfidf_matrix)
        
    def get_recommendations(self, drug_name, n_recommendations=5):
        # Find the index of the drug
        idx = self.df[self.df['drug_name'] == drug_name].index[0]
        
        # Get similarity scores
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get top N similar drugs
        sim_scores = sim_scores[1:n_recommendations+1]
        drug_indices = [i[0] for i in sim_scores]
        
        return self.df.iloc[drug_indices][['drug_name', 'medical_condition', 'rating']] 