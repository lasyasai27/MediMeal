import pandas as pd
from preprocess import DrugDataPreprocessor
from model import DrugRecommendationModel
from sklearn.metrics import classification_report, accuracy_score

def train_model():
    # Load data
    df = pd.read_csv('backend/data/drugs_side_effects_drugs_com.csv')
    
    # Initialize preprocessor and model
    preprocessor = DrugDataPreprocessor()
    model = DrugRecommendationModel()
    
    # Preprocess data
    features = preprocessor.preprocess(df)
    
    # Define target (for example, predicting if a drug has high rating)
    target = (df['rating'] > df['rating'].median()).astype(int)
    
    # Train model
    X_test, y_test = model.train(features, target)
    
    # Make predictions
    y_pred = model.predict(X_test)
    
    # Print metrics
    print("\nModel Performance:")
    print("Accuracy:", accuracy_score(y_test, y_pred))
    print("\nDetailed Classification Report:")
    print(classification_report(y_test, y_pred))
    
    return model, preprocessor

if __name__ == "__main__":
    train_model() 