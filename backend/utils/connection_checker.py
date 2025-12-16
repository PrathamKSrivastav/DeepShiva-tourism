import aiohttp
import asyncio
import logging

logger = logging.getLogger(__name__)

async def check_internet_connection(timeout: int = 5) -> bool:
    """Check internet connectivity by attempting to reach reliable endpoints"""
    test_urls = [
        "https://8.8.8.8",  # Google DNS
        "https://1.1.1.1",  # Cloudflare DNS
        "https://httpbin.org/status/200"  # Simple HTTP endpoint
    ]
    
    async def check_url(url: str) -> bool:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(url) as response:
                    return response.status < 400
        except Exception:
            return False
    
    try:
        tasks = [check_url(url) for url in test_urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # If any URL succeeds, we have internet
        for result in results:
            if result is True:
                return True
        
        logger.info("No internet connectivity detected")
        return False
        
    except Exception as e:
        logger.warning(f"Connection check failed: {str(e)}")
        return False

async def check_groq_api_health(api_key: str, timeout: int = 5) -> bool:
    """
    Check if Groq API is accessible and responsive
    
    Args:
        api_key: Groq API key
        timeout: Maximum time to wait for response
        
    Returns:
        bool: True if API is healthy, False otherwise
    """
    if not api_key:
        return False
        
    try:
        # Check if we have internet first
        has_internet = await check_internet_connection(timeout)
        if not has_internet:
            return False
            
        # Test Groq API endpoint
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        test_payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 5
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=test_payload
            ) as response:
                return response.status == 200
        
    except Exception as e:
        logger.warning(f"Groq API health check failed: {str(e)}")
        return False
