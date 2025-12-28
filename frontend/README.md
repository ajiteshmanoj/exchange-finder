# NTU Exchange Finder Frontend

React frontend for the NTU Exchange University Finder.

## Live App

**URL:** [https://exchange-finder-static.onrender.com](https://exchange-finder-static.onrender.com)

## Tech Stack

- **React** 19.2.0
- **Vite** 7.2.4 (build tool)
- **Tailwind CSS** 3.4.0 (styling)
- **Axios** (HTTP client)
- **React-Select** (searchable dropdowns)

## Features

- Search for exchange universities by module codes
- Filter by countries and semester
- Set minimum mappable modules requirement
- View detailed module mappings for each university
- See CGPA requirements and available spots

## Local Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
# Runs on http://localhost:5173
```

### Build for Production

```bash
npm run build
# Output in ./dist
```

### Preview Production Build

```bash
npm run preview
```

## Environment Variables

Create `.env` for local development:
```
VITE_API_URL=http://localhost:8000
```

For production (`.env.production`):
```
VITE_API_URL=https://exchange-finder-api.onrender.com
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Search.jsx          # Main search interface
│   │   ├── ModuleSelector.jsx  # Module input component
│   │   ├── UniversityCard.jsx  # Result card component
│   │   ├── Navbar.jsx          # Navigation bar
│   │   └── ProgressDisplay.jsx # Loading indicator
│   ├── services/
│   │   └── api.js              # Axios API client
│   ├── utils/
│   │   └── constants.js        # Configuration constants
│   ├── hooks/
│   │   ├── useSession.js       # Session management
│   │   └── useWebSocket.js     # WebSocket connection
│   ├── App.jsx                 # Root component
│   ├── App.css                 # Global styles
│   └── main.jsx                # Entry point
├── .env                        # Local environment
├── .env.production             # Production environment
├── index.html                  # HTML template
├── vite.config.js              # Vite configuration
├── tailwind.config.js          # Tailwind configuration
└── package.json                # Dependencies
```

## Key Components

### Search.jsx
Main search interface that:
- Fetches available countries from API
- Allows module code input
- Sends search requests to `/api/search/db`
- Displays results as UniversityCard components

### ModuleSelector.jsx
Dynamic module input that:
- Allows adding/removing module codes
- Validates module code format
- Supports common SCSE module prefixes

### UniversityCard.jsx
Result display component showing:
- University name and country
- Available spots (Sem 1 / Sem 2)
- CGPA requirement
- Mappable modules with details
- Expandable module mapping details

## API Integration

The frontend communicates with the FastAPI backend:

```javascript
// Search database
const response = await api.searchDatabase(
  ['SC4001', 'SC4002'],  // modules
  ['Sweden', 'Denmark'], // countries (optional)
  1,                      // semester (optional)
  2                       // min mappable
);
```

## Deployment

Deployed on Render.com as a Static Site.

**Configuration:**
- Root Directory: `frontend`
- Build Command: `npm install && npm run build`
- Publish Directory: `dist`
- Environment: `VITE_API_URL=https://exchange-finder-api.onrender.com`

## Styling

Uses Tailwind CSS with custom configuration:

```javascript
// tailwind.config.js
module.exports = {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        'ntu-red': '#EF3340',
        'ntu-blue': '#003D7C',
      }
    }
  }
}
```
