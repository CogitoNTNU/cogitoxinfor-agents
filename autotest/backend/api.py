#!/usr/bin/env python3

import json
from pathlib import Path
from fastapi import FastAPI, Request
import uvicorn
from datetime import datetime

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

    # build testing_steps.json by combining pre_step and post_step info
    testing_file = agent_dir / "testing_steps.json"
    testing_file.parent.mkdir(parents=True, exist_ok=True)

    # load or initialize testing array
    try:
        testing_data = json.loads(testing_file.read_text(encoding="utf-8"))
        if not isinstance(testing_data, list):
            testing_data = []
    except Exception:
        testing_data = []

    # load pre-step records
    pre_file = agent_dir / "pre_step.json"
    if pre_file.exists():
        try:
            pre_data = json.loads(pre_file.read_text(encoding="utf-8"))
        except Exception:
            pre_data = []
    else:
        pre_data = []

    step_num = clean.get("step_number")
    pre_record = next((r for r in pre_data if r.get("step_number") == step_num), {}) or {}
    ma = pre_record.get("model_actions") or {}
    new_records = []

    # record actual element actions (including navigation and waits)
    for el in clean.get("element_actions", []):
        action = el.get("action")

        # 1) Navigation steps: include actual URL
        if action in ("go_to_url", "navigate"):
            rec = {
                "step": step_num,
                "timestamp": el.get("timestamp"),
                "action": "navigate",
            }
            # Try to get URL from different sources
            url_val = el.get("url")
            if not url_val and isinstance(ma, dict):
                if isinstance(ma.get("go_to_url"), dict):
                    url_val = ma.get("go_to_url", {}).get("url")
            if not url_val:
                url_val = clean.get("url")
            
            # Add URL to record if found
            if url_val:
                rec["url"] = url_val
            
            new_records.append(rec)
            continue

        # 2) Wait steps: include recorded timeout
        if action == "wait":
            rec = {
                "step": step_num,
                "timestamp": el.get("timestamp"),
                "action": "wait",
            }
            
            # Try to get timeout from different sources
            timeout = el.get("timeout")
            
            # Fallback to pre_step wait seconds if element has no timeout
            if timeout is None and isinstance(ma, dict):
                if isinstance(ma.get("wait"), dict) and isinstance(ma["wait"].get("seconds"), (int, float)):
                    timeout = int(ma["wait"]["seconds"] * 1000)
            
            # Add timeout to record if found
            if timeout is not None:
                rec["timeout"] = timeout
            
            new_records.append(rec)
            continue

        # 3) Other interactions: click, fill, etc.
        rec = {
            "step": step_num,
            "timestamp": el.get("timestamp"),
            "action": action,
        }

        # selector priority: post css_selector -> post selector -> pre-record css
        sel = el.get("css_selector") or el.get("selector")
        ie = ma.get("interacted_element") or {}
        if not sel and isinstance(ie, dict):
            sel = ie.get("css_selector")
        if sel:
            rec["selector"] = sel

        # fill/text steps
        if action in ("fill", "input_text", "input"):
            text = el.get("text")
            if text is not None:
                rec["text"] = text

        # click steps
        if action == "click":
            btn = el.get("button")
            cnt = el.get("click_count")
            if btn is not None:
                rec["button"] = btn
            if cnt is not None:
                rec["click_count"] = cnt

        # success / error
        if isinstance(el.get("success"), bool):
            rec["success"] = el["success"]
        if el.get("error") is not None:
            rec["error"] = el["error"]

        new_records.append(rec)

    # save merged steps
    testing_data.extend(new_records)
    with testing_file.open("w", encoding="utf-8") as tf:
        json.dump(testing_data, tf, indent=2)

    logger.info(f"Appended {len(new_records)} records to {testing_file}")

    return {
        "status": "ok",
        "message": f"Appended step to {aggregate_file}",
        "event_type": event_type,
        "agent_id": agent_id
    }

@app.post("/save_log")
async def save_log(request: Request):
    data = await request.json()
    
    agent_id = data.get("agent_id", "general")
    log_entry = data.get("log_entry")
    
    logger.info(f"Saving log for agent {agent_id}")
    
    # Create agent-specific directory
    agent_dir = Path(DATA_DIR) / agent_id
    agent_dir.mkdir(exist_ok=True)
    
    # Create logs directory
    logs_dir = agent_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Get current date for log file naming
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file = logs_dir / f"{current_date}.log"
    
    # Append log entry to file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{log_entry}\n")
        
    return {
        "status": "ok",
        "message": f"Log saved for agent {agent_id}",
        "agent_id": agent_id
    }

@app.get("/api/generate")
async def generate_test(agentId: str, mode: str = "regular"):
    base_dir = Path(DATA_DIR) / agentId
    # Log the received mode parameter
    logger.info(f"Test generation requested for agent {agentId} with mode parameter: '{mode}'")
    
    # Normalize mode to lower‑case for flexible matching
    mode = (mode or "regular").lower()
    logger.info(f"Normalized mode: '{mode}', will use infor mode: {mode.startswith('infor')}")

    # Hard‑coded Chrome path for Infor mode
    INFOR_CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    # Path to the signed‑in Chrome *user‑data* directory we want to reuse
    # Root *user‑data* directory that contains the `Default/`, `Profile 1/`, … sub‑folders.
    # Playwright expects the root, not the nested 'Default' folder.
    INFOR_PROFILE_PATH = '/Users/nybruker/Library/Application Support/Google/Chrome'

    # Initial actions for Infor portal (navigate, then save with Ctrl+S)
    INFOR_INITIAL_ACTIONS = [
        "        # Initial actions for Infor portal (navigate, then save with Ctrl+S)",
        "        await page.goto('https://mingle-portal.inforcloudsuite.com/v2/ICSGDENA002_DEV/aa98233d-0f7f-4fe7-8ab8-b5b66eb494c6?favoriteContext=bookmark?OIS100%26%26%26undefined%26A%26Kundeordre.%20%C3%85pne%26OIS100%20Kundeordre.%20%C3%85pne&LogicalId=lid://infor.m3.m3prduse1b')",
        "        await page.wait_for_timeout(3000)",
        "        await page.goto('https://m3prduse1b.m3.inforcloudsuite.com/mne/infor?HybridCertified=1&xfo=https%3A%2F%2Fmingle-portal.inforcloudsuite.com&SupportWorkspaceFeature=0&Responsive=All&enable_health_service=true&portalV2Certified=1&LogicalId=lid%3A%2F%2Finfor.m3.m3&inforThemeName=Light&inforThemeColor=amber&inforCurrentLocale=en-US&inforCurrentLanguage=en-US&infor10WorkspaceShell=1&inforWorkspaceVersion=2025.03.03&inforOSPortalVersion=2025.03.03&inforTimeZone=(UTC%2B01%3A00)%20Dublin%2C%20Edinburgh%2C%20Lisbon%2C%20London&inforStdTimeZone=Europe%2FLondon&inforStartMode=3&inforTenantId=ICSGDENA002_DEV&inforSessionId=ICSGDENA002_DEV~6ba2f2fc-8f7b-4651-97de-06a45e5f54e7')",
        "        # Ensure the page has focus and trigger Ctrl+S (capital S required for Playwright)",
        "        await page.wait_for_timeout(3000)",
        "        await page.keyboard.press('Control+S')",  
    ]

    # Load distilled testing steps
    testing_file = base_dir / "testing_steps.json"
    if testing_file.exists():
        try:
            steps = json.loads(testing_file.read_text(encoding="utf-8"))
        except Exception as e:
            raise HTTPException(500, f"Error reading testing_steps.json: {e}")
        if not steps:
            raise HTTPException(404, "No testing steps found for this agent")
    else:
        raise HTTPException(404, "No testing_steps.json for this agent")

    # Build the Playwright script
    logger.info(f"Mode check: mode='{mode}', startswith('infor')={mode.startswith('infor')}")
    if mode.startswith("infor"):
        lines = [
            "import pytest",
            "import asyncio",
            "from playwright.async_api import async_playwright",
            "",
            "@pytest.mark.asyncio",
            "async def test_from_steps():",
            "    async with async_playwright() as p:",
            "        # Attach to the already‑running Chrome that was started with --remote-debugging-port=9222",
            "        browser = await p.chromium.connect_over_cdp('http://localhost:9222')",
            "        # Re‑use the first context if it exists, otherwise create one",
            "        context = browser.contexts[0] if browser.contexts else await browser.new_context()",
            "        page = await context.new_page()",
        ] + INFOR_INITIAL_ACTIONS
    else:
        lines = [
            "import pytest",
            "import asyncio",
            "from playwright.async_api import async_playwright",
            "",
            "@pytest.mark.asyncio",
            "async def test_from_steps():",
            "    async with async_playwright() as p:",
            "        browser = await p.chromium.launch(headless=False)",
            "        page = await browser.new_page()",
        ]
    for step in steps:
        action = step.get("action")
        sel = step.get("selector", "")
        
        # Check if selector is an element ID (not starting with #, ., or containing spaces/special chars)
        # and add # prefix if needed
        if sel and not sel.startswith(('#', '.')) and not any(c in sel for c in ' >+~:[]()'):
            # This is likely an element ID without the # prefix
            sel = f"#{sel}"
            
        if action == "navigate":
            url = step.get("url", "")
            lines.append(f"        await page.goto({url!r})")
        elif action == "click":
            btn = step.get("button", "left")
            count = step.get("click_count", 1)
            lines.append(f"        await page.click({sel!r}, button={btn!r}, click_count={count})")
        elif action == "wait":
            timeout = step.get("timeout", 0)
            lines.append(f"        await page.wait_for_timeout({timeout})")
        elif action in ("fill", "input"):
            text = step.get("text", "")
            lines.append(f"        await page.fill({sel!r}, {text!r})")

    if mode.startswith("infor"):
        lines.append("        await context.close()")
    else:
        lines.append("        await browser.close()")
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
