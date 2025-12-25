#!/usr/bin/env python3
"""
FastAPI Server Launcher for NTU Exchange Scraper API

Usage:
    python run_api.py

The server will start on http://0.0.0.0:8000
API documentation available at http://localhost:8000/docs
"""

import uvicorn

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Starting NTU Exchange University Recommendation API Server")
    print("="*80)
    print("\nServer will be available at:")
    print("  - API: http://localhost:8000")
    print("  - Docs: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("\nPress CTRL+C to stop the server")
    print("="*80 + "\n")

    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (development mode)
        log_level="info"
    )
