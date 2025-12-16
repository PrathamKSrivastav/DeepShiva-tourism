# tools/trek_tool.py

import os
import pandas as pd
import re
from typing import Optional, Dict, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class IndianTrekTool:
    """Fetch Indian trek information - Kaggle primary source"""
    
    def __init__(self, cache_dir: str = None):
        # Use trek_cache folder relative to this file
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "trek_cache")
        
        self.cache_dir = cache_dir
        self.kaggle_data = None
        
        # Create cache directory
        os.makedirs(cache_dir, exist_ok=True)
        
        # Set Kaggle credentials
        self._setup_kaggle_credentials()
        
        # Load Kaggle data
        self._load_kaggle_cache()
    
    def _setup_kaggle_credentials(self):
        """Set Kaggle credentials from environment variables"""
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            kaggle_username = os.getenv('KAGGLE_USERNAME')
            kaggle_key = os.getenv('KAGGLE_KEY')
            
            if kaggle_username and kaggle_key:
                os.environ['KAGGLE_USERNAME'] = kaggle_username
                os.environ['KAGGLE_KEY'] = kaggle_key
                logger.info("✅ Kaggle credentials loaded")
            else:
                logger.error("❌ KAGGLE_USERNAME or KAGGLE_KEY not found in .env")
        except Exception as e:
            logger.error(f"❌ Error loading credentials: {e}")
    
    def _load_kaggle_cache(self):
        """Load Kaggle dataset from cache or download"""
        cache_file = os.path.join(self.cache_dir, "india_treks.csv")
        
        # Try loading from cache first
        if os.path.exists(cache_file):
            try:
                self.kaggle_data = pd.read_csv(cache_file)
                logger.info(f"✅ Loaded {len(self.kaggle_data)} treks from cache: {cache_file}")
                return
            except Exception as e:
                logger.warning(f"⚠️  Cache read failed: {e}")
        
        # Try downloading fresh
        self._download_kaggle_dataset(cache_file)
    
    def _parse_trek_txt_file(self, filepath: str) -> Optional[Dict]:
        """Parse individual trek .txt file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extract trek name from filename
            filename = os.path.basename(filepath)
            trek_name = filename.replace('.txt', '').replace('-', ' ').title()
            
            # Initialize trek data
            trek_data = {
                'Trek Name': trek_name,
                'Region': 'Unknown',
                'Difficulty': 'Unknown',
                'Duration': 'Unknown',
                'Distance': 'Unknown',
                'Altitude': 'Unknown',
                'Best Time': 'Unknown',
                'Description': content[:500]  # First 500 chars as description
            }
            
            # Extract structured data using regex patterns
            patterns = {
                'Region': r'(?:Region|State|Location)[\s:]+([A-Za-z\s]+?)(?:\n|,|\.)',
                'Difficulty': r'(?:Difficulty|Level)[\s:]+(\w+)',
                'Duration': r'(?:Duration|Days)[\s:]+([0-9\-]+\s*(?:days?|hrs?))',
                'Distance': r'(?:Distance|Length)[\s:]+([0-9\.]+\s*(?:km|kms?))',
                'Altitude': r'(?:Altitude|Height|Elevation)[\s:]+([0-9,]+\s*(?:m|ft|feet|meters?))',
                'Best Time': r'(?:Best Time|Season)[\s:]+([A-Za-z\s\-]+)'
            }
            
            for field, pattern in patterns.items():
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    trek_data[field] = match.group(1).strip()
            
            # Special handling for common regions
            content_lower = content.lower()
            if 'uttarakhand' in content_lower:
                trek_data['Region'] = 'Uttarakhand'
            elif 'himachal' in content_lower:
                trek_data['Region'] = 'Himachal Pradesh'
            elif 'kashmir' in content_lower or 'jammu' in content_lower:
                trek_data['Region'] = 'Jammu & Kashmir'
            elif 'ladakh' in content_lower:
                trek_data['Region'] = 'Ladakh'
            elif 'sikkim' in content_lower:
                trek_data['Region'] = 'Sikkim'
            elif 'maharashtra' in content_lower:
                trek_data['Region'] = 'Maharashtra'
            elif 'karnataka' in content_lower:
                trek_data['Region'] = 'Karnataka'
            elif 'kerala' in content_lower:
                trek_data['Region'] = 'Kerala'
            
            return trek_data
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to parse {filepath}: {e}")
            return None
    
    def _download_kaggle_dataset(self, cache_file: str):
        """Download Kaggle dataset and parse text files"""
        try:
            # Check credentials first
            if not os.getenv('KAGGLE_USERNAME') or not os.getenv('KAGGLE_KEY'):
                logger.error("❌ Cannot download: Kaggle credentials missing")
                logger.error("   Add KAGGLE_USERNAME and KAGGLE_KEY to your .env file")
                return
            
            import kagglehub
            
            logger.info("⬇️  Downloading trek dataset from Kaggle...")
            logger.info("   Dataset: iamrahulpatil/250-trek-description")
            
            # Download dataset
            download_path = kagglehub.dataset_download("iamrahulpatil/250-trek-description")
            logger.info(f"📂 Downloaded to: {download_path}")
            
            # Find all .txt files
            txt_files = []
            for root, dirs, files in os.walk(download_path):
                for file in files:
                    if file.endswith('.txt') and file != 'indiahikes.html':
                        txt_files.append(os.path.join(root, file))
            
            if not txt_files:
                logger.error(f"❌ No .txt files found in {download_path}")
                return
            
            logger.info(f"📄 Found {len(txt_files)} trek text files")
            logger.info("🔄 Parsing trek files...")
            
            # Parse all text files
            trek_list = []
            for txt_file in txt_files:
                trek_data = self._parse_trek_txt_file(txt_file)
                if trek_data:
                    trek_list.append(trek_data)
            
            if not trek_list:
                logger.error("❌ Failed to parse any trek files")
                return
            
            # Create DataFrame
            df = pd.DataFrame(trek_list)
            
            # Save to cache
            df.to_csv(cache_file, index=False)
            self.kaggle_data = df
            
            logger.info(f"✅ Parsed {len(df)} treks from Kaggle")
            logger.info(f"✅ Cached to: {cache_file}")
            logger.info(f"📊 Columns: {list(df.columns)}")
            logger.info(f"📊 Regions found: {df['Region'].value_counts().to_dict()}")
            
        except ImportError:
            logger.error("❌ kagglehub not installed")
            logger.error("   Install: pip install kagglehub")
        except Exception as e:
            logger.error(f"❌ Kaggle download failed: {str(e)}")
            logger.error(f"   Error type: {type(e).__name__}")
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
    
    async def search_treks_by_region(self, region: str) -> List[Dict]:
        """Search treks by Indian region"""
        logger.info(f"🗺️  Searching: {region}")
        
        if self.kaggle_data is None:
            logger.error("❌ Kaggle dataset not loaded - cannot search")
            return []
        
        # Search Kaggle
        results = self._search_kaggle_by_region(region)
        
        if results:
            logger.info(f"✅ Found {len(results)} treks in {region}")
            return results
        
        logger.warning(f"⚠️  No results for {region}")
        return []
    
    async def search_trek_by_name(self, trek_name: str) -> Optional[Dict]:
        """Search for specific trek"""
        logger.info(f"🏔️  Searching: '{trek_name}'")
        
        if self.kaggle_data is None:
            logger.error("❌ Kaggle dataset not loaded")
            return None
        
        result = self._search_kaggle_by_name(trek_name)
        
        if result:
            logger.info(f"✅ Found: {result['name']}")
            return result
        
        logger.warning(f"⚠️  '{trek_name}' not found")
        return None
    
    def _search_kaggle_by_region(self, region: str) -> List[Dict]:
        """Search by region with fallback matching"""
        if self.kaggle_data is None:
            return []
        
        region_clean = region.lower().strip()
        
        # Try exact region match first
        mask = self.kaggle_data['Region'].astype(str).str.lower().str.contains(region_clean, na=False)
        filtered = self.kaggle_data[mask]
        
        if len(filtered) == 0:
            # Try keyword matching in all fields
            logger.info(f"📊 No exact match, trying full-text search...")
            mask = self.kaggle_data.apply(
                lambda row: region_clean in str(row).lower(),
                axis=1
            )
            filtered = self.kaggle_data[mask]
        
        logger.info(f"📊 Found {len(filtered)} matches")
        return self._format_kaggle_data(filtered)
    
    def _search_kaggle_by_name(self, trek_name: str) -> Optional[Dict]:
        """Search by trek name"""
        if self.kaggle_data is None:
            return None
        
        trek_clean = trek_name.lower().strip()
        
        # Search in Trek Name column
        mask = self.kaggle_data['Trek Name'].astype(str).str.lower().str.contains(trek_clean, na=False)
        results = self.kaggle_data[mask]
        
        if not results.empty:
            logger.info(f"✓ Found match")
            formatted = self._format_kaggle_data(results)
            return formatted[0] if formatted else None
        
        return None
    
    def _format_kaggle_data(self, df: pd.DataFrame) -> List[Dict]:
        """Format dataframe to dict"""
        treks = []
        df_limited = df.head(15)
        
        for _, row in df_limited.iterrows():
            trek_info = {
                'name': str(row.get('Trek Name', 'Unknown')),
                'type': 'hiking',
                'difficulty': str(row.get('Difficulty', 'Unknown')),
                'description': str(row.get('Description', ''))[:250],
                'distance': str(row.get('Distance', 'Unknown')),
                'region': str(row.get('Region', 'Unknown')),
                'duration': str(row.get('Duration', 'Unknown')),
                'altitude': str(row.get('Altitude', 'Unknown')),
                'best_time': str(row.get('Best Time', 'Unknown')),
                'source': 'India Treks Database (250+ Treks)'
            }
            treks.append(trek_info)
        
        return treks


# Singleton
_trek_tool = None

def get_trek_tool() -> IndianTrekTool:
    """Get trek tool singleton"""
    global _trek_tool
    if _trek_tool is None:
        _trek_tool = IndianTrekTool()
    return _trek_tool


async def search_treks(region: Optional[str] = None, trek_name: Optional[str] = None) -> Optional[Dict]:
    """
    Search Indian treks by region or name
    """
    tool = get_trek_tool()
    
    try:
        # Name search
        if trek_name:
            result = await tool.search_trek_by_name(trek_name)
            if result:
                return {
                    'trek_found': True,
                    'trek_count': 1,
                    'treks': [result],
                    'source': 'India Treks Database'
                }
            return None
        
        # Region search
        if region:
            results = await tool.search_treks_by_region(region)
            if results:
                return {
                    'trek_found': True,
                    'trek_count': len(results),
                    'region': region,
                    'treks': results,
                    'source': 'India Treks Database'
                }
            return None
        
        logger.warning("⚠️  No region or trek_name provided")
        return None
        
    except Exception as e:
        logger.error(f"❌ Search error: {str(e)}")
        return None
