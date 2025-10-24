import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import requests
from bs4 import BeautifulSoup
import pypdf
from langchain.text_splitter import RecursiveCharacterTextSplitter
import re
import uuid
from urllib.parse import urljoin, urlparse

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
    
    def process_pdf(self, file_path: Path) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Process PDF file and extract text chunks
        
        Returns:
            Tuple of (chunks, metadata_list)
        """
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
                
                # Clean text
                cleaned_text = self._clean_text(full_text)
                
                # Split into chunks
                chunks = self.text_splitter.split_text(cleaned_text)
                
                # Classify content type
                content_type = self._classify_content_type(cleaned_text)
                
                # Create metadata for each chunk
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
        """
        Process web page content
        
        Args:
            url: Web page URL
            content: Optional pre-fetched content (if None, will fetch from URL)
        
        Returns:
            Tuple of (chunks, metadata_list)
        """
        try:
            if content is None:
                # Fetch content from URL
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                content = response.text
            
            # Parse HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean text
            cleaned_text = self._clean_text(text)
            
            if not cleaned_text.strip():
                logger.warning(f"No text extracted from URL: {url}")
                return [], []
            
            # Split into chunks
            chunks = self.text_splitter.split_text(cleaned_text)
            
            # Classify content type
            content_type = self._classify_content_type(cleaned_text)
            
            # Extract title
            title = soup.title.string if soup.title else urlparse(url).netloc
            
            # Create metadata for each chunk
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
        """
        Process plain text file
        
        Returns:
            Tuple of (chunks, metadata_list)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            
            if not text.strip():
                logger.warning(f"Empty text file: {file_path}")
                return [], []
            
            # Clean text
            cleaned_text = self._clean_text(text)
            
            # Split into chunks
            chunks = self.text_splitter.split_text(cleaned_text)
            
            # Classify content type
            content_type = self._classify_content_type(cleaned_text)
            
            # Create metadata for each chunk
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
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Clean up extra spaces again
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
        
        # Return type with highest score
        return max(scores, key=scores.get)
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def batch_process_directory(self, directory: Path, file_extensions: List[str] = None) -> Dict[str, Any]:
        """
        Batch process all supported files in a directory
        
        Args:
            directory: Directory path to process
            file_extensions: List of extensions to process (None = all supported)
        
        Returns:
            Processing results summary
        """
        if file_extensions is None:
            file_extensions = ['.pdf', '.txt', '.md']
        
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
                    else:  # text files
                        chunks, metadata_list = self.process_text_file(file_path)
                    
                    if chunks:
                        results["processed_files"] += 1
                        results["total_chunks"] += len(chunks)
                        
                        # Track content types
                        content_type = metadata_list[0]["content_type"] if metadata_list else "general"
                        results["content_types"][content_type] = results["content_types"].get(content_type, 0) + len(chunks)
                        
                        # Track files by type
                        file_type = file_path.suffix.lower()
                        results["files_by_type"][file_type] = results["files_by_type"].get(file_type, 0) + 1
                    
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {str(e)}")
                    results["failed_files"].append(str(file_path))
        
        return results
