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
        
        # ==================== UPDATED PERSONA STRATEGIES ====================
        # Now includes JSON entity collections
        self.persona_strategies = {
            "local_guide": {
                "primary_collections": ["spiritual_sites", "homestays", "crowd_patterns", "general", "government"],
                "secondary_collections": ["festivals", "cuisines", "treks", "trekking", "cultural"],
                "max_results": 6,
                "relevance_threshold": 0.5
            },
            "spiritual_teacher": {
                "primary_collections": ["spiritual_sites", "shlokas", "wellness", "festivals", "spiritual", "cultural"],
                "secondary_collections": ["crowd_patterns", "general"],
                "max_results": 8,
                "relevance_threshold": 0.5
            },
            "trek_companion": {
                "primary_collections": ["treks", "emergency_info", "spiritual_sites", "trekking", "government"],
                "secondary_collections": ["homestays", "eco_tips", "general"],
                "max_results": 5,
                "relevance_threshold": 0.5
            },
            "cultural_expert": {
                "primary_collections": ["festivals", "spiritual_sites", "cuisines", "cultural", "spiritual"],
                "secondary_collections": ["crowd_patterns", "homestays", "general", "government"],
                "max_results": 10,
                "relevance_threshold": 0.5
            }
        }
        
        # ==================== UPDATED INTENT COLLECTIONS ====================
        # Mapped to include JSON collections
        self.intent_collections = {
            "weather": ["general", "government", "spiritual_sites"],
            "itinerary": ["spiritual_sites", "homestays", "crowd_patterns", "treks", "general", "government"],
            "spiritual": ["spiritual_sites", "shlokas", "festivals", "wellness", "spiritual", "cultural"],
            "trekking": ["treks", "emergency_info", "spiritual_sites", "trekking", "government"],
            "emergency": ["emergency_info", "treks", "government", "general"],
            "festival": ["festivals", "spiritual_sites", "crowd_patterns", "cultural", "spiritual"],
            "accommodation": ["homestays", "spiritual_sites", "general", "government"],
            "food": ["cuisines", "homestays", "cultural", "general"],
            "crowd": ["crowd_patterns", "festivals", "spiritual_sites", "general", "government"],
            "planning": ["spiritual_sites", "homestays", "crowd_patterns", "festivals", "treks", "general"],
            "wellness": ["wellness", "spiritual_sites", "homestays"],
            "eco": ["eco_tips", "homestays", "treks"],
            "cultural": ["festivals", "cuisines", "spiritual_sites", "cultural"]
        }
        
        # ==================== NEW: ENTITY TYPE MAPPING ====================
        self.entity_type_collections = {
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
            'shloka': 'shlokas'
        }
    
    async def retrieve_contextual_documents(
        self, 
        query: str, 
        persona: str, 
        intent: str,
        max_total_results: int = None,
        expand_references: bool = True,  # NEW: Cross-reference expansion
        filters: Optional[Dict[str, Any]] = None  # NEW: Metadata filters
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents with persona and intent-aware strategy
        
        Args:
            query: User's query
            persona: Selected persona (local_guide, spiritual_teacher, etc.)
            intent: Classified intent
            max_total_results: Maximum total results to return
            expand_references: Whether to expand cross-references
            filters: Optional metadata filters (e.g., {'state': 'Uttarakhand'})
            
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
            strategy=strategy,
            filters=filters
        )
        
        # Merge and rank results
        merged_results = self._merge_and_rank_results(
            search_results=search_results,
            persona=persona,
            intent=intent,
            relevance_threshold=strategy["relevance_threshold"]
        )
        
        # Apply final filtering and limiting
        primary_results = merged_results[:max_total_results]
        
        # NEW: Expand cross-references if requested
        if expand_references:
            final_results = await self._expand_cross_references(
                primary_results=primary_results,
                query=query,
                max_expansions=5  # Limit cross-ref expansions
            )
        else:
            final_results = primary_results
        
        logger.info(
            f"Retrieved {len(final_results)} documents "
            f"(primary: {len(primary_results)}, with refs: {len(final_results) - len(primary_results)}) "
            f"for persona={persona}, intent={intent}"
        )
        
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
        strategy: Dict[str, Any],
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform parallel search across multiple collections"""
        
        # ============ ADD DEBUG LOGGING HERE ============
        logger.info(f"🔍 Starting parallel search")
        logger.info(f"🔍 Query: {query[:100]}...")
        logger.info(f"🔍 Collections to search: {collections}")
        logger.info(f"🔍 Strategy max_results: {strategy.get('max_results')}")
        logger.info(f"🔍 Filters: {filters}")
        # ================================================
        
        def search_collection(collection_name: str) -> Tuple[str, List[Dict[str, Any]]]:
            try:
                # Check if collection exists
                if collection_name not in self.vector_store.collections:
                    logger.warning(f"⚠️ Collection {collection_name} not found, skipping")
                    return collection_name, []
                
                # ============ ADD DEBUG LOGGING HERE ============
                collection = self.vector_store.collections[collection_name]
                doc_count = collection.count()
                logger.info(f"📊 Collection {collection_name}: {doc_count} documents available")
                # ================================================
                
                # Use new query method with filters
                results_data = self.vector_store.query(
                    query_text=query,
                    collection_name=collection_name,
                    n_results=strategy["max_results"] // len(collections) + 2,
                    where=filters
                )
                
                # ============ ADD DEBUG LOGGING HERE ============
                raw_doc_count = len(results_data.get('documents', [[]])[0])
                logger.info(f"📊 Raw query returned {raw_doc_count} results from {collection_name}")
                
                if results_data.get('documents'):
                    logger.info(f"📊 Results structure: documents={len(results_data.get('documents', []))}, metadatas={len(results_data.get('metadatas', []))}, distances={len(results_data.get('distances', []))}")
                # ================================================
                
                # Format results
                formatted_results = []
                if results_data.get('documents') and results_data['documents'][0]:
                    for i in range(len(results_data['documents'][0])):
                        formatted_results.append({
                            'content': results_data['documents'][0][i],
                            'metadata': results_data['metadatas'][0][i],
                            'distance': results_data['distances'][0][i],
                            'collection': collection_name
                        })
                    # ============ ADD DEBUG LOGGING HERE ============
                    logger.info(f"✅ Formatted {len(formatted_results)} results from {collection_name}")
                    if formatted_results:
                        logger.info(f"   First result distance: {formatted_results[0]['distance']:.4f}")
                        logger.info(f"   First result entity: {formatted_results[0]['metadata'].get('name', 'N/A')}")
                    # ================================================
                else:
                    # ============ ADD DEBUG LOGGING HERE ============
                    logger.warning(f"⚠️ No documents found in {collection_name} for query: {query[:50]}...")
                    # ================================================
                
                return collection_name, formatted_results
                
            except Exception as e:
                # ============ ENHANCED ERROR LOGGING ============
                logger.error(f"❌ Error searching collection {collection_name}: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # ================================================
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
                # ============ ADD DEBUG LOGGING HERE ============
                logger.info(f"📦 {collection_name}: {len(docs)} docs added to search_results")
                # ================================================
            else:
                logger.error(f"❌ Search task failed: {result}")
        
        # ============ ADD FINAL SUMMARY LOGGING ============
        total_docs = sum(len(docs) for docs in search_results.values())
        logger.info(f"🎯 Parallel search complete: {total_docs} total documents from {len(search_results)} collections")
        # ====================================================
        
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
        
        logger.info(f"🔄 Merging and ranking results from {len(search_results)} collections")
        logger.info(f"🎯 Relevance threshold: {relevance_threshold}")
        
        for collection_name, results in search_results.items():
            for result in results:
                distance = result.get('distance', 1.0)
                
                # FIXED: ChromaDB uses cosine distance (0=identical, 2=opposite)
                # Convert to similarity score (1=identical, 0=opposite)
                # For cosine distance: similarity = 1 - (distance / 2)
                # This maps [0, 2] distance to [1, 0] similarity
                base_score = max(0.0, 1.0 - (distance / 2.0))
                
                # Apply collection weight based on persona and intent
                collection_weight = self._get_collection_weight(collection_name, persona, intent)
                
                # Apply content relevance boost
                content_boost = self._calculate_content_relevance(result, intent)
                
                # NEW: Apply entity type boost for JSON entities
                entity_boost = self._calculate_entity_boost(result)
                
                # Final score
                final_score = base_score * collection_weight * content_boost * entity_boost
                
                # Log scoring details
                entity_name = result.get('metadata', {}).get('name', 'Unknown')[:40]
                logger.debug(
                    f"   📝 {entity_name} [{collection_name}]: "
                    f"dist={distance:.3f} → base={base_score:.3f} × "
                    f"col_wt={collection_weight:.2f} × "
                    f"content={content_boost:.2f} × "
                    f"entity={entity_boost:.2f} = "
                    f"final={final_score:.3f}"
                )
                
                # Only include if above threshold
                if final_score >= relevance_threshold:
                    result['final_score'] = final_score
                    result['base_score'] = base_score  # Store for debugging
                    result['collection_weight'] = collection_weight
                    result['content_boost'] = content_boost
                    result['entity_boost'] = entity_boost
                    all_results.append(result)
                    logger.debug(f"      ✅ ACCEPTED (score={final_score:.3f} >= {relevance_threshold})")
                else:
                    logger.debug(f"      ❌ REJECTED (score={final_score:.3f} < {relevance_threshold})")
        
        logger.info(f"🎯 After filtering: {len(all_results)}/{sum(len(r) for r in search_results.values())} documents passed threshold")
        
        # Sort by final score (descending)
        all_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Remove duplicates based on content similarity
        unique_results = self._remove_similar_duplicates(all_results)
        
        logger.info(f"📊 After deduplication: {len(unique_results)} unique documents")
        
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
            'spiritual': {'spiritual': 1.3, 'cultural': 1.1, 'spiritual_sites': 1.3},
            'trekking': {'trekking': 1.3, 'treks': 1.3, 'government': 1.1},
            'cultural': {'cultural': 1.3, 'festivals': 1.3, 'spiritual': 1.1},
            'government': {'government': 1.3},
            'planning': {'crowd_patterns': 1.2, 'homestays': 1.2},
            'festival': {'festivals': 1.3, 'spiritual_sites': 1.1}
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
    
    def _calculate_entity_boost(self, result: Dict[str, Any]) -> float:
        """
        NEW: Calculate boost for JSON entities based on entity quality
        """
        metadata = result.get('metadata', {})
        entity_type = metadata.get('entity_type')
        
        if not entity_type:
            return 1.0  # No boost for non-entity documents
        
        boost = 1.0
        
        # Boost for complete entities (not sub-chunks)
        if not metadata.get('is_sub_chunk', False):
            boost *= 1.1
        
        # Boost for entities with rich metadata
        if metadata.get('altitude_m'):
            boost *= 1.02
        if metadata.get('best_season'):
            boost *= 1.02
        if metadata.get('recommended_persona'):
            boost *= 1.03
        
        # Boost for entities with cross-references (shows interconnected knowledge)
        has_refs = any([
            metadata.get('related_festivals'),
            metadata.get('related_treks'),
            metadata.get('related_sites'),
            metadata.get('related_crowd_pattern')
        ])
        if has_refs:
            boost *= 1.05
        
        return min(boost, 1.2)  # Cap at 1.2x
    
    # ==================== NEW: CROSS-REFERENCE EXPANSION ====================
    
    async def _expand_cross_references(
        self,
        primary_results: List[Dict[str, Any]],
        query: str,
        max_expansions: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Expand cross-references from primary results to include related entities
        """
        expanded = primary_results.copy()
        seen_entity_ids = set()
        expansion_count = 0
        
        # Track primary entity IDs
        for result in primary_results:
            entity_id = result.get('metadata', {}).get('entity_id')
            if entity_id:
                seen_entity_ids.add(entity_id)
        
        # Expand references from each primary result
        for result in primary_results:
            if expansion_count >= max_expansions:
                break
            
            metadata = result.get('metadata', {})
            
            # Expand festival references
            related_festivals = self._parse_array_field(metadata.get('related_festivals'))
            for festival_id in related_festivals[:2]:  # Limit to 2 per entity
                if expansion_count >= max_expansions:
                    break
                if festival_id and festival_id not in seen_entity_ids:
                    festival_doc = await self._fetch_entity_by_id(
                        entity_id=festival_id,
                        collection_name='festivals'
                    )
                    if festival_doc:
                        festival_doc['is_cross_reference'] = True
                        festival_doc['reference_type'] = 'festival'
                        festival_doc['referenced_from'] = metadata.get('name', 'Unknown')
                        expanded.append(festival_doc)
                        seen_entity_ids.add(festival_id)
                        expansion_count += 1
            
            # Expand crowd pattern reference
            crowd_pattern_id = metadata.get('related_crowd_pattern')
            if crowd_pattern_id and crowd_pattern_id not in seen_entity_ids and expansion_count < max_expansions:
                crowd_doc = await self._fetch_entity_by_id(
                    entity_id=crowd_pattern_id,
                    collection_name='crowd_patterns'
                )
                if crowd_doc:
                    crowd_doc['is_cross_reference'] = True
                    crowd_doc['reference_type'] = 'crowd_pattern'
                    crowd_doc['referenced_from'] = metadata.get('name', 'Unknown')
                    expanded.append(crowd_doc)
                    seen_entity_ids.add(crowd_pattern_id)
                    expansion_count += 1
            
            # Expand trek references
            related_treks = self._parse_array_field(metadata.get('related_treks'))
            for trek_id in related_treks[:1]:  # Limit to 1 trek
                if expansion_count >= max_expansions:
                    break
                if trek_id and trek_id not in seen_entity_ids:
                    trek_doc = await self._fetch_entity_by_id(
                        entity_id=trek_id,
                        collection_name='treks'
                    )
                    if trek_doc:
                        trek_doc['is_cross_reference'] = True
                        trek_doc['reference_type'] = 'trek'
                        trek_doc['referenced_from'] = metadata.get('name', 'Unknown')
                        expanded.append(trek_doc)
                        seen_entity_ids.add(trek_id)
                        expansion_count += 1
            
            # Expand homestay references
            related_homestays = self._parse_array_field(metadata.get('related_homestays'))
            for homestay_id in related_homestays[:1]:
                if expansion_count >= max_expansions:
                    break
                if homestay_id and homestay_id not in seen_entity_ids:
                    homestay_doc = await self._fetch_entity_by_id(
                        entity_id=homestay_id,
                        collection_name='homestays'
                    )
                    if homestay_doc:
                        homestay_doc['is_cross_reference'] = True
                        homestay_doc['reference_type'] = 'homestay'
                        homestay_doc['referenced_from'] = metadata.get('name', 'Unknown')
                        expanded.append(homestay_doc)
                        seen_entity_ids.add(homestay_id)
                        expansion_count += 1
        
        logger.info(f"Expanded {expansion_count} cross-references")
        return expanded
    
    async def _fetch_entity_by_id(
        self,
        entity_id: str,
        collection_name: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch a specific entity by ID from collection"""
        try:
            loop = asyncio.get_event_loop()
            entity_data = await loop.run_in_executor(
                self.executor,
                self.vector_store.get_by_entity_id,
                entity_id,
                collection_name
            )
            
            if entity_data:
                # Format to match search results structure
                return {
                    'content': entity_data.get('content'),
                    'metadata': entity_data.get('metadata'),
                    'distance': 0.0,  # Direct fetch, no distance
                    'collection': collection_name,
                    'final_score': 0.8,  # Give it a good score since it's referenced
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching entity {entity_id} from {collection_name}: {str(e)}")
            return None
    
    def _parse_array_field(self, field_value: Any) -> List[str]:
        """Parse array field from metadata (handles string or list)"""
        if isinstance(field_value, list):
            return field_value
        elif isinstance(field_value, str):
            # Comma-separated string (from ChromaDB metadata cleaning)
            return [x.strip() for x in field_value.split(',') if x.strip()]
        return []
    
    # ==================== NEW: ENTITY-SPECIFIC RETRIEVAL ====================
    
    async def retrieve_by_entity_id(
        self,
        entity_id: str,
        entity_type: str,
        expand_references: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve specific entity by ID with optional reference expansion
        
        Args:
            entity_id: Entity ID (e.g., 'sp001')
            entity_type: Entity type (e.g., 'spiritual_site')
            expand_references: Whether to expand cross-references
        
        Returns:
            Entity data with optional expanded references
        """
        collection_name = self.entity_type_collections.get(entity_type)
        if not collection_name:
            logger.error(f"Unknown entity type: {entity_type}")
            return None
        
        entity = await self._fetch_entity_by_id(entity_id, collection_name)
        
        if not entity:
            return None
        
        if expand_references:
            expanded = await self._expand_cross_references(
                primary_results=[entity],
                query=entity.get('metadata', {}).get('name', ''),
                max_expansions=5
            )
            entity['expanded_references'] = expanded[1:] if len(expanded) > 1 else []
        
        return entity
    
    async def retrieve_with_filters(
        self,
        query: str,
        filters: Dict[str, Any],
        collection_names: Optional[List[str]] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve with metadata filters
        
        Args:
            query: Query text
            filters: Metadata filters (e.g., {'state': 'Uttarakhand', 'category': 'pilgrimage_himalayan'})
            collection_names: Collections to search (default: all entity collections)
            n_results: Number of results
        
        Returns:
            Filtered results
        """
        if collection_names is None:
            collection_names = list(self.entity_type_collections.values())
        
        all_results = []
        
        for collection_name in collection_names:
            try:
                results_data = self.vector_store.query(
                    query_text=query,
                    collection_name=collection_name,
                    n_results=n_results,
                    where=filters
                )
                
                # Format results
                if results_data.get('documents') and results_data['documents'][0]:
                    for i in range(len(results_data['documents'][0])):
                        all_results.append({
                            'content': results_data['documents'][0][i],
                            'metadata': results_data['metadatas'][0][i],
                            'distance': results_data['distances'][0][i],
                            'collection': collection_name,
                            'final_score': 1.0 - results_data['distances'][0][i]
                        })
            
            except Exception as e:
                logger.error(f"Error querying {collection_name} with filters: {str(e)}")
        
        # Sort by score
        all_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return all_results[:n_results]
    
    # ==================== EXISTING METHODS ====================
    
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
            result_entity_id = result.get('metadata', {}).get('entity_id')
            
            for unique_result in unique_results:
                unique_content = unique_result.get('content', '').lower()
                unique_entity_id = unique_result.get('metadata', {}).get('entity_id')
                
                # Check for same entity ID (definite duplicate)
                if result_entity_id and result_entity_id == unique_entity_id:
                    is_duplicate = True
                    break
                
                # Check content similarity
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
            "vector_store_stats": self.vector_store.get_all_stats(),
            "persona_strategies": list(self.persona_strategies.keys()),
            "supported_intents": list(self.intent_collections.keys()),
            "entity_type_collections": self.entity_type_collections,
            "executor_stats": {
                "max_workers": self.executor._max_workers,
                "active_threads": len(self.executor._threads) if hasattr(self.executor, '_threads') else 0
            },
            "collection_status": {}
        }
        
        # Check which collections are populated
        for collection_name in self.vector_store.collections.keys():
            col_stats = self.vector_store.get_collection_stats(collection_name)
            stats["collection_status"][collection_name] = {
                "document_count": col_stats.get("document_count", 0),
                "active": col_stats.get("document_count", 0) > 0
            }
        
        return stats
