import pandas as pd
import numpy as np
import os

def format_price_rs(val):
    if pd.isna(val) or val <= 0:
        return "N/A"
    if val >= 1e7:
        return f"Rs {val / 1e7:.2f} Crore"
    else:
        return f"Rs {val / 1e5:.2f} Lakhs"

def main():
    folder = os.path.dirname(__file__)
    stats_path = os.path.join(folder, "region_stats.csv")
    coords_path = os.path.join(folder, "region_coords.csv")

    if not os.path.exists(stats_path) or not os.path.exists(coords_path):
        raise FileNotFoundError("Missing region_stats.csv or region_coords.csv.")

    stats_df = pd.read_csv(stats_path)
    coords_df = pd.read_csv(coords_path)

    # Merge on region
    merged = pd.merge(stats_df, coords_df, on='region', how='left')

    # Format clean columns
    export_df = pd.DataFrame()
    export_df['Region / Location'] = merged['region']
    export_df['Latitude'] = merged['lat']
    export_df['Longitude'] = merged['lon']
    export_df['Total Listing Count'] = merged['all_count']
    export_df['Median Price / Sq Ft (INR)'] = merged['all_median_price_per_sqft']
    export_df['Typical 2 BHK Price'] = merged['bhk2_median_price'].apply(format_price_rs)
    export_df['1 BHK Listings'] = merged['bhk1_count'].fillna(0).astype(int)
    export_df['1 BHK Median Price / Sq Ft'] = merged['bhk1_median_price_per_sqft']
    export_df['2 BHK Listings'] = merged['bhk2_count'].fillna(0).astype(int)
    export_df['2 BHK Median Price / Sq Ft'] = merged['bhk2_median_price_per_sqft']
    export_df['3 BHK Listings'] = merged['bhk3_count'].fillna(0).astype(int)
    export_df['3 BHK Median Price / Sq Ft'] = merged['bhk3_median_price_per_sqft']

    # Sort by Median Price / Sq Ft descending
    export_df = export_df.sort_values(by='Median Price / Sq Ft (INR)', ascending=False).reset_index(drop=True)

    # Save to Excel and CSV
    excel_path = os.path.join(folder, "Mumbai_Location_Stats.xlsx")
    csv_path = os.path.join(folder, "Mumbai_Location_Stats.csv")

    # Try exporting Excel using openpyxl or fallback to CSV
    try:
        export_df.to_excel(excel_path, index=False, engine='openpyxl')
        print(f"Successfully exported Excel file to: {excel_path}")
    except Exception as e:
        print(f"Excel export notice ({e}), exporting CSV file...")

    export_df.to_csv(csv_path, index=False)
    print(f"Successfully exported CSV file to: {csv_path}")

    print(f"\nSpreadsheet summary: {len(export_df)} regions exported.")
    print("\nTop 5 Most Expensive Locations:")
    print(export_df[['Region / Location', 'Median Price / Sq Ft (INR)', 'Typical 2 BHK Price', 'Total Listing Count']].head(5).to_string(index=False))

if __name__ == "__main__":
    main()
