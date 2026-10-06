# Mumbai House Price Predictor & Interactive Heat Map

A lightweight web application for predicting Mumbai flat prices using a `HistGradientBoostingRegressor` model, paired with an interactive OpenStreetMap Folium circle map of the Mumbai Metropolitan Region (MMR).

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Train the Model
```bash
python train.py
```

### 3. Generate the Interactive Price Heat Map

Run the three map scripts in exact order:

```bash
# Step 1: Filter dataset, compute regional median price / sqft, and output region_stats.csv
python prep_map_data.py

# Step 2: Geocode regions using OpenStreetMap Nominatim and output region_coords.csv
python geocode_regions.py

# Step 3: Build Folium interactive map and output mumbai_price_map.html
python build_map.py
```

### 4. Run the Web Application
```bash
uvicorn app:app --reload
```

Open your browser and navigate to:
- Valuation App: `http://localhost:8000`
- Interactive Price Map: `http://localhost:8000/map`
