from fastapi import APIRouter, HTTPException
from pathlib import Path
import json

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent / "data"

@router.get("/weather")
async def get_weather():
    """Returns mock weather data for Uttarakhand locations"""
    try:
        with open(DATA_DIR / "weather.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Weather data not found")

@router.get("/crowd")
async def get_crowd():
    """Returns mock crowd level data for tourist spots"""
    try:
        with open(DATA_DIR / "crowd.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Crowd data not found")

@router.get("/festivals")
async def get_festivals():
    """Returns upcoming festivals and cultural events"""
    try:
        with open(DATA_DIR / "festivals.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Festival data not found")

@router.get("/emergency")
async def get_emergency():
    """Returns emergency contacts and medical facilities"""
    try:
        with open(DATA_DIR / "emergency.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Emergency data not found")
