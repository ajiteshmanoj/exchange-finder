"""
FastAPI application for NTU Exchange University Recommendation API.

Provides endpoints for searching universities based on module mappings
with intelligent caching for performance.
"""

import sys
import time
from pathlib import Path
from typing import List
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.api.models import (
    SearchRequest, SearchResponse, ErrorResponse,
    CacheClearResponse, UniversityResult, ModuleMapping
)
from backend.services.recommendation_engine import RecommendationEngine


# Initialize FastAPI app
app = FastAPI(
    title="NTU Exchange University Recommendation API",
    description="""
    Find suitable exchange universities based on module mappings.

    ## Features
    - Search universities by module mappings
    - Intelligent caching (365d for universities, 30d for mappings)
    - First search: 15-25 minutes (live scraping)
    - Subsequent searches: Instant (from cache)

    ## Authentication
    NTU SSO credentials required in request body.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Ajitesh",
        "email": "ajitesh@example.com"
    }
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize recommendation engine
try:
    engine = RecommendationEngine()
    print("✓ Recommendation engine initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize recommendation engine: {e}")
    raise


# ============= ENDPOINTS =============

@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint.

    Returns basic API information and status.
    """
    return {
        "status": "online",
        "service": "NTU Exchange University Recommendation API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "search": "POST /api/search",
            "clear_cache": "POST /api/cache/clear",
            "health": "GET /"
        }
    }


@app.post(
    "/api/search",
    response_model=SearchResponse,
    status_code=status.HTTP_200_OK,
    tags=["Search"],
    summary="Search for exchange universities",
    description="""
    Search for exchange universities based on module mappings.

    ## Performance
    - **First search** (cold cache): 15-25 minutes
      - Scrapes live data from NTU module mapping system
      - Caches results for future use
    - **Subsequent searches** (warm cache): 1-2 seconds
      - Loads from cache if parameters match
      - Cache TTL: 30 days for mappings, 365 days for universities

    ## Caching
    Cache is based on:
    - Username (different users may have different permissions)
    - Target countries
    - Target modules

    ## Request
    Provide NTU SSO credentials and search parameters.

    ## Response
    Returns ranked list of universities with module mappings.
    """
)
async def search_universities(request: SearchRequest):
    """
    Search for exchange universities with module mappings.

    This is a synchronous endpoint - the client waits for the full response.
    First request may take 15-25 minutes, subsequent requests are instant.
    """
    start_time = time.time()

    try:
        # Convert credentials to tuple
        credentials = (
            request.credentials.username,
            request.credentials.password,
            request.credentials.domain
        )

        # Execute search via recommendation engine
        ranked_results, cache_used, cache_timestamp = engine.search_universities(
            credentials=credentials,
            target_countries=request.target_countries,
            target_modules=request.target_modules,
            min_mappable_modules=request.min_mappable_modules,
            use_cache=request.use_cache,
            headless=True  # Always headless in API mode
        )

        # Convert results to response format
        results = []
        for rank, (uni_id, uni_data) in enumerate(ranked_results, 1):
            # Convert mappings to Pydantic models
            mappable_modules = {}
            for module_code, mappings in uni_data['mappable_modules'].items():
                mappable_modules[module_code] = [
                    ModuleMapping(**mapping) for mapping in mappings
                ]

            result = UniversityResult(
                rank=rank,
                name=uni_data['name'],
                country=uni_data['country'],
                university_code=uni_data.get('university_code', ''),
                sem1_spots=uni_data['sem1_spots'],
                min_cgpa=uni_data['min_cgpa'],
                mappable_count=uni_data['mappable_count'],
                coverage_score=uni_data['coverage_score'],
                mappable_modules=mappable_modules,
                unmappable_modules=uni_data['unmappable_modules'],
                remarks=uni_data.get('remarks', '')
            )
            results.append(result)

        execution_time = time.time() - start_time

        return SearchResponse(
            status="success",
            message=f"Found {len(results)} universities matching criteria",
            execution_time_seconds=round(execution_time, 2),
            cache_used=cache_used,
            cache_timestamp=cache_timestamp,
            results_count=len(results),
            results=results
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except RuntimeError as e:
        # Login or browser errors
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    except Exception as e:
        # General errors
        import traceback
        error_details = traceback.format_exc()
        print(f"Error during search: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@app.post(
    "/api/cache/clear",
    response_model=CacheClearResponse,
    tags=["Cache"],
    summary="Clear all cached data",
    description="""
    Clear both university list and module mapping caches.

    This will force the next search to scrape fresh data from NTU.
    Use this if you want to update the cached data.
    """
)
async def clear_cache():
    """Clear all cached data to force fresh scraping."""
    try:
        cleared_items = engine.cache_manager.clear_all()

        return CacheClearResponse(
            status="success",
            message=f"Cleared {len(cleared_items)} cache items",
            cleared_items=cleared_items
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@app.post(
    "/api/cache/clear/universities",
    response_model=CacheClearResponse,
    tags=["Cache"],
    summary="Clear university cache only",
    description="""
    Clear only the university list cache (PDF data).

    Mapping caches remain intact.
    """
)
async def clear_university_cache():
    """Clear only the university list cache (PDF data)."""
    try:
        cleared = engine.cache_manager.clear_universities()
        items = ["universities.json"] if cleared else []

        return CacheClearResponse(
            status="success",
            message="University cache cleared" if cleared else "No cache to clear",
            cleared_items=items
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@app.post(
    "/api/cache/clear/mappings",
    response_model=CacheClearResponse,
    tags=["Cache"],
    summary="Clear mapping caches only",
    description="""
    Clear only the module mapping caches.

    University list cache remains intact.
    All mapping caches for all search combinations will be cleared.
    """
)
async def clear_mapping_cache():
    """Clear only the module mapping caches."""
    try:
        count = engine.cache_manager.clear_mappings()
        items = [f"mappings/cache_{i}.json" for i in range(count)]

        return CacheClearResponse(
            status="success",
            message=f"Cleared {count} mapping cache files",
            cleared_items=items
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


# Exception handlers for better error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent error response format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            status="error",
            error=exc.detail,
            details=None
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    import traceback
    error_trace = traceback.format_exc()
    print(f"Unhandled exception: {error_trace}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            status="error",
            error="Internal server error",
            details=str(exc)
        ).dict()
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Runs when the API server starts."""
    print("\n" + "="*80)
    print("NTU EXCHANGE UNIVERSITY RECOMMENDATION API")
    print("="*80)
    print(f"✓ Server started successfully")
    print(f"✓ API documentation: http://localhost:8000/docs")
    print(f"✓ Cache directory: data/cache/")
    print("="*80 + "\n")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Runs when the API server shuts down."""
    print("\n✓ API server shutting down gracefully\n")
