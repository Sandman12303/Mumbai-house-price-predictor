import pandas as pd
import numpy as np
import os

def main():
    csv_path = r"C:\Mumbai House Prices.csv"
    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path)

    # 1. Convert price to rupees: L = 1e5, Cr = 1e7
    multiplier = np.where(df['price_unit'].astype(str).str.strip() == 'Cr', 1e7, 1e5)
    df['price_rs'] = df['price'].astype(float) * multiplier
    df = df.drop(columns=['price', 'price_unit'])

    # 2. Filter type == "Apartment" and exclude typo region 'Ambarnath'
    df = df[df['type'].astype(str).str.strip() == 'Apartment'].reset_index(drop=True)
    df = df[df['region'] != 'Ambarnath'].reset_index(drop=True)

    # 3. Drop exact duplicate rows
    df = df.drop_duplicates().reset_index(drop=True)

    # 4. Compute price_per_sqft
    df['price_per_sqft'] = df['price_rs'] / df['area']

    print(f"Cleaned dataset has {len(df)} apartment listings across {df['region'].nunique()} unique regions.")

    # Group by region
    records = []
    dropped_regions = []

    for region_name, group in df.groupby('region'):
        total_count = len(group)
        if total_count < 20:
            dropped_regions.append((region_name, total_count))
            continue

        all_median_sqft = group['price_per_sqft'].median()

        # 1 BHK stats
        b1 = group[group['bhk'] == 1]
        b1_count = len(b1)
        b1_sqft = b1['price_per_sqft'].median() if b1_count > 0 else np.nan

        # 2 BHK stats
        b2 = group[group['bhk'] == 2]
        b2_count = len(b2)
        b2_sqft = b2['price_per_sqft'].median() if b2_count > 0 else np.nan
        b2_median_price = b2['price_rs'].median() if b2_count > 0 else np.nan

        # 3 BHK stats
        b3 = group[group['bhk'] == 3]
        b3_count = len(b3)
        b3_sqft = b3['price_per_sqft'].median() if b3_count > 0 else np.nan

        # If no 2 BHK, use overall median price scaled to 750 sqft as fallback typical 2 BHK price
        if pd.isna(b2_median_price):
            b2_median_price = all_median_sqft * 750

        records.append({
            'region': region_name,
            'all_count': total_count,
            'all_median_price_per_sqft': round(all_median_sqft, 2),
            'bhk1_count': b1_count,
            'bhk1_median_price_per_sqft': round(b1_sqft, 2) if not pd.isna(b1_sqft) else np.nan,
            'bhk2_count': b2_count,
            'bhk2_median_price_per_sqft': round(b2_sqft, 2) if not pd.isna(b2_sqft) else np.nan,
            'bhk2_median_price': round(b2_median_price, 2) if not pd.isna(b2_median_price) else np.nan,
            'bhk3_count': b3_count,
            'bhk3_median_price_per_sqft': round(b3_sqft, 2) if not pd.isna(b3_sqft) else np.nan
        })

    stats_df = pd.DataFrame(records)
    output_path = os.path.join(os.path.dirname(__file__), "region_stats.csv")
    stats_df.to_csv(output_path, index=False)

    print(f"\n--- Data Prep Summary ---")
    print(f"Retained regions (count >= 20): {len(stats_df)}")
    print(f"Dropped regions (count < 20): {len(dropped_regions)}")
    print("\nSample of dropped regions:")
    for r, c in dropped_regions[:15]:
        print(f"  - {r}: {c} listing(s)")
    if len(dropped_regions) > 15:
        print(f"  ... and {len(dropped_regions) - 15} more.")

    print(f"\nSaved region stats to {output_path}")

if __name__ == "__main__":
    main()
