from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional
import logging
from datetime import datetime

from tools.holiday_tool import get_holidays, get_next_holidays

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/holidays/upcoming")
async def get_upcoming_holidays(
    limit: int = Query(
        default=3, ge=1, le=10, description="Number of upcoming holidays to return"
    )
):
    """
    Get the next N upcoming holidays from today's date

    Args:
        limit: Number of holidays to return (1-10, default: 3)

    Returns:
        List of upcoming holidays with details

    Example:
        GET /api/holidays/upcoming?limit=3
    """
    try:
        logger.info(f"📅 Fetching next {limit} upcoming holidays")

        holidays = await get_next_holidays(limit=limit)

        if not holidays:
            return {
                "success": False,
                "count": 0,
                "holidays": [],
                "message": "No upcoming holidays found",
            }

        # Format response
        formatted_holidays = []
        for h in holidays:
            formatted_holidays.append(
                {
                    "name": h.get("name", "Unknown"),
                    "date": h.get("date", {}).get("iso", "Unknown"),
                    "type": h.get("primary_type", "Holiday"),
                    "description": h.get("description", ""),
                    "day_of_week": _get_day_of_week(h.get("date", {}).get("iso")),
                    "days_until": _calculate_days_until(h.get("date", {}).get("iso")),
                }
            )

        logger.info(f"✅ Returning {len(formatted_holidays)} upcoming holidays")

        return {
            "success": True,
            "count": len(formatted_holidays),
            "holidays": formatted_holidays,
            "fetched_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Error fetching upcoming holidays: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching holidays: {str(e)}"
        )


@router.get("/holidays/year/{year}")
async def get_holidays_by_year(
    year: int,
    month: Optional[int] = Query(default=None, ge=1, le=12),
    quarter: Optional[int] = Query(default=None, ge=1, le=4),
):
    """
    Get holidays for a specific year, optionally filtered by month or quarter

    Args:
        year: Year (e.g., 2025)
        month: Optional month (1-12)
        quarter: Optional quarter (1-4)

    Returns:
        List of holidays for the specified period

    Example:
        GET /api/holidays/year/2025?quarter=1
    """
    try:
        logger.info(
            f"📅 Fetching holidays for year {year}, month={month}, quarter={quarter}"
        )

        holidays = await get_holidays(year=year, month=month, quarter=quarter)

        if not holidays:
            return {
                "success": False,
                "year": year,
                "month": month,
                "quarter": quarter,
                "count": 0,
                "holidays": [],
            }

        # Format response
        formatted_holidays = []
        for h in holidays:
            formatted_holidays.append(
                {
                    "name": h.get("name", "Unknown"),
                    "date": h.get("date", {}).get("iso", "Unknown"),
                    "type": h.get("primary_type", "Holiday"),
                    "description": h.get("description", ""),
                    "day_of_week": _get_day_of_week(h.get("date", {}).get("iso")),
                }
            )

        logger.info(f"✅ Returning {len(formatted_holidays)} holidays")

        return {
            "success": True,
            "year": year,
            "month": month,
            "quarter": quarter,
            "count": len(formatted_holidays),
            "holidays": formatted_holidays,
        }

    except Exception as e:
        logger.error(f"❌ Error fetching holidays: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error fetching holidays: {str(e)}"
        )


# Helper functions


def _get_day_of_week(date_str: str) -> str:
    """Get day of week from ISO date string"""
    try:
        date_obj = datetime.fromisoformat(date_str)
        return date_obj.strftime("%A")
    except:
        return "Unknown"


def _calculate_days_until(date_str: str) -> int:
    """Calculate days until the holiday"""
    try:
        holiday_date = datetime.fromisoformat(date_str).date()
        today = datetime.now().date()
        delta = (holiday_date - today).days
        return max(0, delta)  # Return 0 if holiday is today or past
    except:
        return -1
