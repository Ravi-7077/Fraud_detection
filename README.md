# Fraud Detection

A Python‑based fraud detection pipeline that trains a model on transaction data and provides an API for scoring new records.

## Overview

- **Data preprocessing** – Handles CSV ingestion, feature engineering, and scaling.
- **Modeling** – Implements a RandomForest classifier (saved as `rf_model.joblib`).
- **API** – FastAPI service (`run_app.ps1` launches the app) to score incoming transactions.
- **Docker** – Containerised deployment via the provided `Dockerfile` and `docker‑compose.yml`.

## Setup

1. **Clone the repository** (once it is pushed to GitHub):
   ```bash
   git clone https://github.com/Ravi-7077/Fraud_detection.git
   cd Fraud_detection
   ```
2. **Create a virtual environment** and install dependencies:
   ```bash
   python -m venv .venv_314
   .\.venv_314\Scripts\activate   # Windows PowerShell
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```powershell
   ./run_app.ps1
   ```
   The API will be available at `http://localhost:8000`.

## Usage

- **Training** – Execute `python train_model.py` (script not shown here) to generate `rf_model.joblib`.
- **Scoring** – Send a POST request to `/predict` with JSON payload representing a transaction.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b <feature>`.
3. Commit your changes and push to your fork.
4. Open a Pull Request.

## License

This project is licensed under the MIT License – see the `LICENSE` file for details.
