# Equipment Maintenance Manager

A full-stack web app that takes a warehouse equipment spreadsheet, uses **Google Gemini** to look up maintenance manuals and estimate next maintenance dates, and lets you manage reminders via **Google Calendar**.

---

## Features

- **Upload .xlsx / .xls** spreadsheets with flexible column detection (order doesn't matter)
- **Import from Google Sheets** via OAuth
- **AI-powered analysis**: Gemini searches for equipment manuals and estimates the next maintenance date per item
- **Web table view** with overdue highlighting
- **Download as .xlsx** with formatted headers
- **Add to Google Calendar**: per-item or all at once (all-day events with email reminders)

---

## Setup

### 1. Google Cloud Project (for OAuth + Calendar + Sheets)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use an existing one)
3. Enable these APIs:
   - **Google Sheets API**
   - **Google Calendar API**
4. Go to **APIs & Services → OAuth consent screen**:
   - Choose "External" user type
   - Add scopes: `.../auth/spreadsheets.readonly`, `.../auth/calendar.events`
   - Add your email as a test user
5. Go to **APIs & Services → Credentials**:
   - Create **OAuth 2.0 Client ID** → Web application
   - Add authorized redirect URI: `http://localhost:8000/auth/callback`
   - Download / note the **Client ID** and **Client Secret**

### 2. Backend

```bash
cd backend
cp .env.example .env
# Edit .env with your actual keys:
# GEMINI_API_KEY, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, SESSION_SECRET_KEY

pip install -r requirements.txt
uvicorn main:app --reload
# Backend runs on http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
cp .env.example .env
# VITE_API_BASE_URL=http://localhost:8000 (default is fine)

npm install
npm run dev
# Frontend runs on http://localhost:5173
```

---

## Usage

1. Open `http://localhost:5173` in your browser
2. Click **Connect Google Account** to authorize (enables Google Sheets import + Calendar)
3. **Upload** an `.xlsx` file by dragging it in, or **import** from a Google Sheets URL
4. Click **✨ Analyze with Gemini** — Gemini will search for manuals and estimate next maintenance dates
5. Review the maintenance schedule table (overdue dates highlighted in orange)
6. Click **⬇ Download XLSX** to export the schedule
7. Click **📅 Add** on individual rows or **📅 Add All to Calendar** to push reminders to Google Calendar

---

## Spreadsheet Format

The app auto-detects columns regardless of order or exact naming. It looks for columns matching:

| Field | Recognized column names |
|---|---|
| Equipment Type | type, equipment, machine, asset, category |
| Brand | brand, manufacturer, make, vendor |
| Model | model, model number, part number |
| Installation Date | install date, installation date, commissioned |
| Last Maintenance | last maintenance, last service, serviced, maintenance date |

---

## Architecture

```
frontend/          React 18 + Vite SPA
  src/
    App.jsx                 Main app state + orchestration
    components/
      FileUpload.jsx        Drag-drop + Google Sheets URL input
      EquipmentTable.jsx    Results table with Calendar buttons
      ActionBar.jsx         Analyze / Export / Add All actions
      AuthButton.jsx        Google OAuth status + connect button
      StatusBadge.jsx       Processing status indicator
    services/api.js         Axios API client

backend/           Python FastAPI
  main.py                   App entry, CORS, session middleware
  models.py                 Pydantic data models
  routers/
    auth.py                 Google OAuth2 flow
    spreadsheet.py          .xlsx upload + Google Sheets import
    process.py              Gemini analysis endpoint
    export.py               XLSX export (openpyxl)
    calendar.py             Google Calendar event creation
  services/
    spreadsheet_parser.py   Fuzzy column detection + pandas parsing
    gemini_service.py       Async Gemini API calls with search grounding
    google_calendar.py      Calendar API wrapper
```

---

## Environment Variables

### Backend `.env`

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google Gemini API key |
| `GOOGLE_CLIENT_ID` | OAuth 2.0 client ID |
| `GOOGLE_CLIENT_SECRET` | OAuth 2.0 client secret |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/auth/callback` |
| `SESSION_SECRET_KEY` | Random secret for session signing |
| `FRONTEND_URL` | `http://localhost:5173` |

### Frontend `.env`

| Variable | Description |
|---|---|
| `VITE_API_BASE_URL` | Backend URL (default: `http://localhost:8000`) |
