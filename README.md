# Mumbai House Price Predictor

A lightweight web application for predicting Mumbai flat prices using a `HistGradientBoostingRegressor` model trained on historical listing data.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Train the model:
   ```bash
   python train.py
   ```

3. Run the web application:
   ```bash
   uvicorn app:app --reload
   ```

4. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```
