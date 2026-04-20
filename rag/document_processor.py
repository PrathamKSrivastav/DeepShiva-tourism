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
                "ganga dussehra", "kumbh mela", "indian culture"
            ],
            "government": [
                "government", "policy", "regulation", "official", "permit",
                "license", "authority", "department", "tourism board", "administration"
            ]
        }
        
        
    
    # ADD THIS NEW METHOD at line ~30
    def _classify_to_collection(self, content: str, metadata: Dict) -> str:
        """
        Classify content into one of 4 collections: cultural, trekking, government, general
        """
        content_lower = content.lower()
        
        # Check metadata first
        entity_type = metadata.get('entity_type', '')
        source_file = metadata.get('source_file', '').lower()
        
        # Priority 1: Filename-based classification (most reliable)
        if 'swadesh' in source_file or 'guideline' in source_file:
            logger.debug(f"Classified as 'government' based on filename: {source_file}")
            return 'government'
        
        if 'health' in source_file or 'wellness' in source_file:
            # Health PDFs can be government OR trekking depending on content
            if 'who' in content_lower or 'ministry' in content_lower:
                logger.debug(f"Classified as 'government' based on filename+content: {source_file}")
                return 'government'
        
        if 'hinduism' in source_file or 'geeta' in source_file or 'spiritual' in source_file:
            logger.debug(f"Classified as 'cultural' based on filename: {source_file}")
            return 'cultural'
        
        if 'trek' in source_file or 'peak' in source_file or 'mountain' in source_file:
            logger.debug(f"Classified as 'trekking' based on filename: {source_file}")
            return 'trekking'
        
        if 'maharastra' in source_file or 'fort' in source_file:
            logger.debug(f"Classified as 'trekking' (forts) based on filename: {source_file}")
            return 'trekking'
        
        # Priority 2: Entity type based routing (for JSON)
        entity_cultural = ['spiritual_site', 'festival', 'crowd_pattern', 'homestay', 'cuisine', 'shloka']
        entity_trekking = ['trek', 'emergency_info', 'eco_tip', 'wellness']
        entity_government = ['persona', 'policy', 'regulation']
        
        if entity_type in entity_cultural:
            logger.debug(f"Classified as 'cultural' based on entity_type: {entity_type}")
            return 'cultural'
        elif entity_type in entity_trekking:
            logger.debug(f"Classified as 'trekking' based on entity_type: {entity_type}")
            return 'trekking'
        elif entity_type in entity_government:
            logger.debug(f"Classified as 'government' based on entity_type: {entity_type}")
            return 'government'
        
        # Priority 3: Content keyword-based scoring
        cultural_keywords = [
            'temple', 'spiritual', 'deity', 'god', 'goddess', 'festival', 'puja',
            'sacred', 'holy', 'pilgrimage', 'shrine', 'monastery', 'mythology',
            'heritage', 'tradition', 'ritual', 'religious', 'shloka', 'mandir',
            'cuisine', 'homestay', 'cultural', 'crowd', 'darshan', 'prayer',
            'vedic', 'hinduism', 'buddhism', 'jainism', 'devi', 'shiva', 'vishnu'
        ]
        
        trekking_keywords = [
            'trek', 'mountain', 'peak', 'altitude', 'climbing', 'hiking',
            'expedition', 'trail', 'glacier', 'valley', 'adventure', 'camping',
            'mountaineering', 'emergency', 'safety', 'rescue', 'fort', 'elevation'
        ]
        
        government_keywords = [
            'government', 'ministry', 'policy', 'regulation', 'official',
            'permit', 'license', 'authority', 'scheme', 'guideline', 'circular',
            'notification', 'order', 'department', 'board', 'act', 'rule', 'who'
        ]
        
        cultural_score = sum(1 for kw in cultural_keywords if kw in content_lower)
        trekking_score = sum(1 for kw in trekking_keywords if kw in content_lower)
        government_score = sum(1 for kw in government_keywords if kw in content_lower)
        
        scores = {
            'cultural': cultural_score,
            'trekking': trekking_score,
            'government': government_score
        }
        
        max_score = max(scores.values())
        
        # Return general if no clear match
        if max_score == 0:
            logger.warning(f" No classification match for: {source_file} - defaulting to 'general'")
            return 'general'
        
        # Warn if classification is ambiguous (scores are close)
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[0][1] - sorted_scores[1][1] <= 2:
            logger.warning(
                f" Ambiguous classification for {source_file}: "
                f"Top 2 scores: {sorted_scores[0]} vs {sorted_scores[1]}"
            )
        
        result = max(scores, key=scores.get)
        logger.debug(f"Classified as '{result}' based on content keywords: {scores}")
        return result



    # ===== JSON PROCESSING METHODS =====
        
    def process_json(self, file_path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Process JSON file - automatically classifies to 4 collections
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_chunks = []
            all_metadata = []
            entities = []  # Initialize here
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Direct list of entities
                entities = data
            elif isinstance(data, dict):
                #  UPDATED: Check for regional structure (handles both formats)
                region_keys = [
                    # Standard format
                    'north', 'south', 'east', 'west', 'central', 
                    'northeast', 'northwest', 'southeast', 'southwest',
                    # "_india" suffix format
                    'north_india', 'south_india', 'east_india', 'west_india', 'central_india'
                ]
                found_regions = [key for key in region_keys if key in data and isinstance(data[key], list)]
                
                if found_regions:
                    # Flatten all regional arrays into single entity list
                    for region in found_regions:
                        entities.extend(data[region])
                    logger.info(f"Found {len(entities)} entities across regions: {found_regions}")
                # Special handling for trek data (both dict and list formats)
                elif 'treks' in data:
                    treks_data = data.get('treks', [])
                    
                    if isinstance(treks_data, dict):
                        for difficulty, trek_list in treks_data.items():
                            if isinstance(trek_list, list):
                                for trek in trek_list:
                                    trek['difficulty'] = difficulty
                                    entities.append(trek)
                    elif isinstance(treks_data, list):
                        entities = treks_data
                    else:
                        logger.warning(f"Unexpected treks format in {file_path}: {type(treks_data)}")
                        entities = []
                else:
                    # Try common keys for entity lists
                    entities = data.get('data', data.get('items', data.get('records', data.get('entities', []))))
                    
                    # If still not a list, check if root dict has site data
                    if not isinstance(entities, list):
                        if any(key in data for key in ['name', 'site_name', 'title', 'id', 'site_id']):
                            entities = [data]
                        else:
                            entities = []
            else:
                logger.warning(f"Unexpected JSON structure in {file_path}: {type(data)}")
                return [], []
            
            if not entities:
                logger.warning(f"No entities found in {file_path}")
                return [], []
            
            logger.info(f"Processing {len(entities)} entities from {file_path.name}")
            
            for idx, entity in enumerate(entities):
                if not isinstance(entity, dict):
                    logger.warning(f"Skipping non-dict entity at index {idx}")
                    continue
                    
                # Create content string from all text fields
                content_parts = []
                for key, value in entity.items():
                    if isinstance(value, str) and value.strip():
                        content_parts.append(f"{key}: {value}")
                    elif isinstance(value, list):
                        list_str = ', '.join(str(v) for v in value if v)
                        if list_str:
                            content_parts.append(f"{key}: {list_str}")
                    elif isinstance(value, dict):
                        nested = ', '.join(f"{k}={v}" for k, v in value.items() if v)
                        if nested:
                            content_parts.append(f"{key}: {nested}")
                
                content = "\n".join(content_parts)
                
                if not content.strip():
                    logger.warning(f"Empty content for entity {idx} in {file_path.name}")
                    continue
                
                # Base metadata
                metadata = {
                    'source_file': file_path.name,
                    'source_type': 'json',
                    'entity_id': entity.get('id', entity.get('site_id', entity.get('name', str(idx)))),
                    'name': entity.get('name', entity.get('site_name', entity.get('title', f'Entity_{idx}'))),
                    'processed_at': self._get_current_timestamp()
                }
                
                # Auto-classify to one of 4 collections
                collection = self._classify_to_collection(content, metadata)
                metadata['content_type'] = collection
                
                # Chunk if too large (>1500 chars)
                if len(content) > 1500:
                    sub_chunks = self.text_splitter.split_text(content)
                    for chunk_idx, chunk in enumerate(sub_chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata['chunk_index'] = chunk_idx
                        chunk_metadata['total_chunks'] = len(sub_chunks)
                        all_chunks.append(chunk)
                        all_metadata.append(chunk_metadata)
                else:
                    all_chunks.append(content)
                    all_metadata.append(metadata)
            
            # Log classification summary
            collections_used = {}
            for meta in all_metadata:
                coll = meta.get('content_type', 'unknown')
                collections_used[coll] = collections_used.get(coll, 0) + 1
            
            logger.info(f" Processed {file_path.name}: {len(entities)} entities → {len(all_chunks)} chunks")
            logger.info(f"    Classification: {collections_used}")
            
            return all_chunks, all_metadata
            
        except Exception as e:
            logger.error(f"Error processing JSON {file_path}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return [], []



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
    
    def process_csv(self, file_path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Process CSV files"""
        import csv
        
        all_chunks = []
        all_metadata = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Create content from row
                    content_parts = [f"{k}: {v}" for k, v in row.items() if v]
                    content = "\n".join(content_parts)
                    
                    metadata = {
                        'source_file': file_path.name,
                        'source_type': 'csv',
                        'processed_at': self._get_current_timestamp()
                    }
                    
                    # Classify
                    collection = self._classify_to_collection(content, metadata)
                    metadata['content_type'] = collection
                    
                    all_chunks.append(content)
                    all_metadata.append(metadata)
            
            logger.info(f"Processed CSV {file_path.name}: {len(all_chunks)} rows")
            return all_chunks, all_metadata
            
        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {str(e)}")
            return [], []

