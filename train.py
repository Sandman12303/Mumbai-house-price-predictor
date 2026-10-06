import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
import joblib
import os

def main():
    csv_path = r"C:\Mumbai House Prices.csv"
    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)
    print(f"Initial shape: {df.shape}")

    # 1. Convert price to rupees: L = 1e5, Cr = 1e7
    multiplier = np.where(df['price_unit'].astype(str).str.strip() == 'Cr', 1e7, 1e5)
    df['price_rs'] = df['price'].astype(float) * multiplier
    df = df.drop(columns=['price', 'price_unit'])

    # 2. Filter to Apartment only
    df = df[df['type'].astype(str).str.strip() == 'Apartment'].reset_index(drop=True)
    print(f"Filtered to 'Apartment' type only. Remaining shape: {df.shape}")

    # 3. Drop exact duplicate rows
    initial_count = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    dropped_dups = initial_count - len(df)
    print(f"Dropped {dropped_dups} duplicate rows ({dropped_dups / initial_count * 100:.1f}%). Remaining shape: {df.shape}")

    # 4. Group localities to top 200 plus "Other"
    top_200_localities = df['locality'].value_counts().nlargest(200).index.tolist()
    top_200_set = set(top_200_localities)

    # Build region_localities: dict mapping each region to sorted list of localities that actually appear in that region (excluding "Other")
    region_localities = {}
    for region_name, group in df.groupby('region'):
        locs_in_group = [l for l in group['locality'].unique() if l in top_200_set and l != "Other"]
        region_localities[region_name] = sorted(list(set(locs_in_group)))

    # Map locality column in df to top 200 or "Other"
    df['locality'] = df['locality'].apply(lambda l: l if l in top_200_set else "Other")

    # Store category dtypes explicitly
    categorical_cols = ['type', 'locality', 'region', 'status', 'age']
    categories_meta = {}

    for col in categorical_cols:
        unique_vals = sorted(df[col].astype(str).unique().tolist())
        if col == 'locality' and "Other" not in unique_vals:
            unique_vals.append("Other")
        df[col] = pd.Categorical(df[col], categories=unique_vals)
        categories_meta[col] = unique_vals

    # Prepare features and target
    X = df[['bhk', 'type', 'locality', 'area', 'region', 'status', 'age']].copy()
    y_rs = df['price_rs'].values
    y_log = np.log(y_rs)

    # Train / test split (80/20, random_state=42)
    X_train, X_test, y_log_train, y_log_test, y_rs_train, y_rs_test = train_test_split(
        X, y_log, y_rs, test_size=0.2, random_state=42
    )

    print("\nTraining HistGradientBoostingRegressor(categorical_features='from_dtype')...")
    model = HistGradientBoostingRegressor(
        categorical_features="from_dtype",
        random_state=42
    )
    model.fit(X_train, y_log_train)

    # Evaluation
    y_log_pred_test = model.predict(X_test)
    y_rs_pred_test = np.exp(y_log_pred_test)

    r2_log = r2_score(y_log_test, y_log_pred_test)
    r2_rs = r2_score(y_rs_test, y_rs_pred_test)
    median_pct_error = np.median(np.abs(y_rs_test - y_rs_pred_test) / y_rs_test) * 100

    print(f"\n--- Model Evaluation Results (Apartments Only) ---")
    print(f"Log(Price) R^2 Score: {r2_log:.4f}")
    print(f"Price (INR) R^2 Score: {r2_rs:.4f}")
    print(f"Median Absolute Percentage Error: {median_pct_error:.2f}%")

    bhk_min, bhk_max = int(df['bhk'].min()), int(df['bhk'].max())
    area_min, area_max = float(df['area'].min()), float(df['area'].max())

    output_payload = {
        'model': model,
        'categories': categories_meta,
        'region_localities': region_localities,
        'bhk_bounds': {'min': bhk_min, 'max': bhk_max},
        'area_bounds': {'min': area_min, 'max': area_max},
        'feature_cols': X.columns.tolist()
    }

    model_path = os.path.join(os.path.dirname(__file__), "model.joblib")
    joblib.dump(output_payload, model_path)
    print(f"\nModel and region_localities saved to {model_path}")

if __name__ == "__main__":
    main()
