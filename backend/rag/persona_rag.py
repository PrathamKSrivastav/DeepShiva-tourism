import logging
from typing import Dict, Any, List, Optional, Tuple
from .vector_store import VectorStoreManager
from .retriever import SmartRetriever
import asyncio

logger = logging.getLogger(__name__)

class PersonaRAG:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.retriever = SmartRetriever(vector_store)
        
        # Persona-specific RAG configurations
        self.persona_configs = {
            "local_guide": {
                "context_window": 4000,  # chars
                "max_retrieved_docs": 6,
                "prioritize_practical_info": True,
                "include_source_citations": True,
                "context_template": "Here's what I know from local sources:\n\n{context}\n\nBased on this information:"
            },
            "spiritual_teacher": {
                "context_window": 6000,
                "max_retrieved_docs": 8,
                "prioritize_philosophical_content": True,
                "include_source_citations": False,  # More flowing narrative
                "context_template": "Drawing from sacred texts and spiritual wisdom:\n\n{context}\n\nIn the light of this knowledge:"
            },
            "trek_companion": {
                "context_window": 3000,
                "max_retrieved_docs": 5,
                "prioritize_safety_info": True,
                "include_source_citations": True,
                "context_template": "Here's the essential info from reliable sources:\n\n{context}\n\nGiven these facts:"
            },
            "cultural_expert": {
                "context_window": 8000,  # Needs more context for stories
                "max_retrieved_docs": 10,
                "prioritize_historical_content": True,
                "include_source_citations": True,
                "context_template": "From historical records and cultural documentation:\n\n{context}\n\nWith this rich heritage in mind:"
            }
        }
    
    async def enhance_query_with_rag(
        self, 
        query: str, 
        persona: str, 
        intent: str,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Enhance user query with RAG context for the specified persona
        
        Args:
            query: User's query
            persona: Selected persona
            intent: Classified intent
            context: Additional context
            
        Returns:
            Enhanced context dict with RAG information
        """
        try:
            config = self.persona_configs.get(persona, self.persona_configs["local_guide"])
            
            # Retrieve relevant documents
            retrieved_docs = await self.retriever.retrieve_contextual_documents(
                query=query,
                persona=persona,
                intent=intent,
                max_total_results=config["max_retrieved_docs"]
            )
            
            if not retrieved_docs:
                logger.info(f"No relevant documents found for query: {query[:50]}...")
                return {
                    "has_rag_context": False,
                    "rag_context": "",
                    "source_count": 0,
                    "sources": []
                }
            
            # Build context string
            rag_context = self._build_context_string(
                retrieved_docs=retrieved_docs,
                persona=persona,
                max_chars=config["context_window"]
            )
            
            # Extract source information
            sources = self._extract_source_info(retrieved_docs)
            
            # Build enhanced context
            enhanced_context = {
                "has_rag_context": True,
                "rag_context": rag_context,
                "formatted_context": config["context_template"].format(context=rag_context),
                "source_count": len(sources),
                "sources": sources,
                "retrieved_doc_count": len(retrieved_docs),
                "persona_config": persona,
                "intent": intent,
                "context_length": len(rag_context)
            }
            
            # Add persona-specific enhancements
            enhanced_context.update(
                self._add_persona_specific_context(
                    persona=persona,
                    retrieved_docs=retrieved_docs,
                    intent=intent
                )
            )
            
            logger.info(f"RAG enhanced context for {persona}: {len(retrieved_docs)} docs, {len(rag_context)} chars")
            
            return enhanced_context
            
        except Exception as e:
            logger.error(f"Error enhancing query with RAG: {str(e)}")
            return {
                "has_rag_context": False,
                "rag_context": "",
                "source_count": 0,
                "sources": [],
                "error": str(e)
            }
    
    def _build_context_string(
        self, 
        retrieved_docs: List[Dict[str, Any]], 
        persona: str,
        max_chars: int
    ) -> str:
        """Build context string from retrieved documents"""
        config = self.persona_configs.get(persona, self.persona_configs["local_guide"])
        
        context_parts = []
        current_length = 0
        
        for i, doc in enumerate(retrieved_docs):
            content = doc.get('content', '')
            metadata = doc.get('metadata', {})
            
            # Format content based on persona preferences
            formatted_content = self._format_content_for_persona(content, metadata, persona)
            
            # Check if adding this content would exceed limit
            if current_length + len(formatted_content) > max_chars:
                # Try to fit partial content
                remaining_chars = max_chars - current_length - 10  # Buffer for ellipsis
                if remaining_chars > 100:  # Only if meaningful content can fit
                    truncated = formatted_content[:remaining_chars] + "..."
                    context_parts.append(f"{i+1}. {truncated}")
                break
            
            context_parts.append(f"{i+1}. {formatted_content}")
            current_length += len(formatted_content)
        
        return "\n\n".join(context_parts)
    
    def _format_content_for_persona(
        self, 
        content: str, 
        metadata: Dict[str, Any], 
        persona: str
    ) -> str:
        """Format content based on persona preferences"""
        config = self.persona_configs.get(persona, self.persona_configs["local_guide"])
        
        # Base content
        formatted = content.strip()
        
        # Add source citation if required
        if config.get("include_source_citations", False):
            source = metadata.get('source', '')
            if source:
                if metadata.get('source_type') == 'web_page':
                    source_name = metadata.get('title', metadata.get('domain', 'Web Source'))
                elif metadata.get('source_type') == 'pdf':
                    source_name = metadata.get('file_name', 'PDF Document')
                else:
                    source_name = 'Official Source'
                
                formatted += f" [Source: {source_name}]"
        
        return formatted
    
    def _extract_source_info(self, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Extract and deduplicate source information"""
        sources = []
        seen_sources = set()
        
        for doc in retrieved_docs:
            metadata = doc.get('metadata', {})
            source = metadata.get('source', '')
            
            if source and source not in seen_sources:
                source_info = {
                    "source": source,
                    "type": metadata.get('source_type', 'unknown'),
                    "title": metadata.get('title', metadata.get('file_name', 'Unknown Title')),
                    "content_type": metadata.get('content_type', 'general')
                }
                
                if metadata.get('source_type') == 'web_page':
                    source_info["domain"] = metadata.get('domain', '')
                
                sources.append(source_info)
                seen_sources.add(source)
        
        return sources
    
    def _add_persona_specific_context(
        self, 
        persona: str, 
        retrieved_docs: List[Dict[str, Any]], 
        intent: str
    ) -> Dict[str, Any]:
        """Add persona-specific context enhancements"""
        
        enhancements = {}
        
        if persona == "local_guide":
            # Prioritize practical information
            practical_docs = [
                doc for doc in retrieved_docs 
                if any(keyword in doc.get('content', '').lower() 
                      for keyword in ['practical', 'tip', 'advice', 'recommendation', 'cost', 'time', 'how to'])
            ]
            enhancements["practical_info_count"] = len(practical_docs)
            
        elif persona == "spiritual_teacher":
            # Count spiritual/cultural content
            spiritual_docs = [
                doc for doc in retrieved_docs
                if doc.get('metadata', {}).get('content_type') in ['spiritual', 'cultural']
            ]
            enhancements["spiritual_content_ratio"] = len(spiritual_docs) / len(retrieved_docs) if retrieved_docs else 0
            
        elif persona == "trek_companion":
            # Count safety and trekking specific info
            safety_docs = [
                doc for doc in retrieved_docs
                if any(keyword in doc.get('content', '').lower()
                      for keyword in ['safety', 'danger', 'precaution', 'equipment', 'weather', 'altitude'])
            ]
            enhancements["safety_info_count"] = len(safety_docs)
            
        elif persona == "cultural_expert":
            # Count historical and cultural content
            cultural_docs = [
                doc for doc in retrieved_docs
                if doc.get('metadata', {}).get('content_type') in ['cultural', 'spiritual']
            ]
            enhancements["cultural_content_count"] = len(cultural_docs)
        
        return enhancements
    
    async def get_rag_health_status(self) -> Dict[str, Any]:
        """Get RAG system health and statistics"""
        try:
            # Get retriever stats
            retriever_stats = await self.retriever.get_retrieval_stats()
            
            # Get vector store stats
            vector_stats = self.vector_store.get_collection_stats()
            
            # Calculate total documents
            total_docs = sum(
                stats.get('document_count', 0) 
                for stats in vector_stats.values()
            )
            
            health_status = {
                "status": "healthy" if total_docs > 0 else "no_data",
                "total_documents": total_docs,
                "collections": vector_stats,
                "persona_configs": list(self.persona_configs.keys()),
                "retriever_stats": retriever_stats,
                "rag_enabled": total_docs > 0
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Error getting RAG health status: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "rag_enabled": False
            }
