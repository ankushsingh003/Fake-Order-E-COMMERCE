from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import os

app = FastAPI(title="Fraud Detection API")

# Path to the saved model
MODEL_PATH = os.environ.get("FRAUD_MODEL_PATH", "ml/models/fraud_model.pkl")

# Load model at startup
model = None
if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print(f"Model loaded from {MODEL_PATH}")
else:
    print(f"Warning: Model file not found at {MODEL_PATH}")

class OrderFeatures(BaseModel):
    order_amount: float
    orders_per_user_1m: float

@app.post("/predict")
async def predict(features: OrderFeatures):
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Prepare data for prediction
    data = pd.DataFrame([[features.order_amount, features.orders_per_user_1m]], 
                        columns=['order_amount', 'orders_per_user_1m'])
    
    # Isolation Forest returns -1 for anomalies and 1 for normal
    prediction = model.predict(data)
    dist_score = model.decision_function(data)
    
    is_fraud = bool(prediction[0] == -1)
    
    return {
        "is_fraud": is_fraud,
        "fraud_score": float(dist_score[0]),
        "prediction_raw": int(prediction[0])
    }

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
