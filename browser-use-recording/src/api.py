#!/usr/bin/env python3

import json
import base64
from pathlib import Path

from fastapi import FastAPI, Request
import prettyprinter
import uvicorn

prettyprinter.install_extras()

# Initialize FastAPI app
app = FastAPI()

# Utility function to save screenshots
def b64_to_png(b64_string: str, output_file):
    """
    Convert a Base64-encoded string to a PNG file.
    
    :param b64_string: A string containing Base64-encoded data
    :param output_file: The path to the output PNG file
    """
    with open(output_file, "wb") as f:
        f.write(base64.b64decode(b64_string))


@app.get("/")
async def root():
    """Simple health check endpoint"""
    return {"status": "API is running"}


@app.post("/post_agent_history_step")
async def post_agent_history_step(request: Request):
    data = await request.json()
    prettyprinter.cpprint(data)

    # Ensure the data directories exist
    data_dir = Path("../data")
    data_dir.mkdir(exist_ok=True)
    
    recordings_dir = data_dir / "agent_history"
    recordings_dir.mkdir(exist_ok=True)
    
    screenshots_dir = data_dir / "screenshots"
    screenshots_dir.mkdir(exist_ok=True)
    
    html_dir = data_dir / "html_content"
    html_dir.mkdir(exist_ok=True)

    # Determine the next file number by examining existing .json files
    existing_numbers = []
    for item in recordings_dir.iterdir():
        if item.is_file() and item.suffix == ".json":
            try:
                file_num = int(item.stem)
                existing_numbers.append(file_num)
            except ValueError:
                # In case the file name isn't just a number
                pass

    if existing_numbers:
        next_number = max(existing_numbers) + 1
    else:
        next_number = 1

    # Construct the file path
    file_path = recordings_dir / f"{next_number}.json"

    # Extract the screenshot and HTML before saving the main JSON
    website_screenshot = data.get("website_screenshot")
    website_html = data.get("website_html")
    
    # Remove large fields from the JSON before saving
    clean_data = {**data}
    if website_screenshot:
        clean_data["website_screenshot"] = f"See screenshots/{next_number}.png"
        
        # Save the screenshot
        screenshot_path = screenshots_dir / f"{next_number}.png"
        b64_to_png(website_screenshot, screenshot_path)
    
    if website_html:
        clean_data["website_html"] = f"See html_content/{next_number}.html"
        
        # Save the HTML
        html_path = html_dir / f"{next_number}.html"
        with html_path.open("w", encoding="utf-8") as f:
            f.write(website_html)

    # Save the JSON data to the file
    with file_path.open("w") as f:
        json.dump(clean_data, f, indent=2)

    return {
        "status": "ok", 
        "message": f"Saved to {file_path}",
        "file_id": next_number
    }


if __name__ == "__main__":
    print("Starting Browser-Use recording API on http://0.0.0.0:9000")
    uvicorn.run(app, host="0.0.0.0", port=9000)