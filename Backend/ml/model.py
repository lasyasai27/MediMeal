from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import numpy as np
from scipy.sparse import hstack

class DrugRecommendationModel:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10, 
            random_state=42
        )
        
    def prepare_features(self, features):
        # Combine all features into a single sparse matrix
        feature_matrix = hstack([
            features['side_effects'],
            features['drug_classes'],
            features['medical_condition'].reshape(-1, 1),
            features['rating']
        ])
        return feature_matrix
        
    def train(self, features, target_column):
        X = self.prepare_features(features)
        y = target_column
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Return test data for evaluation
        return X_test, y_test
    
    def predict(self, features):
        X = self.prepare_features(features)
        return self.model.predict(X)
    
    def predict_proba(self, features):
        X = self.prepare_features(features)
        return self.model.predict_proba(X) 