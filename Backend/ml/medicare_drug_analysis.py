import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import logging

logger = logging.getLogger(__name__)

class MedicareDrugAnalyzer:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.features = [
            'Tot_Clms_2022', 'Tot_Benes_2022', 'Tot_Dsg_Unts_2022',
            'Avg_Spnd_Per_Clm_2022', 'Avg_Spnd_Per_Bene_2022'
        ]
        
    def preprocess_data(self, df):
        """Preprocess the Medicare drug data"""
        # Remove rows with missing values
        df = df.dropna(subset=self.features + ['Tot_Spndng_2022'])
        
        # Extract features and target
        X = df[self.features]
        y = df['Tot_Spndng_2022']
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y
        
    def train_model(self, data_path):
        """Train the drug spending prediction model"""
        try:
            # Load data
            df = pd.read_csv(data_path)
            logger.info(f"Loaded dataset with {len(df)} records")
            
            # Preprocess data
            X_scaled, y = self.preprocess_data(df)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42
            )
            
            # Train model
            self.model = RandomForestRegressor(
                n_estimators=100,
                random_state=42
            )
            self.model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test)
            r2 = r2_score(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            
            logger.info(f"Model trained successfully. R2 Score: {r2:.4f}, RMSE: {rmse:.2f}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            return False
    
    def predict_spending(self, features_dict):
        """Predict total spending for a drug based on input features"""
        try:
            if not self.model:
                raise ValueError("Model not trained yet")
                
            # Prepare features
            features = np.array([[
                features_dict['total_claims'],
                features_dict['total_beneficiaries'],
                features_dict['total_dosage_units'],
                features_dict['avg_spending_per_claim'],
                features_dict['avg_spending_per_beneficiary']
            ]])
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            
            return {
                'predicted_total_spending': prediction,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return {
                'error': str(e),
                'status': 'error'
            } 