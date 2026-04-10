import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import joblib
import os
from datetime import datetime, timedelta

def train_forecast_model():
    os.makedirs('ml/models', exist_ok=True)
    
    print("Generating synthetic historical order data...")
    # Simulate hourly order counts for the last 30 days
    dates = pd.date_range(end=datetime.now(), periods=24*30, freq='H')
    
    # Feature: hour of day, day of week
    df = pd.DataFrame({
        'ds': dates,
        'y': np.random.normal(50, 10, len(dates)) + # Base orders
             np.sin(dates.hour * (2 * np.pi / 24)) * 20 + # Daily seasonality
             (dates.dayofweek >= 5) * 30 # Weekend boost
    })
    
    # Simple linear model for trend + seasonality (simplified forecast)
    df['hour'] = df['ds'].dt.hour
    df['is_weekend'] = (df['ds'].dt.dayofweek >= 5).astype(int)
    
    X = df[['hour', 'is_weekend']]
    y = df['y']
    
    print("Training Demand Forecast model...")
    model = LinearRegression()
    model.fit(X, y)
    
    model_path = 'ml/models/forecast_model.pkl'
    print(f"Saving model to {model_path}...")
    joblib.dump(model, model_path)
    print("Forecasting model training complete.")

if __name__ == "__main__":
    train_forecast_model()
