from fraud_detection.tasks.run_ml import ml_predict

sample = {
    "transaction_id": 1,
    "user_id": 42,
    "amount": 120.5,
    "transaction_type": "purchase",
    "merchant_category": "store_x",
    "country": "US",
    "hour": 12,
    "device_risk_score": 0.2,
    "ip_risk_score": 0.1,
}
prob = ml_predict(sample)
print("Fraud probability:", prob)