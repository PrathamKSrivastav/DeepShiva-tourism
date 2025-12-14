import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import uuid
from urllib.parse import urljoin, urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

class DocumentProcessor:
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter with smart splitting
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
            length_function=len
        )
        
        # Content type classifiers (simple keyword-based)
        self.content_classifiers = {
            "spiritual": [
                "temple", "darshan", "puja", "spiritual", "deity", "god", "goddess",
                "mandir", "meditation", "prayer", "sacred", "holy", "divine",
                "kedarnath", "badrinath", "gangotri", "yamunotri", "char dham"
            ],
            "trekking": [
                "trek", "hiking", "mountain", "altitude", "climbing", "adventure",
                "peak", "valley", "glacier", "trail", "expedition", "camping",
                "valley of flowers", "roopkund", "kedarkantha"
            ],
            "cultural": [
                "culture", "tradition", "festival", "folk", "heritage", "history",
                "legend", "mythology", "custom", "ritual", "art", "dance",
                "ganga dussehra", "kumbh mela", "uttarakhand culture"
            ],
            "government": [
                "government", "policy", "regulation", "official", "permit",
                "license", "authority", "department", "tourism board", "administration"
            ]
        }
        
        # JSON entity type handlers - FIXED: Use snake_case to match _detect_entity_type output
        self.json_entity_handlers = {
            "spiritual_site": self._chunk_spiritual_site,
            "festival": self._chunk_festival,
            "crowd_pattern": self._chunk_crowd_pattern,
            "homestay": self._chunk_homestay,
            "persona": self._chunk_persona,
            "trek": self._chunk_trek,
            "cuisine": self._chunk_cuisine,
            "wellness": self._chunk_wellness,
            "eco_tip": self._chunk_eco_tip,
            "emergency_info": self._chunk_emergency_info,
            "shloka": self._chunk_shloka,
        }

    # ===== JSON PROCESSING METHODS =====
    
    def process_json(self, file_path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Process JSON file and extract entity-level chunks
        
        Returns:
            Tuple of (chunks, metadata_list)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Detect entity type from filename
            entity_type = self._detect_entity_type(file_path)
            
            # Get handler for this entity type
            handler = self.json_entity_handlers.get(
                entity_type, 
                self._chunk_generic_json
            )
            
            # Extract entities from JSON structure
            entities = self._extract_entities(data, entity_type)
            
            if not entities:
                logger.warning(f"No entities found in {file_path.name}")
                return [], []
            
            all_chunks = []
            all_metadata = []
            
            # Process each entity
            for entity in entities:
                try:
                    chunks, metadata = handler(entity, file_path, entity_type)
                    all_chunks.extend(chunks)
                    all_metadata.extend(metadata)
                except Exception as e:
                    logger.error(f"Error processing entity {entity.get('id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(
                f"Processed {file_path.name}: "
                f"{len(entities)} entities → {len(all_chunks)} chunks"
            )
            
            return all_chunks, all_metadata
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {str(e)}")
            return [], []
        except Exception as e:
            logger.error(f"Error processing JSON {file_path}: {str(e)}")
            return [], []
    
    def _chunk_spiritual_site(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk spiritual site entity"""
        chunks = []
        metadata_list = []
        
        # Build entity-level content
        content_fields = [
            ('Name', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('History', entity.get('short_history', '')),
            ('Mythology', entity.get('mythological_significance', '')),
            ('Rituals', entity.get('rituals_and_practices', '')),
            ('Travel Tips', entity.get('local_travel_tips', '')),
            ('Common Mistakes to Avoid', entity.get('avoid_common_mistake', '')),
            ('Best Season', entity.get('best_season', '')),
            ('Nearby Attractions', entity.get('nearby_attractions', '')),
        ]
        
        entity_content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        # Base metadata
        base_metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'spiritual_site',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'state': entity.get('state'),
            'category': entity.get('category'),
            'region_specific': entity.get('region_specific'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'altitude_m': entity.get('altitude_m'),
            'ideal_trip_duration_days': entity.get('ideal_trip_duration_days'),
            'best_season': entity.get('best_season'),
            'opening_hours': entity.get('opening_hours'),
            'related_festivals': entity.get('related_festivals', []),
            'related_crowd_pattern': entity.get('related_crowd_pattern'),
            'related_treks': entity.get('related_treks', []),
            'related_sites': entity.get('related_sites', []),
            'related_emergencies': entity.get('related_emergencies', []),
            'recommended_for': entity.get('recommended_for', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        # Add main entity chunk
        chunks.append(entity_content)
        metadata_list.append(base_metadata.copy())
        
        # Sub-chunk long fields if needed
        long_fields = ['mythological_significance', 'rituals_and_practices', 'local_travel_tips']
        for field in long_fields:
            field_content = entity.get(field, '')
            if len(field_content) > 500:
                sub_chunks = self._split_long_field(field_content, 500)
                for idx, sub_chunk in enumerate(sub_chunks):
                    sub_metadata = base_metadata.copy()
                    sub_metadata.update({
                        'field_name': field,
                        'chunk_index': idx,
                        'total_sub_chunks': len(sub_chunks),
                        'is_sub_chunk': True
                    })
                    chunks.append(f"{entity.get('name')} - {field.replace('_', ' ').title()}:\n\n{sub_chunk}")
                    metadata_list.append(sub_metadata)
        
        return chunks, metadata_list
    
    def _chunk_festival(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk festival entity"""
        content_fields = [
            ('Festival Name', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Category', entity.get('category', '')),
            ('Regions', ', '.join(entity.get('states_celebrated', []))),
            ('Main Locations', ', '.join(entity.get('main_locations', []))),
            ('Typical Months', ', '.join(entity.get('typical_months', []))),
            ('Description', entity.get('description', '')),
            ('Mythological Background', entity.get('mythological_background', '')),
            ('Crowd Impact', entity.get('crowd_impact', '')),
            ('Travel Tips', entity.get('travel_tips', '')),
            ('Weather', entity.get('usual_weather', '')),
            ('Recommended Experiences', entity.get('recommended_experiences', '')),
            ('Common Mistakes', entity.get('avoid_common_mistake', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'festival',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'category': entity.get('category'),
            'region_specific': entity.get('region_specific'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'states_celebrated': entity.get('states_celebrated', []),
            'typical_months': entity.get('typical_months', []),
            'related_sites': entity.get('related_sites', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_crowd_pattern(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk crowd pattern entity"""
        content_fields = [
            ('Location', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Peak Months', ', '.join(entity.get('peak_months', []))),
            ('Off-Season', ', '.join(entity.get('off_season_months', []))),
            ('Weekend Spike', entity.get('weekend_spike', '')),
            ('Festival Spikes', ', '.join(entity.get('festival_spikes', []))),
            ('Typical Wait Time (Low)', entity.get('typical_wait_time_low', '')),
            ('Typical Wait Time (High)', entity.get('typical_wait_time_high', '')),
            ('Crowd Summary', entity.get('crowd_level_summary', '')),
            ('Common Mistake', entity.get('avoid_common_mistake', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'crowd_pattern',
            'source_file': file_path.name,
            'place_id': entity.get('place_id'),  # Links to spiritual site
            'name': entity.get('name'),
            'state': entity.get('state'),
            'category': entity.get('category'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'peak_months': entity.get('peak_months', []),
            'off_season_months': entity.get('off_season_months', []),
            'weekend_spike': entity.get('weekend_spike'),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_homestay(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk homestay entity"""
        content_fields = [
            ('Name', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Location', f"{entity.get('region_specific', '')}, {entity.get('state', '')}"),
            ('Nearest City', entity.get('nearest_city', '')),
            ('Price Range', entity.get('price_range', '')),
            ('Eco Rating', entity.get('eco_rating', '')),
            ('Description', entity.get('description', '')),
            ('Unique Experiences', ', '.join(entity.get('unique_experiences', []))),
            ('Local Food', ', '.join(entity.get('local_food_specialties', []))),
            ('Best Season', entity.get('best_season', '')),
            ('Suitable For', ', '.join(entity.get('suitable_for', []))),
            ('Common Mistake', entity.get('avoid_common_mistake', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'homestay',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'state': entity.get('state'),
            'region_specific': entity.get('region_specific'),
            'category': entity.get('category'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'price_range': entity.get('price_range'),
            'eco_rating': entity.get('eco_rating'),
            'effort_level': entity.get('effort_level'),
            'suitable_for': entity.get('suitable_for', []),
            'related_treks': entity.get('related_treks', []),
            'related_sites': entity.get('related_sites', []),
            'related_wellness': entity.get('related_wellness', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_persona(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk persona entity - special handling for system_prompt"""
        chunks = []
        metadata_list = []
        
        # Main persona summary
        content_fields = [
            ('Persona', entity.get('name', '')),
            ('Category', entity.get('category', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Description', entity.get('description', '')),
            ('Typical Use Cases', ', '.join(entity.get('typical_use_cases', []))),
            ('Style Guidelines', entity.get('style_guidelines', '')),
            ('Cross Role Usage', entity.get('cross_role_usage', '')),
            ('Common Mistake', entity.get('avoid_common_mistake', '')),
        ]
        
        summary_content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        base_metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'persona',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'category': entity.get('category'),
            'typical_use_cases': entity.get('typical_use_cases', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        chunks.append(summary_content)
        metadata_list.append(base_metadata.copy())
        
        # Sub-chunk system_prompt (large field)
        system_prompt = entity.get('system_prompt', '')
        if system_prompt and len(system_prompt) > 500:
            prompt_chunks = self._split_long_field(system_prompt, 500)
            for idx, chunk in enumerate(prompt_chunks):
                sub_metadata = base_metadata.copy()
                sub_metadata.update({
                    'field_name': 'system_prompt',
                    'chunk_index': idx,
                    'total_sub_chunks': len(prompt_chunks),
                    'is_sub_chunk': True
                })
                chunks.append(f"{entity.get('name')} - System Prompt Part {idx+1}:\n\n{chunk}")
                metadata_list.append(sub_metadata)
        
        return chunks, metadata_list
    
    def _chunk_trek(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk trek entity"""
        content_fields = [
            ('Trek Name', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Location', f"{entity.get('region_specific', '')}, {entity.get('state', '')}"),
            ('Difficulty', entity.get('difficulty_level', '')),
            ('Duration', entity.get('duration_days', '')),
            ('Max Altitude', entity.get('max_altitude_m', '')),
            ('Description', entity.get('description', '')),
            ('Best Season', entity.get('best_season', '')),
            ('Safety Tips', entity.get('safety_tips', '')),
            ('Common Mistake', entity.get('avoid_common_mistake', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'trek',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'state': entity.get('state'),
            'region_specific': entity.get('region_specific'),
            'difficulty_level': entity.get('difficulty_level'),
            'duration_days': entity.get('duration_days'),
            'max_altitude_m': entity.get('max_altitude_m'),
            'best_season': entity.get('best_season'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'related_sites': entity.get('related_sites', []),
            'related_emergencies': entity.get('related_emergencies', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_cuisine(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk cuisine entity"""
        content_fields = [
            ('Dish Name', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Region', f"{entity.get('region_specific', '')}, {entity.get('state', '')}"),
            ('Category', entity.get('category', '')),
            ('Description', entity.get('description', '')),
            ('Where to Try', entity.get('where_to_try', '')),
            ('Best Season', entity.get('best_season', '')),
            ('Common Mistake', entity.get('avoid_common_mistake', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'cuisine',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'state': entity.get('state'),
            'region_specific': entity.get('region_specific'),
            'category': entity.get('category'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'dietary_type': entity.get('dietary_type'),
            'related_sites': entity.get('related_sites', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_wellness(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk wellness entity"""
        content_fields = [
            ('Practice Name', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Category', entity.get('category', '')),
            ('Description', entity.get('description', '')),
            ('Benefits', entity.get('benefits', '')),
            ('Best Time', entity.get('best_time', '')),
            ('Where to Practice', entity.get('where_to_practice', '')),
            ('Common Mistake', entity.get('avoid_common_mistake', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'wellness',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'category': entity.get('category'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'related_sites': entity.get('related_sites', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_eco_tip(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk eco tip entity"""
        content_fields = [
            ('Tip Title', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Category', entity.get('category', '')),
            ('Description', entity.get('description', '')),
            ('Why Important', entity.get('why_important', '')),
            ('How to Implement', entity.get('how_to_implement', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'eco_tip',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'category': entity.get('category'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_emergency_info(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk emergency info entity"""
        content_fields = [
            ('Emergency Type', entity.get('name', '')),
            ('Quick Summary', entity.get('quick_version', '')),
            ('Category', entity.get('category', '')),
            ('Description', entity.get('description', '')),
            ('Immediate Actions', entity.get('immediate_actions', '')),
            ('Prevention Tips', entity.get('prevention_tips', '')),
            ('Emergency Contacts', entity.get('emergency_contacts', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'emergency_info',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'category': entity.get('category'),
            'severity_level': entity.get('severity_level'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'related_sites': entity.get('related_sites', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_shloka(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Chunk shloka entity"""
        content_fields = [
            ('Shloka Name', entity.get('name', '')),
            ('Sanskrit Text', entity.get('sanskrit_text', '')),
            ('Translation', entity.get('english_translation', '')),
            ('Meaning', entity.get('meaning', '')),
            ('Context', entity.get('context', '')),
            ('When to Recite', entity.get('when_to_recite', '')),
        ]
        
        content = "\n\n".join(
            f"{label}: {value}" 
            for label, value in content_fields 
            if value
        )
        
        metadata = {
            'entity_id': entity.get('id'),
            'entity_type': 'shloka',
            'source_file': file_path.name,
            'name': entity.get('name'),
            'category': entity.get('category'),
            'deity': entity.get('deity'),
            'recommended_persona': entity.get('recommended_persona_id'),
            'related_sites': entity.get('related_sites', []),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    def _chunk_generic_json(
        self, 
        entity: Dict, 
        file_path: Path,
        entity_type: str
    ) -> Tuple[List[str], List[Dict]]:
        """Generic chunker for unknown JSON types"""
        content = json.dumps(entity, indent=2, ensure_ascii=False)
        
        metadata = {
            'entity_id': entity.get('id', str(uuid.uuid4())),
            'entity_type': 'generic',
            'source_file': file_path.name,
            'name': entity.get('name', 'Unknown'),
            'processed_at': self._get_current_timestamp(),
            'is_sub_chunk': False
        }
        
        return [content], [metadata]
    
    # ===== HELPER METHODS =====
    
    def _detect_entity_type(self, file_path: Path) -> str:
        """Detect entity type from filename (handles timestamped managed files)"""
        filename = file_path.stem
        
        # Remove timestamp prefix (format: YYYYMMDD_HHMMSS_originalname)
        parts = filename.split('_')
        if len(parts) >= 3 and parts[0].isdigit() and len(parts[0]) == 8:
            original_name = '_'.join(parts[2:])
        else:
            original_name = filename
        
        # Map to entity types
        type_map = {
            'spiritualSites': 'spiritual_site',
            'festivals': 'festival',
            'crowdPatterns': 'crowd_pattern',
            'homestays': 'homestay',
            'personas': 'persona',
            'treks': 'trek',
            'cuisines': 'cuisine',
            'wellness': 'wellness',
            'ecoTips': 'eco_tip',
            'emergencyInfo': 'emergency_info',
            'shlokas': 'shloka',
        }
        
        detected_type = type_map.get(original_name, 'generic')
        logger.info(f"Detected entity type '{detected_type}' from filename: {original_name}")
        
        return detected_type

    def _extract_entities(self, data: Dict, entity_type: str) -> List[Dict]:
        """Extract entities array from JSON structure"""
        if not data:
            logger.warning(f"Empty JSON data for entity type: {entity_type}")
            return []
        
        # Strategy 1: Direct list values
        for key, value in data.items():
            if isinstance(value, list):
                logger.info(f"Found {len(value)} entities in key '{key}' (direct list)")
                return value
        
        # Strategy 2: Nested structures (like spiritualSites.json)
        for key, value in data.items():
            if isinstance(value, dict):
                for nested_key, nested_value in value.items():
                    if isinstance(nested_value, list):
                        logger.info(f"Found {len(nested_value)} entities in '{key}.{nested_key}' (nested)")
                        return nested_value
        
        # Strategy 3: Root is list
        if isinstance(data, list):
            logger.info(f"Found {len(data)} entities (root is list)")
            return data
        
        logger.warning(f"No list found in JSON. Keys: {list(data.keys())}")
        return []


    
    def _split_long_field(self, text: str, max_chars: int) -> List[str]:
        """Split long text at sentence boundaries"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_len = len(sentence) + 1
            if current_length + sentence_len > max_chars and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_length = sentence_len
            else:
                current_chunk.append(sentence)
                current_length += sentence_len
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    # ===== EXISTING METHODS (PDF, WEB, TEXT) =====
    
    def process_pdf(self, file_path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process PDF file and extract text chunks"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                full_text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        full_text += f"\n--- Page {page_num + 1} ---\n{page_text}"
            
            if not full_text.strip():
                logger.warning(f"No text extracted from PDF: {file_path}")
                return [], []
            
            cleaned_text = self._clean_text(full_text)
            chunks = self.text_splitter.split_text(cleaned_text)
            content_type = self._classify_content_type(cleaned_text)
            
            metadata_list = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "source": str(file_path),
                    "source_type": "pdf",
                    "file_name": file_path.name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "content_type": content_type,
                    "char_count": len(chunk),
                    "processed_at": self._get_current_timestamp()
                }
                metadata_list.append(metadata)
            
            logger.info(f"Processed PDF {file_path.name}: {len(chunks)} chunks, type: {content_type}")
            return chunks, metadata_list
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return [], []
    
    def process_web_page(self, url: str, content: Optional[str] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process web page content"""
        try:
            if content is None:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                content = response.text
            
            soup = BeautifulSoup(content, 'html.parser')
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            text = soup.get_text()
            cleaned_text = self._clean_text(text)
            
            if not cleaned_text.strip():
                logger.warning(f"No text extracted from URL: {url}")
                return [], []
            
            chunks = self.text_splitter.split_text(cleaned_text)
            content_type = self._classify_content_type(cleaned_text)
            title = soup.title.string if soup.title else urlparse(url).netloc
            
            metadata_list = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "source": url,
                    "source_type": "web_page",
                    "title": title,
                    "domain": urlparse(url).netloc,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "content_type": content_type,
                    "char_count": len(chunk),
                    "processed_at": self._get_current_timestamp()
                }
                metadata_list.append(metadata)
            
            logger.info(f"Processed web page {url}: {len(chunks)} chunks, type: {content_type}")
            return chunks, metadata_list
            
        except Exception as e:
            logger.error(f"Error processing web page {url}: {str(e)}")
            return [], []
    
    def process_text_file(self, file_path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            if not text.strip():
                logger.warning(f"Empty text file: {file_path}")
                return [], []
            
            cleaned_text = self._clean_text(text)
            chunks = self.text_splitter.split_text(cleaned_text)
            content_type = self._classify_content_type(cleaned_text)
            
            metadata_list = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "source": str(file_path),
                    "source_type": "text_file",
                    "file_name": file_path.name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "content_type": content_type,
                    "char_count": len(chunk),
                    "processed_at": self._get_current_timestamp()
                }
                metadata_list.append(metadata)
            
            logger.info(f"Processed text file {file_path.name}: {len(chunks)} chunks, type: {content_type}")
            return chunks, metadata_list
            
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            return [], []
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        text = re.sub(r'\S+@\S+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _classify_content_type(self, text: str) -> str:
        """Classify content type based on keywords"""
        text_lower = text.lower()
        scores = {}
        
        for content_type, keywords in self.content_classifiers.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            if score > 0:
                scores[content_type] = score
        
        if not scores:
            return "general"
        
        return max(scores, key=scores.get)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.now().isoformat()
    
    def batch_process_directory(self, directory: Path, file_extensions: List[str] = None) -> Dict[str, Any]:
        """Batch process all supported files in a directory"""
        if file_extensions is None:
            file_extensions = ['.pdf', '.txt', '.md', '.json']
        
        results = {
            "processed_files": 0,
            "total_chunks": 0,
            "failed_files": [],
            "content_types": {},
            "files_by_type": {}
        }
        
        directory = Path(directory)
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return results
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                try:
                    if file_path.suffix.lower() == '.pdf':
                        chunks, metadata_list = self.process_pdf(file_path)
                    elif file_path.suffix.lower() == '.json':
                        chunks, metadata_list = self.process_json(file_path)
                    else:
                        chunks, metadata_list = self.process_text_file(file_path)
                    
                    if chunks:
                        results["processed_files"] += 1
                        results["total_chunks"] += len(chunks)
                        
                        content_type = metadata_list[0].get("entity_type") or metadata_list[0].get("content_type", "general")
                        results["content_types"][content_type] = results["content_types"].get(content_type, 0) + len(chunks)
                        
                        file_type = file_path.suffix.lower()
                        results["files_by_type"][file_type] = results["files_by_type"].get(file_type, 0) + 1
                        
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {str(e)}")
                    results["failed_files"].append(str(file_path))
        
        return results
