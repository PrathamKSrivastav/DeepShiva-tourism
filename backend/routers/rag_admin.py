from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict, Any
import tempfile
from pathlib import Path
import logging
from rag.content_manager import ContentManager
from rag.vector_store import get_vector_store
from routers.auth import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()

# Shared singleton — same instance as main.py and groq_service.
# Previously this module instantiated VectorStoreManager() with no args,
# which dropped Qdrant creds and forced admin endpoints to an empty Chroma.
vector_store = get_vector_store()
content_manager = ContentManager(vector_store)

class WebPageRequest(BaseModel):
    url: HttpUrl
    content_type: Optional[str] = None

class TextContentRequest(BaseModel):
    title: str
    content: str
    content_type: Optional[str] = None

class BatchProcessRequest(BaseModel):
    directory_path: str
    content_type: Optional[str] = None

class RemoveContentRequest(BaseModel):
    identifier: str
    identifier_type: str = "file"  # "file" or "url"

@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    content_type: Optional[str] = Form(None),
    _admin: dict = Depends(require_admin),
):
    """Upload and process PDF file"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        
        try:
            # Process the PDF
            result = await content_manager.add_pdf_file(temp_path, content_type)
            
            # Clean up temp file
            temp_path.unlink()
            
            if result["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "message": "PDF uploaded and processed successfully",
                        "filename": result["filename"],
                        "chunks_count": result["chunks_count"],
                        "collection": result["collection"],
                        "document_ids": result["document_ids"]
                    }
                )
            else:
                raise HTTPException(status_code=400, detail=result["error"])
                
        finally:
            # Ensure temp file is cleaned up
            if temp_path.exists():
                temp_path.unlink()
        
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.post("/add-webpage")
async def add_web_page(request: WebPageRequest, _admin: dict = Depends(require_admin)):
    """Add web page to RAG system"""
    try:
        result = await content_manager.add_web_page(str(request.url), request.content_type)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Web page added successfully",
                    "url": result["url"],
                    "title": result["title"],
                    "chunks_count": result["chunks_count"],
                    "collection": result["collection"],
                    "document_ids": result["document_ids"]
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error adding web page: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding web page: {str(e)}")

@router.post("/add-text-content")
async def add_text_content(request: TextContentRequest, _admin: dict = Depends(require_admin)):
    """Add raw text content to RAG system"""
    try:
        result = await content_manager.add_text_content(
            request.content, 
            request.title, 
            request.content_type
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Text content added successfully",
                    "title": result["title"],
                    "filename": result["filename"],
                    "chunks_count": result["chunks_count"],
                    "collection": result["collection"],
                    "document_ids": result["document_ids"]
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error adding text content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error adding text content: {str(e)}")

@router.post("/batch-process")
async def batch_process_directory(request: BatchProcessRequest, _admin: dict = Depends(require_admin)):
    """Batch process files from directory"""
    try:
        directory_path = Path(request.directory_path)
        
        if not directory_path.exists():
            raise HTTPException(status_code=400, detail="Directory not found")
        
        result = await content_manager.batch_process_directory(directory_path, request.content_type)
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Batch processing completed",
                    "processed_files": result["processed_files"],
                    "failed_files": result["failed_files"],
                    "total_chunks": result["total_chunks"],
                    "processing_time": result["processing_time"]
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in batch processing: {str(e)}")

@router.get("/content-stats")
async def get_content_statistics():
    """Get comprehensive content statistics"""
    try:
        stats = content_manager.get_content_statistics()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return JSONResponse(status_code=200, content=stats)
        
    except Exception as e:
        logger.error(f"Error getting content statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")

@router.get("/collections")
async def get_collections():
    """Get vector store collection information"""
    try:
        collection_stats = vector_store.get_all_stats()
        
        return JSONResponse(
            status_code=200,
            content={
                "collections": collection_stats,
                "total_collections": len(collection_stats)
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting collections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting collections: {str(e)}")

@router.post("/test-search")
async def test_search(query: str, collection_names: Optional[List[str]] = None, n_results: int = 5):
    """Test search functionality"""
    try:
        results = vector_store.search_documents(
            query=query,
            collection_names=collection_names,
            n_results=n_results
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "query": query,
                "results": results,
                "total_results": sum(len(docs) for docs in results.values())
            }
        )
        
    except Exception as e:
        logger.error(f"Error in test search: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in search: {str(e)}")

@router.delete("/remove-content")
async def remove_content(request: RemoveContentRequest, _admin: dict = Depends(require_admin)):
    """Remove content from RAG system"""
    try:
        result = await content_manager.remove_content(
            request.identifier, 
            request.identifier_type
        )
        
        if result["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "message": result["message"],
                    "identifier": request.identifier,
                    "type": request.identifier_type
                }
            )
        else:
            raise HTTPException(status_code=400, detail=result["error"])
            
    except Exception as e:
        logger.error(f"Error removing content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error removing content: {str(e)}")

@router.delete("/clear-collection")
async def clear_collection(collection_name: str, _admin: dict = Depends(require_admin)):
    """Clear all documents from a collection"""
    try:
        success = vector_store.clear_collection(collection_name)
        
        if success:
            return JSONResponse(
                status_code=200,
                content={
                    "message": f"Collection '{collection_name}' cleared successfully",
                    "collection": collection_name
                }
            )
        else:
            raise HTTPException(status_code=400, detail=f"Failed to clear collection '{collection_name}'")
            
    except Exception as e:
        logger.error(f"Error clearing collection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing collection: {str(e)}")

@router.get("/health")
async def rag_health_check():
    """Check RAG system health"""
    try:
        # Check vector store
        collection_stats = vector_store.get_all_stats()
        total_docs = sum(stats.get('document_count', 0) for stats in collection_stats.values() if isinstance(stats, dict))
        
        # Check content manager
        content_stats = content_manager.get_content_statistics()
        
        health_status = {
            "status": "healthy" if total_docs > 0 else "no_content",
            "vector_store": {
                "collections": len(collection_stats),
                "total_documents": total_docs,
                "collections_detail": collection_stats
            },
            "content_manager": {
                "total_files": content_stats.get("total_files", 0),
                "total_urls": content_stats.get("total_urls", 0),
                "last_updated": content_stats.get("last_updated", "Never")
            },
            "timestamp": content_manager.content_registry.get("last_updated", "Never")
        }
        
        return JSONResponse(status_code=200, content=health_status)
        
    except Exception as e:
        logger.error(f"Error in RAG health check: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error checking RAG health: {str(e)}")

@router.get("/supported-content-types")
async def get_supported_content_types():
    """Get list of supported content types"""
    return JSONResponse(
        status_code=200,
        content={
            "content_types": [
                {
                    "id": "general",
                    "name": "General Tourism",
                    "description": "General tourism information, travel guides, basic information"
                },
                {
                    "id": "spiritual",
                    "name": "Spiritual & Religious",
                    "description": "Temple information, spiritual significance, religious practices"
                },
                {
                    "id": "trekking",
                    "name": "Trekking & Adventure",
                    "description": "Trek routes, adventure activities, safety information"
                },
                {
                    "id": "cultural",
                    "name": "Cultural & Heritage",
                    "description": "Cultural traditions, festivals, historical information"
                },
                {
                    "id": "government",
                    "name": "Government & Official",
                    "description": "Official policies, regulations, government communications"
                }
            ],
            "default": "general"
        }
    )
