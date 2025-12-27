"""
Admin API Endpoints for NTU Exchange Scraper

Provides endpoints for:
- Triggering full database scrapes
- Monitoring scrape progress
- Checking database status
- Managing scrape jobs
"""

import asyncio
import yaml
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import JSONResponse

from backend.api.models import (
    AdminScrapeRequest,
    ScrapeJobStatus,
    ScrapeStartResponse,
    DatabaseStatusResponse,
    DatabaseSearchRequest,
    DatabaseSearchResponse,
    ErrorResponse,
    UniversityResult
)
from backend.services.database import DatabaseManager
from backend.services.bulk_scraper import BulkScraper, AsyncBulkScraper


# Create router
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Store active scrape jobs (in production, use Redis or similar)
active_scrapers: Dict[int, BulkScraper] = {}
websocket_connections: Dict[int, list] = {}


def load_config() -> dict:
    """Load configuration from YAML file."""
    config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


# ==================== Database Status ====================

@router.get(
    "/database/status",
    response_model=DatabaseStatusResponse,
    summary="Get database status",
    description="Check if the database has been populated with module mappings"
)
async def get_database_status():
    """Get current database status and statistics."""
    db = DatabaseManager()
    stats = db.get_database_stats()

    return DatabaseStatusResponse(
        populated=stats['populated'],
        total_countries=stats['total_countries'],
        total_universities=stats['total_universities'],
        total_mappings=stats['total_mappings'],
        unique_modules=stats['unique_modules'],
        last_scrape=stats['last_scrape'],
        db_path=stats['db_path']
    )


# ==================== Scrape Management ====================

@router.post(
    "/scrape",
    response_model=ScrapeStartResponse,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
    summary="Start full database scrape",
    description="Trigger a full scrape of all countries, universities, and module mappings"
)
async def start_scrape(
    request: AdminScrapeRequest,
    background_tasks: BackgroundTasks
):
    """
    Start a full scrape of all module mappings.

    This operation:
    1. Logs in to NTU SSO with provided credentials
    2. Scrapes all countries and universities from dropdowns
    3. For each university, scrapes ALL module mappings
    4. Stores everything in SQLite database

    The scrape runs in the background. Use /api/admin/scrape/status/{job_id}
    to track progress, or connect to WebSocket for real-time updates.
    """
    # Check if there's already a running scrape
    db = DatabaseManager()
    running_job = db.get_running_scrape_job()
    if running_job:
        raise HTTPException(
            status_code=409,
            detail=f"A scrape is already running (job_id: {running_job['id']}). "
                   f"Wait for it to complete or cancel it first."
        )

    # Load config
    config = load_config()

    # Extract credentials
    credentials = (
        request.credentials.username,
        request.credentials.password,
        request.credentials.domain
    )

    # Create scraper
    def progress_callback(data):
        job_id = data.get('job_id')
        if job_id and job_id in websocket_connections:
            # Send to all connected WebSockets for this job
            import json
            message = json.dumps(data)
            for ws in websocket_connections.get(job_id, []):
                try:
                    asyncio.create_task(ws.send_text(message))
                except Exception:
                    pass

    scraper = BulkScraper(
        credentials,
        config,
        progress_callback=progress_callback,
        headless=request.headless
    )

    # Start scrape in background
    def run_scrape():
        try:
            result = scraper.scrape_all()
            # Clean up
            if scraper.job_id in active_scrapers:
                del active_scrapers[scraper.job_id]
            return result
        except Exception as e:
            print(f"Scrape error: {e}")
            if scraper.job_id:
                db.update_scrape_job(
                    scraper.job_id,
                    status='failed',
                    error_message=str(e)
                )

    # Create job first to get ID
    job_id = db.create_scrape_job()
    scraper.job_id = job_id
    active_scrapers[job_id] = scraper

    # Run in background
    background_tasks.add_task(run_scrape)

    return ScrapeStartResponse(
        status="started",
        job_id=job_id,
        message=f"Full scrape started. Use /api/admin/scrape/status/{job_id} to track progress, "
                f"or connect to WebSocket /ws/admin/scrape/{job_id} for real-time updates."
    )


@router.get(
    "/scrape/status/{job_id}",
    response_model=ScrapeJobStatus,
    responses={404: {"model": ErrorResponse}},
    summary="Get scrape job status",
    description="Get the current status of a scrape job"
)
async def get_scrape_status(job_id: int):
    """Get status of a specific scrape job."""
    db = DatabaseManager()
    job = db.get_scrape_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Scrape job {job_id} not found"
        )

    return ScrapeJobStatus(
        job_id=job['id'],
        status=job['status'],
        total_countries=job['total_countries'] or 0,
        completed_countries=job['completed_countries'] or 0,
        total_universities=job['total_universities'] or 0,
        completed_universities=job['completed_universities'] or 0,
        current_country=job['current_country'],
        current_university=job['current_university'],
        started_at=job['started_at'],
        completed_at=job['completed_at'],
        error_message=job['error_message']
    )


@router.delete(
    "/scrape/{job_id}",
    responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}},
    summary="Cancel scrape job",
    description="Cancel a running scrape job"
)
async def cancel_scrape(job_id: int):
    """Cancel a running scrape job."""
    db = DatabaseManager()
    job = db.get_scrape_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Scrape job {job_id} not found"
        )

    if job['status'] != 'running':
        raise HTTPException(
            status_code=400,
            detail=f"Job {job_id} is not running (status: {job['status']})"
        )

    # Cancel the scraper
    if job_id in active_scrapers:
        active_scrapers[job_id].cancel()
        del active_scrapers[job_id]

    return {"status": "cancelled", "job_id": job_id, "message": "Scrape job cancelled"}


@router.post(
    "/scrape/force-cancel",
    summary="Force cancel stale jobs",
    description="Force cancel any jobs stuck in 'running' state (use after server restart)"
)
async def force_cancel_stale_jobs():
    """
    Force cancel all stale scrape jobs.

    Use this when jobs are stuck in 'running' state after a server restart
    or when the scraper process died unexpectedly.
    """
    db = DatabaseManager()
    cancelled_count = db.force_cancel_stale_jobs()

    return {
        "status": "success",
        "cancelled_jobs": cancelled_count,
        "message": f"Force cancelled {cancelled_count} stale job(s)"
    }


@router.get(
    "/scrape/latest",
    response_model=ScrapeJobStatus,
    responses={404: {"model": ErrorResponse}},
    summary="Get latest scrape job",
    description="Get the most recent scrape job status"
)
async def get_latest_scrape():
    """Get the most recent scrape job."""
    db = DatabaseManager()
    job = db.get_latest_scrape_job()

    if not job:
        raise HTTPException(
            status_code=404,
            detail="No scrape jobs found"
        )

    return ScrapeJobStatus(
        job_id=job['id'],
        status=job['status'],
        total_countries=job['total_countries'] or 0,
        completed_countries=job['completed_countries'] or 0,
        total_universities=job['total_universities'] or 0,
        completed_universities=job['completed_universities'] or 0,
        current_country=job['current_country'],
        current_university=job['current_university'],
        started_at=job['started_at'],
        completed_at=job['completed_at'],
        error_message=job['error_message']
    )


# ==================== Database Search ====================

@router.post(
    "/search",
    response_model=DatabaseSearchResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Search pre-scraped database",
    description="Search module mappings from pre-scraped database (instant results, no credentials needed)"
)
async def search_database(request: DatabaseSearchRequest):
    """
    Search the pre-scraped database for module mappings.

    This endpoint queries the SQLite database directly - no live scraping required.
    Response time is typically <100ms.

    Note: Database must be populated first using /api/admin/scrape
    """
    start_time = datetime.now()

    db = DatabaseManager()

    # Check if database is populated
    if not db.is_populated():
        raise HTTPException(
            status_code=400,
            detail="Database is empty. Please run /api/admin/scrape first to populate the database."
        )

    # Query database
    try:
        raw_results = db.get_mappings_by_modules(
            request.target_modules,
            request.target_countries
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database query failed: {str(e)}"
        )

    # Convert to response format
    results = []
    rank = 1

    for uni_key, uni_data in raw_results.items():
        country = uni_data['country']
        university = uni_data['university']
        mappings = uni_data['mappings']

        # Count mappable modules
        mappable_count = len([m for m in mappings if mappings[m]])

        # Filter by min_mappable_modules
        if mappable_count < request.min_mappable_modules:
            continue

        # Build mappable_modules dict
        mappable_modules = {}
        for module_code, module_mappings in mappings.items():
            if module_mappings:
                mappable_modules[module_code] = [
                    {
                        'ntu_module': m['ntu_module'],
                        'ntu_module_name': m['ntu_module_name'],
                        'partner_module_code': m['partner_module_code'],
                        'partner_module_name': m['partner_module_name'],
                        'academic_units': m['academic_units'],
                        'status': m['status'],
                        'approval_year': m['approval_year'],
                        'semester': m['semester']
                    }
                    for m in module_mappings
                ]

        # Find unmappable modules
        unmappable = [m for m in request.target_modules if m not in mappable_modules]

        results.append(UniversityResult(
            rank=rank,
            name=university,
            country=country,
            university_code=uni_key,
            sem1_spots=0,  # Not available from database
            min_cgpa=0.0,  # Not available from database
            mappable_count=mappable_count,
            coverage_score=(mappable_count / len(request.target_modules)) * 100,
            mappable_modules=mappable_modules,
            unmappable_modules=unmappable,
            remarks=""
        ))
        rank += 1

    # Sort by mappable_count descending
    results.sort(key=lambda x: (-x.mappable_count, x.country, x.name))

    # Re-assign ranks after sorting
    for i, result in enumerate(results):
        result.rank = i + 1

    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()

    # Get database timestamp
    stats = db.get_database_stats()

    return DatabaseSearchResponse(
        status="success",
        message=f"Found {len(results)} universities matching criteria",
        execution_time_seconds=execution_time,
        database_timestamp=stats['last_scrape'],
        results_count=len(results),
        results=results
    )


# ==================== WebSocket for Real-time Progress ====================

@router.websocket("/ws/scrape/{job_id}")
async def websocket_scrape_progress(websocket: WebSocket, job_id: int):
    """
    WebSocket endpoint for real-time scrape progress updates.

    Connect to receive live updates during a scrape job.
    """
    await websocket.accept()

    # Add to connections
    if job_id not in websocket_connections:
        websocket_connections[job_id] = []
    websocket_connections[job_id].append(websocket)

    try:
        # Send initial status
        db = DatabaseManager()
        job = db.get_scrape_job(job_id)
        if job:
            await websocket.send_json({
                "type": "status",
                "job_id": job_id,
                "status": job['status'],
                "total_universities": job['total_universities'] or 0,
                "completed_universities": job['completed_universities'] or 0
            })

        # Keep connection alive
        while True:
            try:
                # Wait for messages (or disconnection)
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})

    except WebSocketDisconnect:
        pass
    finally:
        # Remove from connections
        if job_id in websocket_connections:
            if websocket in websocket_connections[job_id]:
                websocket_connections[job_id].remove(websocket)
            if not websocket_connections[job_id]:
                del websocket_connections[job_id]


# ==================== Database Management ====================

@router.post(
    "/database/clear",
    summary="Clear database",
    description="Clear all data from the database (requires confirmation)"
)
async def clear_database(confirm: bool = False):
    """
    Clear all data from the database.

    WARNING: This will delete all scraped data. Use with caution.
    Set confirm=true to proceed.
    """
    if not confirm:
        return {
            "status": "warning",
            "message": "This will delete all scraped data. Set confirm=true to proceed."
        }

    db = DatabaseManager()
    db.clear_all_data()

    return {
        "status": "success",
        "message": "Database cleared successfully"
    }


@router.get(
    "/database/modules",
    summary="Get available modules",
    description="Get list of all module codes in the database"
)
async def get_available_modules():
    """Get list of all NTU module codes in the database."""
    db = DatabaseManager()
    modules = db.get_all_module_codes()

    return {
        "status": "success",
        "count": len(modules),
        "modules": modules
    }


@router.get(
    "/database/countries",
    summary="Get available countries",
    description="Get list of all countries in the database"
)
async def get_available_countries():
    """Get list of all countries in the database."""
    db = DatabaseManager()
    countries = db.get_all_countries()

    return {
        "status": "success",
        "count": len(countries),
        "countries": countries
    }
