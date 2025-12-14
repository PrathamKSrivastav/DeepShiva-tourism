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
            "json_files": self.base_path / "json_files",  # NEW: JSON storage
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
            "json_entities": {},  # NEW: Track JSON entities
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
    
    # ==================== EXISTING PDF METHODS ====================
    
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
    
    # ==================== EXISTING WEB PAGE METHODS ====================
    
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
    
    # ==================== EXISTING TEXT CONTENT METHODS ====================
    
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
    
    # ==================== NEW: JSON PROCESSING METHODS ====================
    
    async def add_json_file(self, file_path: Path, managed: bool = True) -> Dict[str, Any]:
        """
        Add JSON file to RAG system
        
        Args:
            file_path: Path to JSON file
            managed: If True, copy file to managed location
        
        Returns:
            Processing result dict
        """
        try:
            # Copy file to managed location if requested
            if managed:
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file_path.name}"
                managed_path = self.paths["json_files"] / filename
                shutil.copy2(file_path, managed_path)
                process_path = managed_path
            else:
                process_path = file_path
                managed_path = file_path
            
            # Process JSON
            chunks, metadata_list = self.document_processor.process_json(process_path)
            
            if not chunks:
                logger.warning(f"No content extracted from JSON: {file_path}")
                return {"success": False, "error": "No content extracted"}
            
            # Determine entity type from first metadata
            entity_type = metadata_list[0]['entity_type']
            
            # Add to vector store
            doc_ids = self.vector_store.add_json_documents(
                documents=chunks,
                metadatas=metadata_list,
                entity_type=entity_type
            )
            
            # Count unique entities
            unique_entities = len(set(
                m['entity_id'] for m in metadata_list 
                if m.get('entity_id')
            ))
            
            # Map entity_type to collection
            collection_map = {
                'spiritual_site': 'spiritual_sites',
                'festival': 'festivals',
                'crowd_pattern': 'crowd_patterns',
                'homestay': 'homestays',
                'persona': 'personas',
                'trek': 'treks',
                'cuisine': 'cuisines',
                'wellness': 'wellness',
                'eco_tip': 'eco_tips',
                'emergency_info': 'emergency_info',
                'shloka': 'shlokas',
                'generic': 'general'
            }
            collection_name = collection_map.get(entity_type, 'general')
            
            # Update registry
            json_info = {
                "original_path": str(file_path),
                "managed_path": str(managed_path) if managed else str(file_path),
                "entity_type": entity_type,
                "chunks_count": len(chunks),
                "entity_count": unique_entities,
                "collection": collection_name,
                "document_ids": doc_ids,
                "added_at": datetime.now().isoformat(),
                "file_size": process_path.stat().st_size
            }
            
            self.content_registry["json_entities"][str(managed_path)] = json_info
            self.content_registry["total_documents"] += len(chunks)
            self.content_registry["processing_history"].append({
                "action": "add_json",
                "file": file_path.name,
                "entity_type": entity_type,
                "entities": unique_entities,
                "chunks": len(chunks),
                "timestamp": datetime.now().isoformat()
            })
            
            self._save_content_registry()
            
            logger.info(
                f"Added JSON {file_path.name}: "
                f"{unique_entities} entities → {len(chunks)} chunks "
                f"({entity_type} → {collection_name})"
            )
            
            return {
                "success": True,
                "filename": file_path.name,
                "chunks_count": len(chunks),
                "entity_count": unique_entities,
                "entity_type": entity_type,
                "collection": collection_name,
                "document_ids": doc_ids
            }
            
        except Exception as e:
            logger.error(f"Error adding JSON {file_path}: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def batch_ingest_all_json(
        self, 
        json_directory: Path,
        managed: bool = True
    ) -> Dict[str, Any]:
        """
        Batch ingest all JSON files from directory
        
        Args:
            json_directory: Directory containing JSON files
            managed: If True, copy files to managed location
        
        Returns:
            Batch processing results
        """
        results = {
            'processed_files': [],
            'failed_files': [],
            'total_chunks': 0,
            'total_entities': 0,
            'processing_time': None
        }
        
        try:
            json_directory = Path(json_directory)
            if not json_directory.exists():
                logger.error(f"Directory not found: {json_directory}")
                return {"success": False, "error": "Directory not found", **results}
            
            json_files = list(json_directory.glob('*.json'))
            logger.info(f"Found {len(json_files)} JSON files to process")
            
            if not json_files:
                return {"success": False, "error": "No JSON files found", **results}
            
            start_time = datetime.now()
            
            for json_file in json_files:
                result = await self.add_json_file(json_file, managed=managed)
                
                if result['success']:
                    results['processed_files'].append({
                        'file': json_file.name,
                        'chunks': result['chunks_count'],
                        'entities': result['entity_count'],
                        'type': result['entity_type'],
                        'collection': result['collection']
                    })
                    results['total_chunks'] += result['chunks_count']
                    results['total_entities'] += result['entity_count']
                else:
                    results['failed_files'].append({
                        'file': json_file.name,
                        'error': result.get('error')
                    })
            
            end_time = datetime.now()
            results['processing_time'] = str(end_time - start_time)
            
            logger.info(
                f"Batch JSON ingestion complete: "
                f"{len(results['processed_files'])} files, "
                f"{results['total_entities']} entities, "
                f"{results['total_chunks']} chunks"
            )
            
            return {"success": True, **results}
            
        except Exception as e:
            logger.error(f"Error in batch JSON processing: {str(e)}")
            return {"success": False, "error": str(e), **results}
    
    # ==================== EXISTING BATCH PROCESSING ====================
    
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
            supported_extensions = ['.pdf', '.txt', '.md', '.json']
            files = [
                f for f in directory.rglob('*') 
                if f.is_file() and f.suffix.lower() in supported_extensions
            ]
            
            for file_path in files:
                try:
                    if file_path.suffix.lower() == '.pdf':
                        result = await self.add_pdf_file(file_path, content_type)
                    elif file_path.suffix.lower() == '.json':
                        result = await self.add_json_file(file_path, managed=True)
                    else:
                        # For text files, use filename as title
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        result = await self.add_text_content(content, file_path.stem, content_type)
                    
                    if result["success"]:
                        results["processed_files"].append({
                            "file": str(file_path),
                            "chunks": result["chunks_count"],
                            "collection": result.get("collection", "unknown")
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
    
    # ==================== STATISTICS & MANAGEMENT ====================
    
    def get_content_statistics(self) -> Dict[str, Any]:
        """Get comprehensive content statistics"""
        try:
            vector_stats = self.vector_store.get_all_stats()
            
            stats = {
                "total_files": len(self.content_registry.get("files", {})),
                "total_urls": len(self.content_registry.get("urls", {})),
                "total_json_files": len(self.content_registry.get("json_entities", {})),
                "total_documents": self.content_registry.get("total_documents", 0),
                "collections": vector_stats.get("collections", {}),
                "processing_history": self.content_registry.get("processing_history", [])[-10:],
                "last_updated": self.content_registry.get("last_updated", "Never"),
                "storage_paths": {k: str(v) for k, v in self.paths.items()},
                "content_types_distribution": {},
                "json_entities_by_type": {}
            }
            
            # Calculate content type distribution for regular files
            for file_info in self.content_registry.get("files", {}).values():
                content_type = file_info.get("content_type", "general")
                stats["content_types_distribution"][content_type] = \
                    stats["content_types_distribution"].get(content_type, 0) + file_info.get("chunks_count", 0)
            
            for url_info in self.content_registry.get("urls", {}).values():
                content_type = url_info.get("content_type", "general")
                stats["content_types_distribution"][content_type] = \
                    stats["content_types_distribution"].get(content_type, 0) + url_info.get("chunks_count", 0)
            
            # Calculate JSON entities distribution
            for json_info in self.content_registry.get("json_entities", {}).values():
                entity_type = json_info.get("entity_type", "unknown")
                if entity_type not in stats["json_entities_by_type"]:
                    stats["json_entities_by_type"][entity_type] = {
                        "files": 0,
                        "entities": 0,
                        "chunks": 0
                    }
                stats["json_entities_by_type"][entity_type]["files"] += 1
                stats["json_entities_by_type"][entity_type]["entities"] += json_info.get("entity_count", 0)
                stats["json_entities_by_type"][entity_type]["chunks"] += json_info.get("chunks_count", 0)
            
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
            
            elif identifier_type == "json":
                if identifier not in self.content_registry.get("json_entities", {}):
                    return {"success": False, "error": "JSON file not found in registry"}
                
                json_info = self.content_registry["json_entities"][identifier]
                doc_ids = json_info.get("document_ids", [])
                collection = json_info.get("collection", "general")
                
                # Remove from vector store
                if doc_ids:
                    self.vector_store.delete_documents(doc_ids, collection)
                
                # Remove file
                file_path = Path(identifier)
                if file_path.exists():
                    file_path.unlink()
                
                # Update registry
                del self.content_registry["json_entities"][identifier]
            
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
    
    async def clear_json_content(self) -> Dict[str, Any]:
        """Clear all JSON content (use with caution)"""
        try:
            removed_count = 0
            
            for json_path in list(self.content_registry.get("json_entities", {}).keys()):
                result = await self.remove_content(json_path, identifier_type="json")
                if result["success"]:
                    removed_count += 1
            
            logger.info(f"Cleared {removed_count} JSON files from RAG system")
            
            return {
                "success": True,
                "message": f"Cleared {removed_count} JSON files",
                "removed_count": removed_count
            }
            
        except Exception as e:
            logger.error(f"Error clearing JSON content: {str(e)}")
            return {"success": False, "error": str(e)}
