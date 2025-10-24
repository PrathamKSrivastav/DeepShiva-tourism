import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
import shutil
from datetime import datetime
from .document_processor import DocumentProcessor
from .vector_store import VectorStoreManager
import json

logger = logging.getLogger(__name__)

class ContentManager:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.document_processor = DocumentProcessor()
        
        # Content storage paths
        self.base_path = Path("data/rag_content")
        self.paths = {
            "pdfs": self.base_path / "pdfs",
            "web_pages": self.base_path / "web_pages", 
            "texts": self.base_path / "texts",
            "processed": self.base_path / "processed",
            "metadata": self.base_path / "metadata"
        }
        
        # Create directories
        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)
        
        # Content tracking
        self.content_registry_path = self.paths["metadata"] / "content_registry.json"
        self.content_registry = self._load_content_registry()
    
    def _load_content_registry(self) -> Dict[str, Any]:
        """Load content registry from file"""
        if self.content_registry_path.exists():
            try:
                with open(self.content_registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading content registry: {str(e)}")
        
        return {
            "files": {},
            "urls": {},
            "last_updated": datetime.now().isoformat(),
            "total_documents": 0,
            "processing_history": []
        }
    
    def _save_content_registry(self):
        """Save content registry to file"""
        try:
            self.content_registry["last_updated"] = datetime.now().isoformat()
            with open(self.content_registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.content_registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving content registry: {str(e)}")
    
    async def add_pdf_file(self, file_path: Path, content_type: str = None) -> Dict[str, Any]:
        """Add PDF file to RAG system"""
        try:
            # Copy file to managed location
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
            managed_path = self.paths["pdfs"] / filename
            shutil.copy2(file_path, managed_path)
            
            # Process document
            chunks, metadata_list = self.document_processor.process_pdf(managed_path)
            
            if not chunks:
                logger.warning(f"No content extracted from PDF: {file_path}")
                return {"success": False, "error": "No content extracted"}
            
            # Override content type if specified
            if content_type:
                for metadata in metadata_list:
                    metadata["content_type"] = content_type
            
            # Determine target collection
            collection_name = metadata_list[0]["content_type"] if metadata_list else "general"
            
            # Add to vector store
            doc_ids = self.vector_store.add_documents(
                documents=chunks,
                metadatas=metadata_list,
                collection_name=collection_name
            )
            
            # Update registry
            file_info = {
                "original_path": str(file_path),
                "managed_path": str(managed_path),
                "chunks_count": len(chunks),
                "collection": collection_name,
                "document_ids": doc_ids,
                "added_at": datetime.now().isoformat(),
                "file_size": managed_path.stat().st_size,
                "content_type": collection_name
            }
            
            self.content_registry["files"][str(managed_path)] = file_info
            self.content_registry["total_documents"] += len(chunks)
            self.content_registry["processing_history"].append({
                "action": "add_pdf",
                "file": filename,
                "chunks": len(chunks),
                "timestamp": datetime.now().isoformat()
            })
            
            self._save_content_registry()
            
            logger.info(f"Added PDF {filename}: {len(chunks)} chunks to {collection_name}")
            
            return {
                "success": True,
                "filename": filename,
                "chunks_count": len(chunks),
                "collection": collection_name,
                "document_ids": doc_ids
            }
            
        except Exception as e:
            logger.error(f"Error adding PDF file {file_path}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def add_web_page(self, url: str, content_type: str = None) -> Dict[str, Any]:
        """Add web page to RAG system"""
        try:
            # Process web page
            chunks, metadata_list = self.document_processor.process_web_page(url)
            
            if not chunks:
                logger.warning(f"No content extracted from URL: {url}")
                return {"success": False, "error": "No content extracted"}
            
            # Override content type if specified
            if content_type:
                for metadata in metadata_list:
                    metadata["content_type"] = content_type
            
            # Determine target collection
            collection_name = metadata_list[0]["content_type"] if metadata_list else "general"
            
            # Add to vector store
            doc_ids = self.vector_store.add_documents(
                documents=chunks,
                metadatas=metadata_list,
                collection_name=collection_name
            )
            
            # Save web page content for future reference
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"webpage_{timestamp}_{url.replace('/', '_').replace(':', '')[:50]}.txt"
            content_file = self.paths["web_pages"] / filename
            
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(f"URL: {url}\n")
                f.write(f"Processed: {datetime.now().isoformat()}\n")
                f.write(f"Title: {metadata_list[0].get('title', 'Unknown') if metadata_list else 'Unknown'}\n")
                f.write("\n" + "="*50 + "\n\n")
                f.write("\n\n".join(chunks))
            
            # Update registry
            url_info = {
                "url": url,
                "saved_content": str(content_file),
                "chunks_count": len(chunks),
                "collection": collection_name,
                "document_ids": doc_ids,
                "added_at": datetime.now().isoformat(),
                "title": metadata_list[0].get('title', 'Unknown') if metadata_list else 'Unknown',
                "content_type": collection_name
            }
            
            self.content_registry["urls"][url] = url_info
            self.content_registry["total_documents"] += len(chunks)
            self.content_registry["processing_history"].append({
                "action": "add_webpage",
                "url": url,
                "chunks": len(chunks),
                "timestamp": datetime.now().isoformat()
            })
            
            self._save_content_registry()
            
            logger.info(f"Added web page {url}: {len(chunks)} chunks to {collection_name}")
            
            return {
                "success": True,
                "url": url,
                "chunks_count": len(chunks),
                "collection": collection_name,
                "document_ids": doc_ids,
                "title": url_info["title"]
            }
            
        except Exception as e:
            logger.error(f"Error adding web page {url}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def add_text_content(self, content: str, title: str, content_type: str = None) -> Dict[str, Any]:
        """Add raw text content to RAG system"""
        try:
            # Save text content to file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"text_{timestamp}_{title.replace(' ', '_')[:30]}.txt"
            text_file = self.paths["texts"] / filename
            
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n")
                f.write(f"Added: {datetime.now().isoformat()}\n")
                f.write("\n" + "="*50 + "\n\n")
                f.write(content)
            
            # Process text
            chunks, metadata_list = self.document_processor.process_text_file(text_file)
            
            if not chunks:
                logger.warning(f"No content extracted from text: {title}")
                return {"success": False, "error": "No content extracted"}
            
            # Override content type if specified
            if content_type:
                for metadata in metadata_list:
                    metadata["content_type"] = content_type
                    metadata["title"] = title
            
            # Determine target collection
            collection_name = content_type or (metadata_list[0]["content_type"] if metadata_list else "general")
            
            # Add to vector store
            doc_ids = self.vector_store.add_documents(
                documents=chunks,
                metadatas=metadata_list,
                collection_name=collection_name
            )
            
            # Update registry
            text_info = {
                "title": title,
                "file_path": str(text_file),
                "chunks_count": len(chunks),
                "collection": collection_name,
                "document_ids": doc_ids,
                "added_at": datetime.now().isoformat(),
                "content_length": len(content),
                "content_type": collection_name
            }
            
            self.content_registry["files"][str(text_file)] = text_info
            self.content_registry["total_documents"] += len(chunks)
            self.content_registry["processing_history"].append({
                "action": "add_text",
                "title": title,
                "chunks": len(chunks),
                "timestamp": datetime.now().isoformat()
            })
            
            self._save_content_registry()
            
            logger.info(f"Added text content '{title}': {len(chunks)} chunks to {collection_name}")
            
            return {
                "success": True,
                "title": title,
                "filename": filename,
                "chunks_count": len(chunks),
                "collection": collection_name,
                "document_ids": doc_ids
            }
            
        except Exception as e:
            logger.error(f"Error adding text content '{title}': {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def batch_process_directory(self, directory_path: Path, content_type: str = None) -> Dict[str, Any]:
        """Batch process all files in a directory"""
        try:
            results = {
                "processed_files": [],
                "failed_files": [],
                "total_chunks": 0,
                "processing_time": None
            }
            
            start_time = datetime.now()
            
            directory = Path(directory_path)
            if not directory.exists():
                return {"success": False, "error": "Directory not found"}
            
            # Get all supported files
            supported_extensions = ['.pdf', '.txt', '.md']
            files = [
                f for f in directory.rglob('*') 
                if f.is_file() and f.suffix.lower() in supported_extensions
            ]
            
            for file_path in files:
                try:
                    if file_path.suffix.lower() == '.pdf':
                        result = await self.add_pdf_file(file_path, content_type)
                    else:
                        # For text files, use filename as title
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        result = await self.add_text_content(content, file_path.stem, content_type)
                    
                    if result["success"]:
                        results["processed_files"].append({
                            "file": str(file_path),
                            "chunks": result["chunks_count"],
                            "collection": result["collection"]
                        })
                        results["total_chunks"] += result["chunks_count"]
                    else:
                        results["failed_files"].append({
                            "file": str(file_path),
                            "error": result.get("error", "Unknown error")
                        })
                        
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    results["failed_files"].append({
                        "file": str(file_path),
                        "error": str(e)
                    })
            
            end_time = datetime.now()
            results["processing_time"] = str(end_time - start_time)
            
            logger.info(f"Batch processed {len(results['processed_files'])} files, {results['total_chunks']} total chunks")
            
            return {"success": True, **results}
            
        except Exception as e:
            logger.error(f"Error in batch processing: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """Get comprehensive content statistics"""
        try:
            vector_stats = self.vector_store.get_collection_stats()
            
            stats = {
                "total_files": len(self.content_registry.get("files", {})),
                "total_urls": len(self.content_registry.get("urls", {})),
                "total_documents": self.content_registry.get("total_documents", 0),
                "collections": vector_stats,
                "processing_history": self.content_registry.get("processing_history", [])[-10:],  # Last 10 entries
                "last_updated": self.content_registry.get("last_updated", "Never"),
                "storage_paths": {k: str(v) for k, v in self.paths.items()},
                "content_types_distribution": {}
            }
            
            # Calculate content type distribution
            for file_info in self.content_registry.get("files", {}).values():
                content_type = file_info.get("content_type", "general")
                stats["content_types_distribution"][content_type] = \
                    stats["content_types_distribution"].get(content_type, 0) + file_info.get("chunks_count", 0)
            
            for url_info in self.content_registry.get("urls", {}).values():
                content_type = url_info.get("content_type", "general")
                stats["content_types_distribution"][content_type] = \
                    stats["content_types_distribution"].get(content_type, 0) + url_info.get("chunks_count", 0)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting content statistics: {str(e)}")
            return {"error": str(e)}
    
    async def remove_content(self, identifier: str, identifier_type: str = "file") -> Dict[str, Any]:
        """Remove content from RAG system"""
        try:
            if identifier_type == "file":
                if identifier not in self.content_registry.get("files", {}):
                    return {"success": False, "error": "File not found in registry"}
                
                file_info = self.content_registry["files"][identifier]
                doc_ids = file_info.get("document_ids", [])
                collection = file_info.get("collection", "general")
                
                # Remove from vector store
                if doc_ids:
                    self.vector_store.delete_documents(doc_ids, collection)
                
                # Remove file
                file_path = Path(identifier)
                if file_path.exists():
                    file_path.unlink()
                
                # Update registry
                del self.content_registry["files"][identifier]
                
            elif identifier_type == "url":
                if identifier not in self.content_registry.get("urls", {}):
                    return {"success": False, "error": "URL not found in registry"}
                
                url_info = self.content_registry["urls"][identifier]
                doc_ids = url_info.get("document_ids", [])
                collection = url_info.get("collection", "general")
                
                # Remove from vector store
                if doc_ids:
                    self.vector_store.delete_documents(doc_ids, collection)
                
                # Remove saved content file
                content_file = Path(url_info.get("saved_content", ""))
                if content_file.exists():
                    content_file.unlink()
                
                # Update registry
                del self.content_registry["urls"][identifier]
            
            self.content_registry["processing_history"].append({
                "action": "remove_content",
                "identifier": identifier,
                "type": identifier_type,
                "timestamp": datetime.now().isoformat()
            })
            
            self._save_content_registry()
            
            logger.info(f"Removed {identifier_type}: {identifier}")
            
            return {"success": True, "message": f"Content removed successfully"}
            
        except Exception as e:
            logger.error(f"Error removing content {identifier}: {str(e)}")
            return {"success": False, "error": str(e)}
