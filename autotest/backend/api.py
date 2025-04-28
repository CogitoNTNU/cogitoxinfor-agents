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

@app.get("/api/generate")
async def generate_test(agentId: str):
    base_dir = Path(DATA_DIR) / agentId
    # Aggregated log files
    pre_file = base_dir / "pre_step.json"
    post_file = base_dir / "post_step.json"

    logs = []
    # Load pre_step entries if exists
    if pre_file.exists():
        try:
            pre_logs = json.loads(pre_file.read_text(encoding="utf-8"))
            if isinstance(pre_logs, list):
                logs.extend(pre_logs)
        except Exception as e:
            raise HTTPException(500, f"Error reading {pre_file.name}: {e}")

    # Load post_step entries if exists
    if post_file.exists():
        try:
            post_logs = json.loads(post_file.read_text(encoding="utf-8"))
            if isinstance(post_logs, list):
                logs.extend(post_logs)
        except Exception as e:
            raise HTTPException(500, f"Error reading {post_file.name}: {e}")

    if not logs:
        raise HTTPException(404, "No log entries found for this agent")

    # Build the Playwright script
    lines = [
        "import pytest",
        "from playwright.sync_api import sync_playwright",
        "",
        "def test_from_log():",
        "    with sync_playwright() as p:",
        "        browser = p.chromium.launch(headless=False)",
        "        page = browser.new_page()",
    ]
    for entry in logs:
        # Navigate to URL
        url = entry.get("url")
        if url:
            lines.append(f'        page.goto("{url}")')

        # Handle new "actions" or legacy "model_outputs"
        actions_list = []
        if isinstance(entry.get("actions"), list):
            actions_list = entry["actions"]
        else:
            mo = entry.get("model_outputs") or {}
            if isinstance(mo, dict):
                actions_list = mo.get("action", [])

        for act in actions_list:
            if not isinstance(act, dict):
                continue
            # Wait
            if act.get("wait"):
                secs = act["wait"]["seconds"]
                lines.append(f"        page.wait_for_timeout({secs} * 1000)")
            # Input text
            if act.get("input_text"):
                txt = act["input_text"].get("text", "").replace('"', '\\"')
                sel = entry.get("model_actions", {}) \
                    .get("interacted_element", {}) \
                    .get("css_selector", "")
                lines.append(f'        page.fill("{sel}", "{txt}")')
            # Click by index
            if act.get("click_element_by_index"):
                idx = act["click_element_by_index"].get("index", 0)
                sel = entry.get("model_actions", {}) \
                    .get("interacted_element", {}) \
                    .get("css_selector", "")
                if not sel:
                    sel = f'* >> nth={idx}'
                lines.append(f'        page.click("{sel}")')
            # Step done comment
            if act.get("done"):
                lines.append(f'        # Step done: {act["done"].get("text", "")}')

    lines.append("        browser.close()")
    script = "\n".join(lines)
    return Response(script, media_type="text/plain")

@app.post("/api/run-test")
async def run_test(body: dict = Body(...)):
    script = body.get("script")
    if not script:
        raise HTTPException(400, "No script provided")
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
    tf.write(script.encode("utf-8"))
    tf.flush()
    tf.close()
    try:
        result = subprocess.run(
            ["pytest", tf.name, "--maxfail=1", "--disable-warnings", "-q"],
            capture_output=True, text=True, timeout=30
        )
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output = "Error: Test execution timed out."
    finally:
        try:
            os.unlink(tf.name)
        except:
            pass
    return Response(output, media_type="text/plain")

if __name__ == "__main__":
    logger.info("Starting Browser-Use recording API on http://0.0.0.0:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000)