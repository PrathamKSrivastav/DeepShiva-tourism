import logging
from typing import List, Dict, Any, Optional, Tuple
from .vector_store import VectorStoreManager
import asyncio
from concurrent.futures import ThreadPoolExecutor
import re

logger = logging.getLogger(__name__)

class SmartRetriever:
    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Persona-specific retrieval strategies
        self.persona_strategies = {
            "local_guide": {
                "primary_collections": ["general", "government"],
                "secondary_collections": ["trekking", "cultural"],
                "max_results": 6,
                "relevance_threshold": 0.7
            },
            "spiritual_teacher": {
                "primary_collections": ["spiritual", "cultural"],
                "secondary_collections": ["general"],
                "max_results": 8,
                "relevance_threshold": 0.6
            },
            "trek_companion": {
                "primary_collections": ["trekking", "government"],
                "secondary_collections": ["general"],
                "max_results": 5,
                "relevance_threshold": 0.8
            },
            "cultural_expert": {
                "primary_collections": ["cultural", "spiritual"],
                "secondary_collections": ["general", "government"],
                "max_results": 10,
                "relevance_threshold": 0.5
            }
        }
        
        # Intent-based collection weighting
        self.intent_collections = {
            "weather": ["general", "government"],
            "itinerary": ["general", "government", "trekking"],
            "spiritual": ["spiritual", "cultural"],
            "trekking": ["trekking", "government"],
            "emergency": ["government", "general"],
            "festival": ["cultural", "spiritual"],
            "accommodation": ["general", "government"],
            "food": ["cultural", "general"],
            "crowd": ["general", "government"]
        }
    
    async def retrieve_contextual_documents(
        self, 
        query: str, 
        persona: str, 
        intent: str,
        max_total_results: int = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents with persona and intent-aware strategy
        
        Args:
            query: User's query
            persona: Selected persona
            intent: Classified intent
            max_total_results: Maximum total results to return
            
        Returns:
            List of relevant document chunks with metadata
        """
        strategy = self.persona_strategies.get(persona, self.persona_strategies["local_guide"])
        
        if max_total_results is None:
            max_total_results = strategy["max_results"]
        
        # Determine collections to search based on persona and intent
        target_collections = self._get_target_collections(persona, intent)
        
        # Perform parallel search across collections
        search_results = await self._parallel_search(
            query=query,
            collections=target_collections,
            strategy=strategy
        )
        
        # Merge and rank results
        merged_results = self._merge_and_rank_results(
            search_results=search_results,
            persona=persona,
            intent=intent,
            relevance_threshold=strategy["relevance_threshold"]
        )
        
        # Apply final filtering and limiting
        final_results = merged_results[:max_total_results]
        
        logger.info(f"Retrieved {len(final_results)} documents for persona={persona}, intent={intent}")
        
        return final_results
    
    def _get_target_collections(self, persona: str, intent: str) -> List[str]:
        """Determine which collections to search based on persona and intent"""
        strategy = self.persona_strategies.get(persona, self.persona_strategies["local_guide"])
        
        # Start with persona-specific collections
        collections = strategy["primary_collections"].copy()
        
        # Add intent-specific collections
        intent_cols = self.intent_collections.get(intent, ["general"])
        for col in intent_cols:
            if col not in collections:
                collections.append(col)
        
        # Add secondary collections if we don't have enough variety
        if len(collections) < 3:
            for col in strategy["secondary_collections"]:
                if col not in collections:
                    collections.append(col)
                    if len(collections) >= 3:
                        break
        
        return collections
    
    async def _parallel_search(
        self, 
        query: str, 
        collections: List[str], 
        strategy: Dict[str, Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform parallel search across multiple collections"""
        
        def search_collection(collection_name: str) -> Tuple[str, List[Dict[str, Any]]]:
            try:
                results = self.vector_store.search_documents(
                    query=query,
                    collection_names=[collection_name],
                    n_results=strategy["max_results"] // len(collections) + 2
                )
                return collection_name, results.get(collection_name, [])
            except Exception as e:
                logger.error(f"Error searching collection {collection_name}: {str(e)}")
                return collection_name, []
        
        # Run searches in parallel
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(self.executor, search_collection, collection)
            for collection in collections
        ]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert to dictionary
        search_results = {}
        for result in results_list:
            if isinstance(result, tuple):
                collection_name, docs = result
                search_results[collection_name] = docs
            else:
                logger.error(f"Search task failed: {result}")
        
        return search_results
    
    def _merge_and_rank_results(
        self, 
        search_results: Dict[str, List[Dict[str, Any]]], 
        persona: str,
        intent: str,
        relevance_threshold: float
    ) -> List[Dict[str, Any]]:
        """Merge results from multiple collections and rank by relevance"""
        
        all_results = []
        
        for collection_name, results in search_results.items():
            for result in results:
                # Calculate combined score
                base_score = 1.0 - result.get('distance', 0.5)  # Convert distance to similarity
                
                # Apply collection weight based on persona and intent
                collection_weight = self._get_collection_weight(collection_name, persona, intent)
                
                # Apply content relevance boost
                content_boost = self._calculate_content_relevance(result, intent)
                
                # Final score
                final_score = base_score * collection_weight * content_boost
                
                # Only include if above threshold
                if final_score >= relevance_threshold:
                    result['final_score'] = final_score
                    result['collection_weight'] = collection_weight
                    result['content_boost'] = content_boost
                    all_results.append(result)
        
        # Sort by final score (descending)
        all_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Remove duplicates based on content similarity
        unique_results = self._remove_similar_duplicates(all_results)
        
        return unique_results
    
    def _get_collection_weight(self, collection_name: str, persona: str, intent: str) -> float:
        """Calculate weight for collection based on persona and intent"""
        strategy = self.persona_strategies.get(persona, self.persona_strategies["local_guide"])
        
        # Base weight from persona strategy
        if collection_name in strategy["primary_collections"]:
            base_weight = 1.0
        elif collection_name in strategy["secondary_collections"]:
            base_weight = 0.8
        else:
            base_weight = 0.6
        
        # Intent-based boost
        intent_boost = 1.0
        if collection_name in self.intent_collections.get(intent, []):
            intent_boost = 1.2
        
        return base_weight * intent_boost
    
    def _calculate_content_relevance(self, result: Dict[str, Any], intent: str) -> float:
        """Calculate content relevance boost based on metadata and content"""
        content = result.get('content', '').lower()
        metadata = result.get('metadata', {})
        
        relevance_boost = 1.0
        
        # Source type boost
        source_type = metadata.get('source_type', '')
        if source_type == 'web_page':
            relevance_boost *= 1.1  # Prefer web content for freshness
        elif source_type == 'pdf':
            relevance_boost *= 1.05  # Slight preference for structured documents
        
        # Content type alignment
        content_type = metadata.get('content_type', 'general')
        intent_content_alignment = {
            'spiritual': {'spiritual': 1.3, 'cultural': 1.1},
            'trekking': {'trekking': 1.3, 'government': 1.1},
            'cultural': {'cultural': 1.3, 'spiritual': 1.1},
            'government': {'government': 1.3}
        }
        
        if intent in intent_content_alignment:
            relevance_boost *= intent_content_alignment[intent].get(content_type, 1.0)
        
        # Freshness boost (more recent content gets slight boost)
        processed_at = metadata.get('processed_at', '')
        if processed_at:
            # Simple freshness calculation - more recent = slight boost
            try:
                from datetime import datetime, timedelta
                processed_date = datetime.fromisoformat(processed_at)
                age_days = (datetime.now() - processed_date).days
                if age_days <= 30:  # Recent content
                    relevance_boost *= 1.05
            except:
                pass
        
        return min(relevance_boost, 1.5)  # Cap the boost
    
    def _remove_similar_duplicates(
        self, 
        results: List[Dict[str, Any]], 
        similarity_threshold: float = 0.9
    ) -> List[Dict[str, Any]]:
        """Remove results that are too similar to avoid redundancy"""
        if not results:
            return results
        
        unique_results = [results[0]]  # Always keep the top result
        
        for result in results[1:]:
            is_duplicate = False
            result_content = result.get('content', '').lower()
            
            for unique_result in unique_results:
                unique_content = unique_result.get('content', '').lower()
                
                # Simple similarity check using common words
                if self._calculate_text_similarity(result_content, unique_content) > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_results.append(result)
        
        return unique_results
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple similarity between two texts"""
        if not text1 or not text2:
            return 0.0
        
        # Simple word-based similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    async def get_retrieval_stats(self) -> Dict[str, Any]:
        """Get retrieval statistics and health metrics"""
        stats = {
            "vector_store_stats": self.vector_store.get_collection_stats(),
            "persona_strategies": list(self.persona_strategies.keys()),
            "supported_intents": list(self.intent_collections.keys()),
            "executor_stats": {
                "max_workers": self.executor._max_workers,
                "active_threads": len(self.executor._threads) if hasattr(self.executor, '_threads') else 0
            }
        }
        
        return stats
