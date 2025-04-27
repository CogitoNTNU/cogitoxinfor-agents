#!/usr/bin/env python3

import json
from pathlib import Path
from fastapi import FastAPI, Request
import uvicorn

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
    
    # Determine which event type we're dealing with (pre_step or post_step)
    event_type = data.get("event_type", "unknown")
    agent_id = data.get("agent_id", "unknown")
    
    logger.info(f"Processing {event_type} data for agent {agent_id}")
    
    # Create agent-specific directory
    agent_dir = DATA_DIR / Path(agent_id)
    agent_dir.mkdir(exist_ok=True)
    
    # Create event-type specific directories
    event_dir = agent_dir / event_type
    event_dir.mkdir(exist_ok=True)
    
    # Create separate directories for different content types
    recordings_dir = event_dir / "json"
    recordings_dir.mkdir(exist_ok=True)
    
    screenshots_dir = event_dir / "screenshots" 
    screenshots_dir.mkdir(exist_ok=True)
    
    html_dir = event_dir / "html"
    html_dir.mkdir(exist_ok=True)

    # Determine the next file number within this specific event type
    existing_numbers = []
    for item in recordings_dir.iterdir():
        if item.is_file() and item.suffix == ".json":
            try:
                file_num = int(item.stem)
                existing_numbers.append(file_num)
            except ValueError:
                # In case the file name isn't just a number
                pass

    next_number = max(existing_numbers) + 1 if existing_numbers else 1
    
    # Get step number from the data (different fields for pre and post)
    step_number = data.get("step_number")
    if step_number is not None:
        # Use the step number as the file name if available
        file_name = f"{step_number:03d}"
    else:
        file_name = f"{next_number:03d}"

    # Construct the file path
    file_path = recordings_dir / f"{file_name}.json"

    # Extract the screenshot and HTML before saving the main JSON
    website_screenshot = data.get("website_screenshot")
    website_html = data.get("website_html")
    
    # Remove large fields from the JSON before saving
    clean_data = {**data}
    if website_screenshot:
        clean_data["website_screenshot"] = f"See screenshots/{file_name}.png"
        
        # Save the screenshot
        screenshot_path = screenshots_dir / f"{file_name}.png"
        try:
            b64_to_png(website_screenshot, screenshot_path)
        except Exception as e:
            logger.error(f"Error saving screenshot: {e}")
    
    if website_html:
        clean_data["website_html"] = f"See html/{file_name}.html"
        
        # Save the HTML
        html_path = html_dir / f"{file_name}.html"
        try:
            with html_path.open("w", encoding="utf-8") as f:
                f.write(website_html)
        except Exception as e:
            logger.error(f"Error saving HTML: {e}")

    # Save the JSON data to the file
    with file_path.open("w") as f:
        json.dump(clean_data, f, indent=2)
        
    logger.info(f"Successfully saved agent history step to {file_path}")

    return {
        "status": "ok", 
        "message": f"Saved to {file_path}",
        "file_id": file_name,
        "event_type": event_type,
        "agent_id": agent_id
    }

if __name__ == "__main__":
    logger.info("Starting Browser-Use recording API on http://0.0.0.0:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000)