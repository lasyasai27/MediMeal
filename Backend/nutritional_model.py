import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os

class NutritionalModel:
    def __init__(self):
        self.data_dir = 'data'
        self.models = {}
        self.scalers = {}
        
    def load_data(self):
        """Load and preprocess the anthropometric data"""
        try:
            # Load the dataset
            df = pd.read_csv(os.path.join(self.data_dir, 'anthropometric_measurements.csv'))
            print(f"Loaded dataset with {len(df)} records")
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None

    def prepare_features(self, df):
        """Prepare features for training"""
        # Features to predict body composition
        feature_columns = [
            'current_weight_kg',
            'bmi_kg_m2',
            'fat_mass_perc',
            'muscle_mass_perc',
            'visceral_fat_level',
            'basal_metabolism',
            'waist_cm',
            'hip_cm'
        ]
        
        # Remove rows with missing values
        df_clean = df[feature_columns].dropna()
        
        return df_clean

    def train_models(self):
        """Train multiple models for different health metrics"""
        print("Training nutritional intervention models...")
        
        # Load and prepare data
        df = self.load_data()
        if df is None:
            return
        
        df_clean = self.prepare_features(df)
        
        # Define target variables to predict
        targets = {
            'weight': 'current_weight_kg',
            'body_fat': 'fat_mass_perc',
            'muscle_mass': 'muscle_mass_perc',
            'visceral_fat': 'visceral_fat_level'
        }
        
        for target_name, target_column in targets.items():
            print(f"\nTraining model for {target_name}...")
            
            # Prepare features and target
            features = df_clean.drop(columns=[target_column])
            target = df_clean[target_column]
            
            # Scale features
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                features_scaled, target, test_size=0.2, random_state=42
            )
            
            # Train model
            model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            print(f"Model performance for {target_name}:")
            print(f"Mean Squared Error: {mse:.4f}")
            print(f"R² Score: {r2:.4f}")
            
            # Save model and scaler
            self.models[target_name] = model
            self.scalers[target_name] = scaler
            
            # Save feature importance
            feature_importance = pd.DataFrame({
                'feature': features.columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\nTop 3 important features:")
            print(feature_importance.head(3))
        
        print("\nAll models trained successfully!")

    def predict_metrics(self, input_data: dict) -> dict:
        """Make predictions using trained models"""
        try:
            results = {}
            
            # Prepare input data
            input_df = pd.DataFrame([input_data])
            
            for metric, model in self.models.items():
                # Get features excluding the target
                features = input_df.drop(columns=[self.targets[metric]], errors='ignore')
                
                # Scale features
                features_scaled = self.scalers[metric].transform(features)
                
                # Make prediction
                prediction = model.predict(features_scaled)[0]
                
                results[metric] = float(prediction)
            
            return results
            
        except Exception as e:
            print(f"Error making predictions: {e}")
            return {}

    def analyze_trends(self, user_id: int) -> dict:
        """Analyze trends for a specific user"""
        try:
            df = self.load_data()
            user_data = df[df['id'] == user_id].sort_values('visit')
            
            if len(user_data) < 2:
                return {"error": "Not enough data points for trend analysis"}
            
            trends = {}
            metrics = ['current_weight_kg', 'fat_mass_perc', 'muscle_mass_perc', 'visceral_fat_level']
            
            for metric in metrics:
                initial = user_data[metric].iloc[0]
                current = user_data[metric].iloc[-1]
                change = current - initial
                percent_change = (change / initial) * 100
                
                trends[metric] = {
                    'initial': float(initial),
                    'current': float(current),
                    'change': float(change),
                    'percent_change': float(percent_change)
                }
            
            return trends
            
        except Exception as e:
            print(f"Error analyzing trends: {e}")
            return {"error": str(e)}

# Initialize and train models
nutritional_model = NutritionalModel()
nutritional_model.train_models() 