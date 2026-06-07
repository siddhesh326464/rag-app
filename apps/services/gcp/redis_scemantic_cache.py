import logfire
from redisvl.extensions.llmcache import SemanticCache
from apps.config import settings
from apps.services.retrieval.embedding import embed_texts

_cache = None

def initialize_cache():
    """
    initialize_cache sets up the Redis-based semantic cache using the RedisVL library.
    """
    global _cache
    if settings.LOCAL_MODE or not settings.REDIS_HOST:
        logfire.warning("Redis host is not set or running in local mode. Semantic cache will not be initialized.")
        return None
    
    try:
        redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        _cache = SemanticCache(
            name = "enterprise_knowledge_cache",
            prefix = "semantic",
            redis_url=redis_url,
            distance_threshold=0.15,
        )

        try:
            _cache.index.create(dims = 768,overwrite=False)
            logfire.info("Semantic cache index created successfully.")


        except Exception as e:
            logfire.error(f"Error initializing Redis semantic cache: {e}")
            return None
        
        return _cache

    except Exception as e:
        logfire.error(f"Error initializing Redis semantic cache: {e}")
        return None
    

def search_in_cache(query:str):
    """
    checks the Redis semantic cache for relevant results based on the query.
    """
    if not _cache:
        return None
    
    with logfire.span("🧠 Semantic Cache Check", query=query):
        try:
            vector = embed_texts([query])[0]

            results = _cache.query(vector = vector)
            if results:
                logfire.info(f"Cache hit: Found {len(results)} results in semantic cache.")
                return results[0]["response"]
            return None

        except Exception as e:
            logfire.error(f"Error searching Redis semantic cache: {e}")
            return None
        

def add_to_cache(query:str, response:str):
    """
    adds a new query-response pair to the Redis semantic cache. 
    """
    if not _cache:
        return None
    try:
        vector = embed_texts([query])[0]

        _cache.store(
            prompt = query,
            response = response,
            vector = vector
        )
    except Exception as e:
        logfire.error(f"Error adding to Redis semantic cache: {e}")
        return None
    