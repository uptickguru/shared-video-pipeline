# Shared Video Pipeline

A centralized pipeline for queueing and generating video and text via web scraping (Playwright) and API fallbacks, leveraging dynamic Vast.ai instances for cost-effective GPU rendering.

## Setup

1. Create a virtual environment: `python -m venv venv`
2. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Linux)
3. Install dependencies: `pip install -r requirements.txt`
4. Install Playwright browsers: `playwright install chromium`

## Running the System

### 1. Start the API Server
```bash
uvicorn main:app --reload --port 8000
```

### 2. Start the Worker Queue
Make sure Redis is running locally or configured via `.env`
```bash
rq worker high standard vast_video
```
