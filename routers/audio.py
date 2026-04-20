# """
# Audio Chat Endpoints
# Handles audio file upload, transcription, and chat response
# """

# from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
# from typing import Optional
# import logging
# import tempfile
# import os
# from datetime import datetime

# from utils.audio_processor import get_audio_processor
# from utils.groq_service import GroqService
# from utils.database import get_database
# from middleware.auth import get_current_user
# from pydantic import BaseModel

# logger = logging.getLogger(__name__)

# router = APIRouter()

# # Initialize services
# audio_processor = get_audio_processor()
# groq_service = GroqService()


# class AudioChatResponse(BaseModel):
#     """Response for audio chat"""
#     transcription: str
#     detected_language: str
#     response: str
#     response_mode: str  # "english" or "hinglish"
#     persona: str
#     session_id: Optional[str] = None


# @router.post("/chat/audio", response_model=AudioChatResponse)
# async def chat_with_audio(
#     audio: UploadFile = File(...),
#     persona: str = Form("local_guide"),
#     session_id: Optional[str] = Form(None),
#     current_user: Optional[dict] = Depends(get_current_user)
# ):
#     """
#     Process audio input and return text response
    
#     Flow:
#     1. Receive audio file
#     2. Transcribe to text (faster-whisper)
#     3. Detect language (en/hi)
#     4. Send to Groq API with appropriate prompt
#     5. Return response (English or Hinglish)
#     """
#     temp_audio_path = None
    
#     try:
#         logger.info("=" * 70)
#         logger.info("🎤 AUDIO CHAT REQUEST RECEIVED")
#         logger.info(f"   Persona: {persona}")
#         logger.info(f"   Session ID: {session_id}")
#         logger.info(f"   File: {audio.filename}")
#         logger.info(f"   Content Type: {audio.content_type}")
        
#         # Validate audio file
#         if not audio.content_type.startswith("audio/"):
#             raise HTTPException(
#                 status_code=400,
#                 detail="Invalid file type. Please upload an audio file."
#             )
        
#         # Save uploaded audio temporarily
#         suffix = os.path.splitext(audio.filename)[1] or ".webm"
#         with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
#             temp_audio_path = temp_file.name
#             content = await audio.read()
#             temp_file.write(content)
        
#         logger.info(f"✅ Audio saved temporarily: {temp_audio_path}")
#         logger.info(f"   File size: {len(content)} bytes")
        
#         # Step 1: Transcribe audio to text
#         transcription_result = await audio_processor.transcribe_audio(
#             temp_audio_path,
#             detect_language=True
#         )
        
#         transcription_text = transcription_result["transcription"]
#         detected_language = transcription_result["detected_language"]
        
#         if not transcription_text or len(transcription_text.strip()) < 2:
#             raise HTTPException(
#                 status_code=400,
#                 detail="Could not transcribe audio. Please speak clearly and try again."
#             )
        
#         logger.info(f"✅ Transcription: '{transcription_text}'")
#         logger.info(f"✅ Detected Language: {detected_language}")
        
#         # Step 2: Determine response mode
#         response_mode = "hinglish" if detected_language == "hi" else "english"
#         logger.info(f"📝 Response mode: {response_mode}")
        
#         # Step 3: Get chat response from Groq
#         # Import the chat logic from chat.py
#         from routers.chat import groq_service, classify_intent
        
#         intent = classify_intent(transcription_text)
        
#         # Get RAG context
#         rag_context = {"has_rag_context": False}
#         if groq_service.persona_rag:
#             try:
#                 rag_context = await groq_service._get_rag_context(
#                     transcription_text,
#                     persona,
#                     intent,
#                     {}
#                 )
#             except Exception as e:
#                 logger.warning(f"⚠️ RAG failed: {str(e)}")
        
#         # Modify system prompt based on response mode
#         if response_mode == "hinglish":
#             # Add Hinglish instruction to context
#             rag_context["response_language"] = "hinglish"
        
#         # Generate response
#         result = await groq_service.generate_persona_response(
#             message=transcription_text,
#             persona=persona,
#             intent=intent,
#             context={"response_mode": response_mode},
#             tool_context={},
#             conversation_history=[],
#             tools=None,  # Simplified for audio (no tools for now)
#             rag_context=rag_context
#         )
        
#         response_text = result.get("response", "I couldn't generate a response.")
        
#         logger.info(f"✅ Response generated ({response_mode}): {response_text[:100]}...")
        
#         # Step 4: Save to database if authenticated
#         if current_user and session_id:
#             try:
#                 db = get_database()
#                 user_id = str(current_user.get("_id") or current_user.get("id"))
                
#                 await db.chats.update_one(
#                     {"_id": session_id, "user_id": user_id},
#                     {
#                         "$push": {
#                             "messages": {
#                                 "$each": [
#                                     {
#                                         "role": "user",
#                                         "content": transcription_text,
#                                         "persona": persona,
#                                         "timestamp": datetime.utcnow(),
#                                         "audio_input": True,
#                                         "detected_language": detected_language
#                                     },
#                                     {
#                                         "role": "assistant",
#                                         "content": response_text,
#                                         "persona": persona,
#                                         "timestamp": datetime.utcnow(),
#                                         "response_mode": response_mode
#                                     }
#                                 ]
#                             }
#                         },
#                         "$set": {"updated_at": datetime.utcnow()}
#                     }
#                 )
#                 logger.info(f"✅ Audio chat saved to session: {session_id}")
#             except Exception as e:
#                 logger.warning(f"⚠️ Failed to save audio chat: {str(e)}")
        
#         return AudioChatResponse(
#             transcription=transcription_text,
#             detected_language=detected_language,
#             response=response_text,
#             response_mode=response_mode,
#             persona=persona,
#             session_id=session_id
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"❌ Audio chat error: {str(e)}")
#         logger.exception("Full traceback:")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Audio processing failed: {str(e)}"
#         )
#     finally:
#         # Cleanup temporary file
#         if temp_audio_path and os.path.exists(temp_audio_path):
#             try:
#                 os.remove(temp_audio_path)
#                 logger.info(f"🧹 Cleaned up temp file: {temp_audio_path}")
#             except:
#                 pass


# @router.get("/audio/test")
# async def test_audio_system():
#     """Test endpoint to check if audio system is working"""
#     try:
#         processor = get_audio_processor()
#         return {
#             "status": "ok",
#             "model_loaded": processor.model is not None,
#             "message": "Audio system is ready"
#         }
#     except Exception as e:
#         return {
#             "status": "error",
#             "message": str(e)
#         }
# routers/audio.py

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Form
from typing import Optional
import logging
import tempfile
import os
from pydantic import BaseModel

from utils.audio_processor import get_audio_processor
from middleware.auth import get_current_user

# 🟢 IMPORT THE CHAT ROUTE & REQUEST MODEL
from routers.chat import chat, ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter()
audio_processor = get_audio_processor()

class AudioChatResponse(BaseModel):
    transcription: str
    detected_language: str
    response: str
    response_mode: str
    persona: str
    session_id: Optional[str] = None

@router.post("/chat/audio", response_model=AudioChatResponse)
async def chat_with_audio(
    audio: UploadFile = File(...),
    persona: str = Form("local_guide"),
    session_id: Optional[str] = Form(None),
    current_user: Optional[dict] = Depends(get_current_user)
):
    temp_audio_path = None
    try:
        # ... (Audio save/transcribe logic stays same) ...
        
        # Save temp file
        suffix = os.path.splitext(audio.filename)[1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_audio_path = temp_file.name
            content = await audio.read()
            temp_file.write(content)
            
        # Transcribe
        transcription_result = await audio_processor.transcribe_audio(temp_audio_path, detect_language=True)
        text = transcription_result["transcription"]
        lang = transcription_result["detected_language"]
        
        if not text or len(text.strip()) < 2:
            raise HTTPException(status_code=400, detail="No speech detected.")

        logger.info(f"✅ Transcription: '{text}'")

        # 🟢 CALL CHAT ENDPOINT DIRECTLY
        # We construct the Pydantic model just like a frontend would
        chat_request = ChatRequest(
            message=text,
            session_id=session_id,
            persona=persona,
            use_rag=True,
            context={"response_mode": "hinglish" if lang == "hi" else "english"}
        )
        
        # Call the existing chat function logic
        chat_response = await chat(
            request=chat_request,
            current_user=current_user
        )
        
        return AudioChatResponse(
            transcription=text,
            detected_language=lang,
            response=chat_response.response, # Extract text from ChatResponse
            response_mode="hinglish" if lang == "hi" else "english",
            persona=persona,
            session_id=chat_response.session_id or session_id
        )

    except Exception as e:
        logger.error(f"Audio Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_audio_path and os.path.exists(temp_audio_path):
            try: os.remove(temp_audio_path)
            except: pass
