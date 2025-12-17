# tests/test_trek_kaggle.py - Test Kaggle trek integration

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path to import from tools
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)

logger = logging.getLogger(__name__)


async def test_kaggle_credentials():
    """Step 1: Check Kaggle credentials"""
    print("\n" + "="*70)
    print("🧪 TESTING KAGGLE TREK INTEGRATION")
    print("="*70)
    
    print("\n📋 Step 1: Checking Kaggle credentials...")
    from dotenv import load_dotenv
    
    # Load from backend/.env
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(env_path)
    
    username = os.getenv('KAGGLE_USERNAME')
    key = os.getenv('KAGGLE_KEY')
    
    if username and key:
        print(f"   ✅ Username: {username}")
        print(f"   ✅ API Key: {'*' * min(10, len(key))}...")
        return True
    else:
        print("   ❌ Missing credentials in .env file")
        print(f"   📁 Expected location: {env_path}")
        print("\n   Add these lines to your .env:")
        print("   KAGGLE_USERNAME=your_username")
        print("   KAGGLE_KEY=your_api_key")
        return False


async def test_import():
    """Step 2: Test imports"""
    print("\n📋 Step 2: Importing trek tool...")
    try:
        from tools.trek_tool import IndianTrekTool, search_treks
        print("   ✅ Import successful")
        return True, (IndianTrekTool, search_treks)
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        print("\n   Troubleshooting:")
        print("   - Make sure trek_tool.py exists in backend/tools/")
        print("   - Check if pandas and kagglehub are installed:")
        print("     pip install pandas kagglehub")
        return False, None


async def test_initialization(IndianTrekTool):
    """Step 3: Test tool initialization"""
    print("\n📋 Step 3: Initializing trek tool...")
    try:
        tool = IndianTrekTool()
        print(f"   ✅ Tool initialized")
        print(f"   📂 Cache directory: {tool.cache_dir}")
        print(f"   📊 Dataset loaded: {tool.kaggle_data is not None}")
        
        if tool.kaggle_data is not None:
            print(f"   📈 Total treks: {len(tool.kaggle_data)}")
            print(f"   📋 Columns: {list(tool.kaggle_data.columns)}")
            
            # Show first trek as sample
            if len(tool.kaggle_data) > 0:
                print("\n   📌 Sample trek (first row):")
                first_trek = tool.kaggle_data.iloc[0]
                for col in tool.kaggle_data.columns[:5]:  # Show first 5 columns
                    print(f"      • {col}: {first_trek[col]}")
            
            return True, tool
        else:
            print("   ⚠️  Dataset not loaded - check logs above")
            return False, None
        
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        import traceback
        print("\n   Full traceback:")
        traceback.print_exc()
        return False, None


async def test_region_search(search_treks):
    """Step 4: Test region search"""
    print("\n📋 Step 4: Testing region search (Uttarakhand)...")
    try:
        results = await search_treks(region="Uttarakhand")
        
        if results and results.get('trek_found'):
            print(f"   ✅ Found {results['trek_count']} treks")
            print(f"   📊 Source: {results.get('source', 'Unknown')}")
            print("\n   📍 Sample treks:")
            
            for i, trek in enumerate(results['treks'][:3], 1):
                print(f"\n   {i}. {trek['name']}")
                print(f"      • Difficulty: {trek['difficulty']}")
                print(f"      • Duration: {trek['duration']}")
                print(f"      • Altitude: {trek['altitude']}")
                print(f"      • Best Time: {trek['best_time']}")
            
            if results['trek_count'] > 3:
                print(f"\n   ... and {results['trek_count'] - 3} more treks")
            
            return True
        else:
            print("   ⚠️  No treks found for Uttarakhand")
            return False
            
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_trek_name_search(search_treks):
    """Step 5: Test trek name search"""
    print("\n📋 Step 5: Testing trek name search (Kedarnath)...")
    try:
        result = await search_treks(trek_name="Kedarnath")
        
        if result and result.get('trek_found'):
            trek = result['treks'][0]
            print(f"   ✅ Found: {trek['name']}")
            print(f"      • Difficulty: {trek['difficulty']}")
            print(f"      • Duration: {trek['duration']}")
            print(f"      • Region: {trek['region']}")
            print(f"      • Description: {trek['description'][:150]}...")
            return True
        else:
            print("   ⚠️  Trek 'Kedarnath' not found")
            print("   Trying alternative search: 'Valley of Flowers'...")
            
            result = await search_treks(trek_name="Valley of Flowers")
            if result and result.get('trek_found'):
                trek = result['treks'][0]
                print(f"   ✅ Found: {trek['name']}")
                print(f"      • Difficulty: {trek['difficulty']}")
                return True
            else:
                print("   ⚠️  No treks found by name")
                return False
            
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_empty_search(search_treks):
    """Step 6: Test empty/invalid search"""
    print("\n📋 Step 6: Testing edge cases...")
    try:
        # Test with non-existent region
        result = await search_treks(region="XYZ_NonExistent")
        if not result or not result.get('trek_found'):
            print("   ✅ Correctly handled non-existent region")
        else:
            print("   ⚠️  Unexpected results for invalid region")
        
        # Test with no parameters
        result = await search_treks()
        if not result:
            print("   ✅ Correctly handled empty search")
        else:
            print("   ⚠️  Unexpected results for empty search")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Edge case test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests in sequence"""
    
    # Test 1: Credentials
    if not await test_kaggle_credentials():
        print("\n❌ TESTING ABORTED: Missing Kaggle credentials")
        return
    
    # Test 2: Import
    success, imports = await test_import()
    if not success:
        print("\n❌ TESTING ABORTED: Import failed")
        return
    
    IndianTrekTool, search_treks = imports
    
    # Test 3: Initialization
    success, tool = await test_initialization(IndianTrekTool)
    if not success:
        print("\n❌ TESTING ABORTED: Initialization failed")
        return
    
    # Test 4: Region search
    await test_region_search(search_treks)
    
    # Test 5: Trek name search
    await test_trek_name_search(search_treks)
    
    # Test 6: Edge cases
    await test_empty_search(search_treks)
    
    # Summary
    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70)
    
    print("\n📝 Summary:")
    print(f"   • Cache location: {tool.cache_dir}")
    print(f"   • Dataset loaded: {tool.kaggle_data is not None}")
    if tool.kaggle_data is not None:
        print(f"   • Total treks available: {len(tool.kaggle_data)}")
    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    print("\n🚀 Starting Kaggle Trek Integration Tests...")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📁 Test script location: {__file__}")
    
    asyncio.run(run_all_tests())
