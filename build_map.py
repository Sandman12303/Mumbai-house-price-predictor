import pandas as pd
import numpy as np
import os
import folium
import branca.colormap as cm

def format_price_display(price_rs):
    if pd.isna(price_rs) or price_rs <= 0:
        return "N/A"
    if price_rs >= 1e7:
        cr_val = price_rs / 1e7
        return f"₹ {cr_val:.2f} Crore"
    else:
        lakh_val = price_rs / 1e5
        return f"₹ {lakh_val:.2f} Lakhs"

def main():
    stats_path = os.path.join(os.path.dirname(__file__), "region_stats.csv")
    coords_path = os.path.join(os.path.dirname(__file__), "region_coords.csv")
    output_html = os.path.join(os.path.dirname(__file__), "mumbai_price_map.html")

    if not os.path.exists(stats_path) or not os.path.exists(coords_path):
        raise FileNotFoundError("Missing region_stats.csv or region_coords.csv. Run step 1 and step 2 first.")

    stats_df = pd.read_csv(stats_path)
    coords_df = pd.read_csv(coords_path)

    # Merge stats with coords
    merged = pd.merge(stats_df, coords_df, on='region', how='inner')
    merged = merged.dropna(subset=['lat', 'lon']).reset_index(drop=True)

    print(f"Loaded {len(merged)} valid regions with coordinates for map rendering.")

    # Step 4: Sanity check printouts
    sorted_by_price = merged.sort_values(by='all_median_price_per_sqft', ascending=False)

    print("\n=======================================================")
    print(" 10 MOST EXPENSIVE REGIONS (Median Price / sq ft)")
    print("=======================================================")
    for idx, row in sorted_by_price.head(10).iterrows():
        print(f"  {row['region']:<25} | Rs {row['all_median_price_per_sqft']:>8,.0f} / sq ft | Listings: {int(row['all_count']):>4} | Typical 2BHK: {format_price_display(row['bhk2_median_price']).replace('₹', 'Rs')}")

    print("\n=======================================================")
    print(" 10 CHEAPEST REGIONS (Median Price / sq ft)")
    print("=======================================================")
    for idx, row in sorted_by_price.tail(10).iterrows():
        print(f"  {row['region']:<25} | Rs {row['all_median_price_per_sqft']:>8,.0f} / sq ft | Listings: {int(row['all_count']):>4} | Typical 2BHK: {format_price_display(row['bhk2_median_price']).replace('₹', 'Rs')}")

    # Min and max price per sqft for sequential color scale
    min_price = merged['all_median_price_per_sqft'].min()
    max_price = merged['all_median_price_per_sqft'].max()

    # Create linear colormap scale (YlOrRd / Sunset palette)
    colormap = cm.LinearColormap(
        colors=['#2c7bb6', '#abd9e9', '#ffffbf', '#fdae61', '#d7191c'],
        vmin=min_price,
        vmax=max_price,
        caption="Median Price per sq ft (₹)"
    )

    # Initialize Folium Map centered on Mumbai / MMR
    mmr_map = folium.Map(
        location=[19.1000, 72.9200],
        zoom_start=11,
        tiles='OpenStreetMap'
    )

    # Create FeatureGroups for Layer Control (All, 1 BHK, 2 BHK, 3 BHK)
    fg_all = folium.FeatureGroup(name="All Apartments", show=True)
    fg_1bhk = folium.FeatureGroup(name="1 BHK", show=False)
    fg_2bhk = folium.FeatureGroup(name="2 BHK", show=False)
    fg_3bhk = folium.FeatureGroup(name="3 BHK", show=False)

    for _, row in merged.iterrows():
        r_name = row['region']
        lat, lon = row['lat'], row['lon']
        all_sqft = row['all_median_price_per_sqft']
        all_cnt = int(row['all_count'])
        b2_price = row['bhk2_median_price']

        color = colormap(all_sqft)

        # Scale circle radius based on listing count
        radius_all = 4.5 + 0.35 * np.sqrt(all_cnt)

        # Build popup HTML
        popup_html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; width: 230px; line-height: 1.4;">
            <h4 style="margin:0 0 6px 0; color:#1a202c; border-bottom: 2px solid #e2e8f0; padding-bottom:4px;">{r_name}</h4>
            <div style="font-size: 13px; color: #4a5568;">
                <b>Median Price / sq ft:</b> ₹ {all_sqft:,.0f}<br/>
                <b>Total Listings:</b> {all_cnt}<br/>
                <b>Typical 2 BHK Price:</b> {format_price_display(b2_price)}
            </div>
        </div>
        """

        # 1. Add to ALL layer
        folium.CircleMarker(
            location=[lat, lon],
            radius=radius_all,
            color='#1a202c',
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=0.85,
            tooltip=f"{r_name}: ₹ {all_sqft:,.0f}/sq ft ({all_cnt} listings)",
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(fg_all)

        # 2. Add to 1 BHK layer
        if not pd.isna(row['bhk1_median_price_per_sqft']) and row['bhk1_count'] > 0:
            c1 = int(row['bhk1_count'])
            sqft1 = row['bhk1_median_price_per_sqft']
            popup_1 = f"<b>{r_name} (1 BHK)</b><br/>Median: ₹ {sqft1:,.0f}/sq ft<br/>Listings: {c1}"
            folium.CircleMarker(
                location=[lat, lon],
                radius=4 + 0.35 * np.sqrt(c1),
                color='#1a202c',
                weight=1,
                fill=True,
                fill_color=colormap(sqft1),
                fill_opacity=0.85,
                tooltip=f"{r_name} (1 BHK): ₹ {sqft1:,.0f}/sq ft",
                popup=folium.Popup(popup_1, max_width=250)
            ).add_to(fg_1bhk)

        # 3. Add to 2 BHK layer
        if not pd.isna(row['bhk2_median_price_per_sqft']) and row['bhk2_count'] > 0:
            c2 = int(row['bhk2_count'])
            sqft2 = row['bhk2_median_price_per_sqft']
            popup_2 = f"<b>{r_name} (2 BHK)</b><br/>Median: ₹ {sqft2:,.0f}/sq ft<br/>Listings: {c2}<br/>Typical Price: {format_price_display(b2_price)}"
            folium.CircleMarker(
                location=[lat, lon],
                radius=4 + 0.35 * np.sqrt(c2),
                color='#1a202c',
                weight=1,
                fill=True,
                fill_color=colormap(sqft2),
                fill_opacity=0.85,
                tooltip=f"{r_name} (2 BHK): ₹ {sqft2:,.0f}/sq ft",
                popup=folium.Popup(popup_2, max_width=250)
            ).add_to(fg_2bhk)

        # 4. Add to 3 BHK layer
        if not pd.isna(row['bhk3_median_price_per_sqft']) and row['bhk3_count'] > 0:
            c3 = int(row['bhk3_count'])
            sqft3 = row['bhk3_median_price_per_sqft']
            popup_3 = f"<b>{r_name} (3 BHK)</b><br/>Median: ₹ {sqft3:,.0f}/sq ft<br/>Listings: {c3}"
            folium.CircleMarker(
                location=[lat, lon],
                radius=4 + 0.35 * np.sqrt(c3),
                color='#1a202c',
                weight=1,
                fill=True,
                fill_color=colormap(sqft3),
                fill_opacity=0.85,
                tooltip=f"{r_name} (3 BHK): ₹ {sqft3:,.0f}/sq ft",
                popup=folium.Popup(popup_3, max_width=250)
            ).add_to(fg_3bhk)

    # Add feature groups to map
    fg_all.add_to(mmr_map)
    fg_1bhk.add_to(mmr_map)
    fg_2bhk.add_to(mmr_map)
    fg_3bhk.add_to(mmr_map)

    # Add Colormap Legend
    colormap.add_to(mmr_map)

    # Add Layer Control
    folium.LayerControl(collapsed=False).add_to(mmr_map)

    # Add custom HTML footnote overlay
    footnote_html = """
    <div style="
        position: fixed;
        bottom: 15px; left: 15px;
        z-index: 9999;
        background: rgba(255, 255, 255, 0.92);
        padding: 8px 14px;
        border-radius: 6px;
        border: 1px solid #cbd5e1;
        font-family: sans-serif;
        font-size: 12px;
        color: #334155;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    ">
        Asking prices from listings, median per region. Regions with fewer than 20 listings are hidden.
    </div>
    """
    mmr_map.get_root().html.add_child(folium.Element(footnote_html))

    # Save to HTML file
    mmr_map.save(output_html)
    print(f"\nSuccessfully generated Mumbai Price Map at: {output_html}")

if __name__ == "__main__":
    main()
