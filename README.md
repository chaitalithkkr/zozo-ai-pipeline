# zozo-ai-pipeline

An automated, AI-powered personal data pipeline that ingests nightly form inputs, enriches them with live API data, and delivers a structured daily briefing via email every morning at 7am.

Built as a personal productivity tool — and a demonstration of end-to-end ETL pipeline design using Python and modern APIs.

---

## What It Does

Every morning, Zozo:

1. **Extracts** the most recent Google Form response from Google Sheets
2. **Enriches** the data with live weather forecasts from Open-Meteo API
3. **Transforms** all inputs using Claude AI (Anthropic) into a structured, personalized daily plan
4. **Loads** the output as a formatted HTML email delivered via Gmail SMTP
5. **Runs automatically** every day via Windows Task Scheduler

---

## Tech Stack

| Layer | Tool |
|---|---|
| Language | Python 3.13 |
| AI / LLM | Anthropic Claude (claude-sonnet) |
| Data Source | Google Sheets API via gspread |
| Weather API | Open-Meteo (free, no key required) |
| Output | Gmail SMTP |
| Scheduling | Windows Task Scheduler |
| Auth | Google Service Account (OAuth2) |
| Config | python-dotenv |

---

## Pipeline Architecture

```
Google Form (nightly input)
        ↓
Google Sheets API  →  extract last row
        ↓
Open-Meteo API     →  enrich with weather data
        ↓
Anthropic Claude   →  transform into structured daily plan
        ↓
Gmail SMTP         →  load as HTML email
        ↓
Windows Task Scheduler  →  orchestrate at 7:00 AM daily
```

---

## Project Structure

```
zozo-ai-pipeline/
├── zozo.py                  # Main pipeline script
├── context.example.json     # User profile template (see setup)
├── .env.example             # Environment variable template
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/zozo-ai-pipeline.git
cd zozo-ai-pipeline
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```
ANTHROPIC_API_KEY=your-anthropic-api-key
GMAIL_ADDRESS=your-gmail@gmail.com
GMAIL_APP_PASSWORD=your-gmail-app-password
SHEET_ID=your-google-sheet-id
```

> **Gmail:** You need a [Gmail App Password](https://support.google.com/accounts/answer/185833), not your regular password. 2FA must be enabled on your account.

### 4. Add your Google Service Account credentials

- Create a service account in [Google Cloud Console](https://console.cloud.google.com/)
- Enable the Google Sheets API
- Download the credentials JSON and save as `zozo_credentials.json`
- Share your Google Sheet with the service account email

### 5. Create your context file

Copy `context.example.json` to `context.json` and fill in your personal profile. This gives the AI context about you for personalized output.

### 6. Run manually to test

```bash
python zozo.py
```

Uncomment the `run_zozo()` line at the bottom of the script to trigger immediately without waiting for the scheduler.

### 7. Schedule daily runs

Use Windows Task Scheduler (or cron on Mac/Linux) to run `zozo.py` daily at your preferred time.

---

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Anthropic API key from [console.anthropic.com](https://console.anthropic.com) |
| `GMAIL_ADDRESS` | Gmail address to send/receive the briefing |
| `GMAIL_APP_PASSWORD` | Gmail App Password (not your account password) |
| `SHEET_ID` | Google Sheet ID from the URL of your linked form responses |

---

## Key Design Decisions

- **Fallback handling:** If no form response is found, the pipeline runs with sensible defaults rather than failing
- **Modular functions:** Each pipeline stage (extract, enrich, transform, load) is a separate function for easy testing and extension
- **Prompt engineering:** The system prompt is structured to enforce output format, tone, and content constraints on the LLM
- **Error isolation:** Weather API failures are caught per-city and return a graceful fallback string rather than crashing the pipeline

---

## Requirements

```
anthropic
gspread
google-auth
requests
schedule
python-dotenv
```

---

## Notes

- Weather data is sourced from [Open-Meteo](https://open-meteo.com/) — free, no API key required
- The pipeline is designed to be extended: swap Gmail for SendGrid, Google Sheets for any database, or Task Scheduler for Airflow
- All personal data (context.json, credentials, .env) is excluded from version control via .gitignore

---

## License

MIT
