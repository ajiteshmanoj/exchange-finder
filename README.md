# NTU Exchange University Finder

A web application to help NTU students find suitable exchange universities based on module mappings and availability.

## Live Demo

**Try it now:** [https://exchange-finder-static.onrender.com](https://exchange-finder-static.onrender.com)

No login required - search instantly from our pre-scraped database of 24,000+ module mappings across 500+ universities.

## Features

- **Instant Search**: Query pre-scraped database for results in <100ms
- **No Login Required**: Public access to all module mapping data
- **Smart Filtering**: Filter by countries, semester, and minimum mappable modules
- **Comprehensive Data**: 509 universities, 34 countries, 24,619 module mappings
- **Semester Selection**: Filter by Sem 1, Sem 2, or both
- **Detailed Results**: See approved module mappings, CGPA requirements, available spots

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PRODUCTION (Render.com)                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐         ┌─────────────────────────┐   │
│  │  Static Site    │  HTTP   │  Web Service            │   │
│  │  (React/Vite)   │ ──────> │  (FastAPI + SQLite)     │   │
│  │                 │         │                         │   │
│  │  - Search UI    │         │  - /api/search/db       │   │
│  │  - Results      │         │  - Pre-scraped DB       │   │
│  │  - Filters      │         │  - 24,619 mappings      │   │
│  └─────────────────┘         └─────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite (pre-scraped, 3.8MB)
- **Server**: Uvicorn

### Frontend
- **Framework**: React 19
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios

### Deployment
- **Platform**: Render.com (Free tier)
- **Frontend**: Static Site
- **Backend**: Web Service

## Project Structure

```
Exchange_Scraper/
├── backend/
│   ├── api/
│   │   ├── main.py              # FastAPI endpoints
│   │   ├── models.py            # Pydantic models
│   │   └── admin.py             # Admin endpoints
│   └── services/
│       ├── database.py          # SQLite manager
│       ├── recommendation_engine.py
│       ├── cache_manager.py
│       └── pdf_service.py
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── services/            # API client
│   │   └── App.jsx              # Main app
│   ├── .env.production          # Production API URL
│   └── package.json
├── scrapers/                    # Data collection scripts
│   ├── pdf_extractor.py
│   ├── selenium_scraper.py
│   └── ntu_mapper.py
├── data/
│   └── exchange_mappings.db     # Pre-scraped SQLite database
├── config/
│   └── config.yaml              # Configuration
├── run_api.py                   # Backend launcher
└── requirements.txt             # Python dependencies
```

## Local Development

### Prerequisites
- Python 3.9+
- Node.js 18+
- Chrome (for scraping)

### Backend Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the API server
python run_api.py
# Server runs on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
# Frontend runs on http://localhost:5173
```

### Environment Variables

**Frontend** (`frontend/.env`):
```
VITE_API_URL=http://localhost:8000
```

**Production** (`frontend/.env.production`):
```
VITE_API_URL=https://exchange-finder-api.onrender.com
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check + database stats |
| POST | `/api/search/db` | Search database (instant, no auth) |
| GET | `/api/admin/database/status` | Database statistics |
| GET | `/api/admin/database/countries` | List all countries |
| GET | `/api/admin/database/modules` | List all module codes |

### Search Example

```bash
curl -X POST "https://exchange-finder-api.onrender.com/api/search/db" \
  -H "Content-Type: application/json" \
  -d '{
    "target_modules": ["SC4001", "SC4002"],
    "target_countries": ["Sweden", "Denmark"],
    "target_semester": 1,
    "min_mappable_modules": 1
  }'
```

## Database

The SQLite database contains pre-scraped data:

| Table | Records | Description |
|-------|---------|-------------|
| countries | 34 | All NTU exchange partner countries |
| universities | 509 | All partner universities |
| module_mappings | 24,619 | Approved module mappings |

**Last updated**: December 2025

## Updating the Database

To refresh the module mapping data:

1. Run the scraper locally with NTU credentials
2. Commit the updated `data/exchange_mappings.db`
3. Push to GitHub - Render auto-deploys

```bash
# Run full scrape (requires NTU login)
python main.py

# Or use admin endpoint (if credentials configured)
curl -X POST "http://localhost:8000/api/admin/scrape" \
  -H "Content-Type: application/json" \
  -d '{"credentials": {...}}'
```

## Deployment

### Render.com Setup

**Backend (Web Service)**:
- Build: `pip install -r requirements.txt`
- Start: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`

**Frontend (Static Site)**:
- Root: `frontend`
- Build: `npm install && npm run build`
- Publish: `dist`
- Env: `VITE_API_URL=https://exchange-finder-api.onrender.com`

### Free Tier Limitations
- Backend sleeps after 15 min inactivity
- First request takes ~30s to wake
- 750 free hours/month

## Legacy CLI Mode

The original CLI scraper still works for local data collection:

```bash
# Setup credentials (first time)
python main.py --setup

# Run full scrape pipeline
python main.py

# Show browser during scrape (for debugging)
python main.py --show-browser
```

## License

This project is for personal educational use.

## Author

Ajitesh (NTU DSAI)
