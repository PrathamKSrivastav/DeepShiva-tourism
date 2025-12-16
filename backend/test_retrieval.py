import asyncio
import logging
from rag.vector_store import VectorStoreManager
from rag.retriever import SmartRetriever

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_retrieval():
    logger.info("=" * 70)
    logger.info("RETRIEVAL DIAGNOSTIC TEST")
    logger.info("=" * 70)
    
    # Initialize
    logger.info("\n🔧 Initializing components...")
    vector_store = VectorStoreManager()
    retriever = SmartRetriever(vector_store)
    
    # Check collections have data
    logger.info("\n📊 Collection Stats:")
    stats = vector_store.get_all_stats()
    logger.info(f"Total documents: {stats.get('total_documents', 0)}")
    logger.info(f"Total collections: {stats.get('total_collections', 0)}")
    
    for col_name, col_stats in stats.get('collections', {}).items():
        doc_count = col_stats.get('document_count', 0)
        if doc_count > 0:
            logger.info(f"  ✓ {col_name}: {doc_count} docs")
    
    # Test 1: Direct vector_store query
    logger.info("\n" + "=" * 70)
    logger.info("TEST 1: Direct vector_store.query()")
    logger.info("=" * 70)
    
    test_collection = "spiritual_sites"
    test_query = "Kedarnath temple"
    
    try:
        logger.info(f"Querying collection: {test_collection}")
        logger.info(f"Query: {test_query}")
        
        results = vector_store.query(
            query_text=test_query,
            collection_name=test_collection,
            n_results=3
        )
        
        logger.info(f"\n✅ Query successful!")
        logger.info(f"Result structure keys: {list(results.keys())}")
        logger.info(f"Number of documents: {len(results.get('documents', [[]])[0])}")
        
        if results.get('documents') and results['documents'][0]:
            logger.info(f"\n📄 First result preview:")
            first_doc = results['documents'][0][0]
            logger.info(f"Content length: {len(first_doc)} chars")
            logger.info(f"Preview: {first_doc[:200]}...")
            logger.info(f"Metadata: {results['metadatas'][0][0]}")
            logger.info(f"Distance: {results['distances'][0][0]}")
        else:
            logger.warning("⚠️ No documents in results!")
            
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Test 2: SmartRetriever query
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: SmartRetriever.retrieve_contextual_documents()")
    logger.info("=" * 70)
    
    try:
        logger.info(f"Querying with persona='local_guide', intent='spiritual'")
        logger.info(f"Query: {test_query}")
        
        results = await retriever.retrieve_contextual_documents(
            query=test_query,
            persona="local_guide",
            intent="spiritual",
            expand_references=False  # Disable for simpler test
        )
        
        logger.info(f"\n✅ Retrieval successful!")
        logger.info(f"Number of results: {len(results)}")
        
        if results:
            logger.info(f"\n📄 First result:")
            first = results[0]
            logger.info(f"  Collection: {first.get('collection')}")
            logger.info(f"  Name: {first.get('metadata', {}).get('name', 'N/A')}")
            logger.info(f"  Entity Type: {first.get('metadata', {}).get('entity_type', 'N/A')}")
            logger.info(f"  Final Score: {first.get('final_score', 0):.3f}")
            logger.info(f"  Content preview: {first.get('content', '')[:200]}...")
        else:
            logger.warning("⚠️ No results returned!")
            
    except Exception as e:
        logger.error(f"❌ ERROR: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Test 3: Test different collections
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Query Multiple Collections")
    logger.info("=" * 70)
    
    test_collections = ["spiritual_sites", "festivals", "crowd_patterns"]
    
    for collection in test_collections:
        try:
            results = vector_store.query(
                query_text="Badrinath",
                collection_name=collection,
                n_results=2
            )
            doc_count = len(results.get('documents', [[]])[0])
            logger.info(f"  {collection}: {doc_count} results")
        except Exception as e:
            logger.error(f"  {collection}: ERROR - {str(e)}")
    
    logger.info("\n" + "=" * 70)
    logger.info("DIAGNOSTIC TEST COMPLETE")
    logger.info("=" * 70)

if __name__ == "__main__":
    asyncio.run(test_retrieval())
