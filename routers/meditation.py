"""
Meditation API Router
Provides endpoints for guided meditation courses and chapters
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

# Path to meditation data
MEDITATION_DATA_DIR = Path(__file__).parent.parent / "data" / "meditation"
COURSES_FILE = MEDITATION_DATA_DIR / "courses.json"
CHAPTERS_DIR = MEDITATION_DATA_DIR / "chapters"


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """Load and parse JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"Data file not found: {file_path.name}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Invalid JSON data")
    except Exception as e:
        logger.error(f"Error loading {file_path}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error loading data")


@router.get("/meditation/courses")
async def get_all_courses():
    """
    Get all available meditation courses
    
    Returns:
        {
            "courses": [
                {
                    "id": "temple_prep",
                    "title": "Temple Visit Preparation",
                    "type": "spiritual",
                    "duration": 10,
                    "difficulty": "beginner",
                    "description": "...",
                    "icon": "🕉️",
                    "benefits": [...],
                    "chapter_count": 4
                },
                ...
            ]
        }
    """
    try:
        logger.info("📚 Fetching all meditation courses")
        courses_data = load_json_file(COURSES_FILE)
        
        # Remove internal fields that frontend doesn't need
        courses = courses_data.get("courses", [])
        for course in courses:
            course.pop("chapters_file", None)
        
        logger.info(f"✅ Returning {len(courses)} meditation courses")
        return {
            "courses": courses,
            "total": len(courses)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching courses: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch meditation courses")


@router.get("/meditation/courses/{course_id}")
async def get_course_details(course_id: str):
    """
    Get detailed information about a specific course including all chapters
    
    Args:
        course_id: Course identifier (e.g., "temple_prep", "mountain_peace")
    
    Returns:
        {
            "course_id": "temple_prep",
            "course_title": "Temple Visit Preparation",
            "total_duration": 10,
            "chapters": [
                {
                    "id": 1,
                    "title": "Welcome & Setup",
                    "duration": 2,
                    "script_preview": "Namaste. Welcome to..."
                },
                ...
            ]
        }
    """
    try:
        logger.info(f"📖 Fetching course details: {course_id}")
        
        # Load courses to verify course exists
        courses_data = load_json_file(COURSES_FILE)
        course = next(
            (c for c in courses_data.get("courses", []) if c["id"] == course_id),
            None
        )
        
        if not course:
            logger.warning(f"⚠️ Course not found: {course_id}")
            raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
        
        # Load chapter data
        chapters_file = CHAPTERS_DIR / course["chapters_file"]
        chapters_data = load_json_file(chapters_file)
        
        # Create chapter summaries (without full scripts for performance)
        chapter_summaries = []
        for chapter in chapters_data.get("chapters", []):
            # Get first line of script as preview
            script_preview = ""
            if chapter.get("script") and len(chapter["script"]) > 0:
                script_preview = chapter["script"][0].get("text", "")
            
            chapter_summaries.append({
                "id": chapter["id"],
                "title": chapter["title"],
                "duration": chapter["duration"],
                "script_preview": script_preview[:100] + "..." if len(script_preview) > 100 else script_preview
            })
        
        logger.info(f"✅ Returning course '{course_id}' with {len(chapter_summaries)} chapters")
        
        return {
            "course_id": chapters_data["course_id"],
            "course_title": chapters_data["course_title"],
            "total_duration": chapters_data["total_duration"],
            "course_info": {
                "type": course["type"],
                "difficulty": course["difficulty"],
                "description": course["description"],
                "image": course["image"],
                "benefits": course["benefits"]
            },
            "chapters": chapter_summaries,
            "chapter_count": len(chapter_summaries)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching course details: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch course details")


@router.get("/meditation/courses/{course_id}/chapters/{chapter_id}")
async def get_chapter_script(course_id: str, chapter_id: int):
    """
    Get full script for a specific chapter (for playback)
    
    Args:
        course_id: Course identifier
        chapter_id: Chapter number (1, 2, 3, 4)
    
    Returns:
        {
            "course_id": "temple_prep",
            "chapter": {
                "id": 1,
                "title": "Welcome & Setup",
                "duration": 2,
                "background_music": "https://...",
                "script": [
                    {
                        "text": "Namaste. Welcome...",
                        "pause": 2,
                        "instruction": "breathe_in"
                    },
                    ...
                ]
            }
        }
    """
    try:
        logger.info(f"📜 Fetching chapter script: {course_id} - Chapter {chapter_id}")
        
        # Load courses to get chapters file
        courses_data = load_json_file(COURSES_FILE)
        course = next(
            (c for c in courses_data.get("courses", []) if c["id"] == course_id),
            None
        )
        
        if not course:
            logger.warning(f"⚠️ Course not found: {course_id}")
            raise HTTPException(status_code=404, detail=f"Course '{course_id}' not found")
        
        # Load chapters
        chapters_file = CHAPTERS_DIR / course["chapters_file"]
        chapters_data = load_json_file(chapters_file)
        
        # Find specific chapter
        chapter = next(
            (ch for ch in chapters_data.get("chapters", []) if ch["id"] == chapter_id),
            None
        )
        
        if not chapter:
            logger.warning(f"⚠️ Chapter not found: {course_id} - Chapter {chapter_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Chapter {chapter_id} not found in course '{course_id}'"
            )
        
        logger.info(f"✅ Returning chapter {chapter_id} script ({len(chapter.get('script', []))} segments)")
        
        return {
            "course_id": course_id,
            "course_title": chapters_data["course_title"],
            "chapter": chapter
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching chapter script: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch chapter script")


@router.get("/meditation/health")
async def meditation_health_check():
    """
    Health check endpoint for meditation system
    Verifies all data files exist and are readable
    """
    try:
        status = {
            "status": "healthy",
            "data_directory": str(MEDITATION_DATA_DIR),
            "files_status": {}
        }
        
        # Check courses file
        if COURSES_FILE.exists():
            courses_data = load_json_file(COURSES_FILE)
            status["files_status"]["courses.json"] = {
                "exists": True,
                "course_count": len(courses_data.get("courses", []))
            }
        else:
            status["files_status"]["courses.json"] = {"exists": False}
            status["status"] = "unhealthy"
        
        # Check chapter files
        for chapter_file in ["temple_prep.json", "mountain_peace.json", "chakra_journey.json"]:
            file_path = CHAPTERS_DIR / chapter_file
            if file_path.exists():
                chapter_data = load_json_file(file_path)
                status["files_status"][chapter_file] = {
                    "exists": True,
                    "chapter_count": len(chapter_data.get("chapters", []))
                }
            else:
                status["files_status"][chapter_file] = {"exists": False}
                status["status"] = "unhealthy"
        
        return status
    
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
