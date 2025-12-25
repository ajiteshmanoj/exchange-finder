"""
FastAPI application for NTU Exchange University Recommendation API.

Provides endpoints for searching universities based on module mappings
with intelligent caching for performance.
"""

import sys
import time
import asyncio
import json
from pathlib import Path
from typing import List
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.api.models import (
    SearchRequest, SearchResponse, ErrorResponse,
    CacheClearResponse, UniversityResult, ModuleMapping,
    ProgressMessage, CompleteMessage, ErrorMessage,
    CountriesUniversitiesRequest, CountriesUniversitiesResponse, CountryUniversity,
    LoginRequest, LoginResponse
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
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "*"  # Allow all in development
    ],
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

# Initialize thread pool executor for running blocking operations
executor = ThreadPoolExecutor(max_workers=4)


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
    "/api/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    tags=["Authentication"],
    summary="Verify NTU SSO credentials and fetch countries",
    description="""
    Verify NTU SSO credentials and pre-fetch countries in the same session.

    ## Process
    1. Starts a headless Chrome browser
    2. Navigates to NTU SSO login page
    3. Attempts authentication with provided credentials
    4. If successful, also fetches and caches all countries/universities
    5. Returns success/failure status

    ## Timing
    - Login: 10-30 seconds
    - Country fetch: 1-2 minutes (only on first login, then cached)
    """
)
async def verify_login(request: LoginRequest):
    """
    Verify NTU SSO credentials and pre-fetch countries.

    Returns success status and message.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from scrapers.selenium_scraper import SeleniumNTUScraper

    try:
        credentials = (
            request.credentials.username,
            request.credentials.password,
            request.credentials.domain
        )

        scraper = SeleniumNTUScraper(credentials, engine.config, headless=True)

        try:
            # Start browser
            if not scraper.start():
                return LoginResponse(
                    success=False,
                    message="Failed to start browser",
                    username=None
                )

            # Attempt login
            if not scraper.login():
                return LoginResponse(
                    success=False,
                    message="Login failed - invalid credentials or NTU SSO error",
                    username=None
                )

            # Login successful! Now fetch and cache countries in the same session
            # Check if already cached
            cached = engine.cache_manager.get_countries_universities()
            if not cached:
                print("  Pre-fetching countries in login session...")
                try:
                    countries_dict = scraper.scrape_countries_and_universities()
                    engine.cache_manager.save_countries_universities(countries_dict)
                    print(f"  ✓ Cached {len(countries_dict)} countries")
                except Exception as e:
                    print(f"  Warning: Failed to pre-fetch countries: {e}")
                    # Don't fail login if country fetch fails
            else:
                print("  Countries already cached, skipping pre-fetch")

            return LoginResponse(
                success=True,
                message="Login successful",
                username=request.credentials.username
            )

        finally:
            scraper.close()

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Login error: {error_details}")
        return LoginResponse(
            success=False,
            message=f"Login error: {str(e)}",
            username=None
        )


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


@app.post(
    "/api/cache/clear/countries",
    response_model=CacheClearResponse,
    tags=["Cache"],
    summary="Clear countries/universities cache only"
)
async def clear_countries_cache():
    """Clear only the countries/universities cache."""
    try:
        cleared = engine.cache_manager.clear_countries_universities()
        items = ["countries_universities.json"] if cleared else []

        return CacheClearResponse(
            status="success",
            message="Countries cache cleared" if cleared else "No cache to clear",
            cleared_items=items
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear cache: {str(e)}"
        )


@app.post(
    "/api/countries-universities",
    response_model=CountriesUniversitiesResponse,
    status_code=status.HTTP_200_OK,
    tags=["Data"],
    summary="Get all countries and universities",
    description="""
    Retrieve complete list of all countries and universities from NTU dropdown.

    ## Performance
    - **First request** (cold cache): 2-5 minutes
      - Scrapes live data from NTU system
      - Caches results for 30 days
    - **Subsequent requests** (warm cache): <1 second
      - Loads from cache

    ## Caching
    Cache TTL: 30 days (universities/partnerships can change)

    ## Usage
    This endpoint is called by the frontend to populate the country/university selector.
    """
)
async def get_countries_universities(request: CountriesUniversitiesRequest):
    """
    Get all countries and their universities from NTU dropdown.

    Returns alphabetically sorted list with university counts.
    """
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from scrapers.selenium_scraper import SeleniumNTUScraper

    start_time = time.time()

    try:
        # Try cache first
        if request.use_cache:
            cached = engine.cache_manager.get_countries_universities()
            if cached:
                countries_dict, cache_time = cached

                # Transform to response format
                countries_list = []
                for country, universities in sorted(countries_dict.items()):
                    countries_list.append(CountryUniversity(
                        country=country,
                        universities=universities,
                        university_count=len(universities)
                    ))

                return CountriesUniversitiesResponse(
                    status="success",
                    message=f"Retrieved {len(countries_list)} countries with {sum(c.university_count for c in countries_list)} universities (from cache)",
                    cache_used=True,
                    cache_timestamp=cache_time,
                    total_countries=len(countries_list),
                    total_universities=sum(c.university_count for c in countries_list),
                    countries=countries_list
                )

        # Cache miss - scrape from NTU
        credentials = (
            request.credentials.username,
            request.credentials.password,
            request.credentials.domain
        )

        scraper = SeleniumNTUScraper(credentials, engine.config, headless=True)

        try:
            # Start browser and login
            if not scraper.start():
                raise RuntimeError("Failed to start browser")

            if not scraper.login():
                raise RuntimeError("Login failed - check credentials")

            # Scrape countries and universities
            countries_dict = scraper.scrape_countries_and_universities()

            # Save to cache
            if request.use_cache:
                engine.cache_manager.save_countries_universities(countries_dict)

            # Transform to response format
            countries_list = []
            for country, universities in sorted(countries_dict.items()):
                countries_list.append(CountryUniversity(
                    country=country,
                    universities=universities,
                    university_count=len(universities)
                ))

            return CountriesUniversitiesResponse(
                status="success",
                message=f"Retrieved {len(countries_list)} countries with {sum(c.university_count for c in countries_list)} universities",
                cache_used=False,
                cache_timestamp=None,
                total_countries=len(countries_list),
                total_universities=sum(c.university_count for c in countries_list),
                countries=countries_list
            )

        finally:
            scraper.close()

    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error fetching countries/universities: {error_details}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch countries/universities: {str(e)}"
        )


@app.websocket("/ws/search")
async def websocket_search_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time university search with progress updates.

    Accepts a SearchRequest JSON and streams progress messages in real-time,
    followed by complete results or an error message.

    Message Types:
    - ProgressMessage: Real-time progress updates during scraping
    - CompleteMessage: Final results when search completes
    - ErrorMessage: Error details if search fails
    """
    await websocket.accept()
    print("✓ WebSocket client connected")

    try:
        # Receive search request from client
        request_data = await websocket.receive_text()
        request_dict = json.loads(request_data)

        # Validate request using Pydantic model
        try:
            search_request = SearchRequest(**request_dict)
        except Exception as e:
            error_msg = ErrorMessage(
                error="Invalid request format",
                details=str(e)
            )
            await websocket.send_text(error_msg.json())
            await websocket.close()
            return

        print(f"✓ WebSocket search request received from {search_request.credentials.username}")

        # Progress callback function to send updates to client
        async def send_progress(step: int, step_name: str, message: str, details: dict = None):
            """Send progress message to WebSocket client"""
            try:
                progress_msg = ProgressMessage(
                    step=step,
                    step_name=step_name,
                    message=message,
                    details=details
                )
                await websocket.send_text(progress_msg.json())
            except Exception as e:
                print(f"✗ Failed to send progress message: {e}")

        # Run search in thread pool executor (blocking operation)
        start_time = time.time()

        # Convert credentials to tuple
        credentials = (
            search_request.credentials.username,
            search_request.credentials.password,
            search_request.credentials.domain
        )

        # Send initial progress message
        await send_progress(
            step=1,
            step_name="Starting Search",
            message="Initializing search pipeline...",
            details=None
        )

        # Execute search with progress callbacks
        loop = asyncio.get_event_loop()

        ranked_results, cache_used, cache_timestamp = await loop.run_in_executor(
            executor,
            lambda: engine.search_universities_with_progress(
                credentials=credentials,
                target_countries=search_request.target_countries,
                target_modules=search_request.target_modules,
                min_mappable_modules=search_request.min_mappable_modules,
                use_cache=search_request.use_cache,
                headless=True,
                progress_callback=send_progress
            )
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

        # Send completion message
        complete_msg = CompleteMessage(
            message=f"Found {len(results)} universities matching criteria",
            execution_time=execution_time,
            results_count=len(results),
            results=results,
            cache_used=cache_used
        )
        await websocket.send_text(complete_msg.json())
        print(f"✓ WebSocket search completed in {execution_time:.2f}s")

    except WebSocketDisconnect:
        print("✓ WebSocket client disconnected")
    except FileNotFoundError as e:
        error_msg = ErrorMessage(
            error="PDF file not found",
            details=str(e)
        )
        await websocket.send_text(error_msg.json())
    except RuntimeError as e:
        error_msg = ErrorMessage(
            error="Authentication failed",
            details=str(e)
        )
        await websocket.send_text(error_msg.json())
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"✗ WebSocket error: {error_details}")
        error_msg = ErrorMessage(
            error="Internal server error",
            details=str(e)
        )
        await websocket.send_text(error_msg.json())
    finally:
        try:
            await websocket.close()
        except:
            pass


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
