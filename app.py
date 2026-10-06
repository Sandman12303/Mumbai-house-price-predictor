import os
import joblib
import numpy as np
import pandas as pd
from typing import Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.joblib")

if not os.path.exists(MODEL_PATH):
    raise RuntimeError("model.joblib not found. Please run `python train.py` first.")

artifact = joblib.load(MODEL_PATH)
model = artifact['model']
categories_meta = artifact['categories']
region_localities = artifact.get('region_localities', {})
bhk_bounds = artifact['bhk_bounds']
area_bounds = artifact['area_bounds']

app = FastAPI(
    title="Mumbai Apartment Valuation API",
    description="FastAPI machine learning model for Mumbai apartment valuations.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def format_price_display(price_rs: float) -> str:
    """Format price in rupees to human readable Lakhs or Crores."""
    if price_rs >= 1e7:
        cr_val = round(price_rs / 1e7, 2)
        if cr_val == int(cr_val):
            return f"Rs {int(cr_val)} crore"
        return f"Rs {cr_val:.2f} crore"
    else:
        lakh_val = round(price_rs / 1e5, 2)
        lakh_str = f"{lakh_val:.2f}".rstrip('0').rstrip('.')
        return f"Rs {lakh_str} lakh"

class PredictionRequest(BaseModel):
    bhk: int = Field(..., description="Number of bedrooms")
    type: str = Field("Apartment", description="Property type (Apartment only)")
    area: float = Field(..., description="Carpet area in sq ft")
    region: str = Field(..., description="Region / Location area")
    status: str = Field(..., description="Construction status")
    age: str = Field(..., description="Age of property")
    locality: Optional[str] = Field("Other", description="Specific locality")
    years_ahead: Optional[int] = Field(0, ge=0, le=30)
    annual_growth_pct: Optional[float] = Field(5.0, ge=-20.0, le=50.0)

@app.get("/options")
def get_options():
    return {
        "type": ["Apartment"],
        "region": categories_meta["region"],
        "status": categories_meta["status"],
        "age": categories_meta["age"],
        "region_localities": region_localities,
        "bhk_min": bhk_bounds["min"],
        "bhk_max": bhk_bounds["max"],
        "area_min": area_bounds["min"],
        "area_max": area_bounds["max"]
    }

@app.post("/predict")
def predict_price(req: PredictionRequest):
    # Reject type other than Apartment
    if req.type != "Apartment":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid property type '{req.type}'. Only 'Apartment' is supported."
        )

    # Validate region
    if req.region not in categories_meta["region"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown region '{req.region}'. Must be a valid Mumbai region."
        )

    # Validate region-locality relation
    valid_region_locs = region_localities.get(req.region, [])
    if req.locality and req.locality != "Other" and req.locality not in valid_region_locs:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Locality '{req.locality}' is invalid for region '{req.region}'."
        )

    # Validate BHK range
    if req.bhk < bhk_bounds["min"] or req.bhk > bhk_bounds["max"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"bhk must be between {bhk_bounds['min']} and {bhk_bounds['max']}."
        )

    # Validate Area range
    if req.area < area_bounds["min"] or req.area > area_bounds["max"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"area must be between {area_bounds['min']} and {area_bounds['max']} sq ft."
        )

    if req.status not in categories_meta["status"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status '{req.status}'."
        )
    if req.age not in categories_meta["age"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid age '{req.age}'."
        )

    locality_val = req.locality if (req.locality and req.locality in categories_meta["locality"]) else "Other"

    input_dict = {
        'bhk': req.bhk,
        'type': 'Apartment',
        'locality': locality_val,
        'area': req.area,
        'region': req.region,
        'status': req.status,
        'age': req.age
    }
    input_df = pd.DataFrame([input_dict])

    for col in ['type', 'locality', 'region', 'status', 'age']:
        input_df[col] = pd.Categorical(input_df[col], categories=categories_meta[col])

    log_pred = model.predict(input_df)[0]
    base_price_rs = float(np.exp(log_pred))

    is_projection = req.years_ahead is not None and req.years_ahead > 0
    if is_projection:
        growth_multiplier = (1.0 + (req.annual_growth_pct or 5.0) / 100.0) ** req.years_ahead
        final_price_rs = base_price_rs * growth_multiplier
    else:
        final_price_rs = base_price_rs

    low_rs = final_price_rs * 0.8
    high_rs = final_price_rs * 1.2

    return {
        "price_rs": round(final_price_rs, 2),
        "price_lakh": round(final_price_rs / 1e5, 2),
        "price_crore": round(final_price_rs / 1e7, 2),
        "low_rs": round(low_rs, 2),
        "high_rs": round(high_rs, 2),
        "low_display": format_price_display(low_rs),
        "high_display": format_price_display(high_rs),
        "display": format_price_display(final_price_rs),
        "is_projection": is_projection,
        "years_ahead": req.years_ahead or 0,
        "annual_growth_pct": req.annual_growth_pct or 5.0
    }

@app.get("/map")
def read_map():
    map_path = os.path.join(os.path.dirname(__file__), "mumbai_price_map.html")
    if os.path.exists(map_path):
        return FileResponse(map_path)
    return JSONResponse({"message": "Map not generated. Please run `python build_map.py`."})

@app.get("/")
def read_root():
    index_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return JSONResponse({"message": "Mumbai Apartment Valuation API running."})
