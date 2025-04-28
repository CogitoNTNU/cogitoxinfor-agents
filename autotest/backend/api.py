#!/usr/bin/env python3

import json
from pathlib import Path
from fastapi import FastAPI, Request
import uvicorn

import glob
import os
import subprocess
import tempfile
from fastapi import HTTPException, Response, Body
from datetime import datetime
# Import centralized logging
from logging_setup import get_logger, b64_to_png, DATA_DIR

# Initialize logger for this module
logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI()

@app.get("/")
async def root():
    """Simple health check endpoint"""
    logger.info("Health check endpoint accessed")
    return {"status": "API is running"}

@app.post("/post_agent_history_step")
async def post_agent_history_step(request: Request):
    data = await request.json()
    
    # Determine event type and agent_id
    event_type = data.get("event_type", "unknown")
    agent_id = data.get("agent_id", "unknown")
    logger.info(f"Processing {event_type} data for agent {agent_id}")

    # Ensure agent directory exists
    agent_dir = Path(DATA_DIR) / agent_id
    agent_dir.mkdir(exist_ok=True)

    # Ensure screenshots directory exists
    screenshots_dir = agent_dir / event_type / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Prepare clean data (handling screenshot)
    website_screenshot = data.get("website_screenshot")
    
    # Remove large fields from the JSON before saving
    clean = {**data}
    if website_screenshot:
        clean["website_screenshot"] = f"See screenshots/{agent_id}_{event_type}_{clean.get('step_number', '')}.png"
        screenshot_path = screenshots_dir / f"{agent_id}_{event_type}_{clean.get('step_number', '')}.png"
        try:
            b64_to_png(website_screenshot, screenshot_path)
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")

    # Aggregate into a single file per event_type
    aggregate_file = agent_dir / f"{event_type}.json"
    if aggregate_file.exists():
        try:
            existing = json.loads(aggregate_file.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
    else:
        existing = []

    existing.append(clean)
    with aggregate_file.open("w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    logger.info(f"Appended step {clean.get('step_number')} to {aggregate_file}")

    return {
        "status": "ok",
        "message": f"Appended step to {aggregate_file}",
        "event_type": event_type,
        "agent_id": agent_id
    }

if __name__ == "__main__":
    logger.info("Starting Browser-Use recording API on http://0.0.0.0:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000)