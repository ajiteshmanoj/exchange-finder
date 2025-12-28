# NTU Exchange Finder API

FastAPI backend for the NTU Exchange University Finder.

## Live API

**Base URL:** `https://exchange-finder-api.onrender.com`

**API Docs:** `https://exchange-finder-api.onrender.com/docs`

## Quick Start

### Search for Universities

```bash
curl -X POST "https://exchange-finder-api.onrender.com/api/search/db" \
  -H "Content-Type: application/json" \
  -d '{
    "target_modules": ["SC4001", "SC4002"],
    "min_mappable_modules": 1
  }'
```

### Check Database Status

```bash
curl "https://exchange-finder-api.onrender.com/api/admin/database/status"
```

## API Endpoints

### Public Endpoints (No Auth Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check + database stats |
| POST | `/api/search/db` | Search pre-scraped database |
| GET | `/api/admin/database/status` | Database statistics |
| GET | `/api/admin/database/countries` | List all countries |
| GET | `/api/admin/database/modules` | List all module codes |

### Search Request

```json
POST /api/search/db
{
  "target_modules": ["SC4001", "SC4002", "SC4003"],
  "target_countries": ["Sweden", "Denmark", "Finland"],
  "target_semester": 1,
  "min_mappable_modules": 2
}
```

**Parameters:**
- `target_modules` (required): List of NTU module codes to search
- `target_countries` (optional): Filter by countries (null = all countries)
- `target_semester` (optional): 1, 2, or null (both semesters)
- `min_mappable_modules` (optional): Minimum mappable modules required (default: 1)

### Search Response

```json
{
  "status": "success",
  "message": "Found 72 universities matching criteria",
  "execution_time_seconds": 0.012,
  "database_timestamp": "2025-12-27T22:43:23",
  "results_count": 72,
  "results": [
    {
      "rank": 1,
      "name": "Technical University Of Denmark",
      "country": "Denmark",
      "university_code": "Denmark_Technical University Of Denmark",
      "sem1_spots": 16,
      "sem2_spots": 13,
      "min_cgpa": 3.5,
      "mappable_count": 2,
      "coverage_score": 100.0,
      "mappable_modules": {
        "SC4001": [
          {
            "ntu_module": "SC4001",
            "ntu_module_name": "NEURAL NETWORK & DEEP LEARNING",
            "partner_module_code": "02456",
            "partner_module_name": "Deep Learning",
            "academic_units": "3",
            "status": "Approved",
            "approval_year": "2025",
            "semester": "1"
          }
        ]
      },
      "unmappable_modules": [],
      "remarks": "DTU requires students to have finished..."
    }
  ]
}
```

## Database Stats

Current database contains:
- **34** countries
- **509** universities
- **24,619** module mappings
- **1,588** unique NTU modules

Last scraped: December 2025

## Performance

| Operation | Time |
|-----------|------|
| Database search | <100ms |
| Health check | <10ms |
| Cold start (after sleep) | ~30s |

## Local Development

### Start the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python run_api.py
# Server starts on http://localhost:8000
```

### API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Architecture

```
FastAPI Application
├── /api/search/db          → DatabaseManager.get_mappings_by_modules()
├── /api/admin/database/*   → DatabaseManager statistics
└── backend/services/
    ├── database.py         → SQLite operations
    └── pdf_service.py      → PDF data enrichment (spots, CGPA)
```

## File Structure

```
backend/
├── api/
│   ├── main.py         # FastAPI app + endpoints
│   ├── models.py       # Pydantic request/response models
│   └── admin.py        # Admin router
└── services/
    ├── database.py     # SQLite database manager
    ├── pdf_service.py  # PDF data for spots/CGPA
    ├── cache_manager.py
    └── recommendation_engine.py
```

## Error Handling

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (e.g., database empty) |
| 422 | Validation error |
| 500 | Internal server error |

### Error Response

```json
{
  "status": "error",
  "error": "Database is empty. Please run /api/admin/scrape first.",
  "details": null
}
```

## CORS Configuration

Allowed origins:
- `http://localhost:5173` (local development)
- `https://exchange-finder-static.onrender.com` (production)

## Deployment

Deployed on Render.com as a Web Service.

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT
```

## Legacy Endpoints

These endpoints require NTU credentials and are used for live scraping:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Verify NTU credentials |
| POST | `/api/search` | Live scraping search (slow) |
| POST | `/api/admin/scrape` | Trigger full database scrape |

These are primarily for updating the database and not needed for public use.
