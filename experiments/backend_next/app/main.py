# backend_next/app/main.py

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import json
from subprocess import CalledProcessError

def mb_start_browser_py():
    # uses the 'mb' CLI binary to start a browser session
    try:
        out = subprocess.check_output(
            ["mb", "browser", "start", "--json"], stderr=subprocess.STDOUT
        )
    except CalledProcessError as e:
        # surface the CLI error message in the HTTP response
        err = e.output.decode("utf-8", errors="ignore")
        raise HTTPException(status_code=500, detail=f"mb browser start failed: {err}")
    data = json.loads(out)
    return data.get("session_id") or data.get("sessionId")

def mb_use_browser_tool_py(session_id: str, command: str):
    # uses the 'mb' CLI to execute a browser command
    try:
        out = subprocess.check_output([
            "mb", "browser", "use",
            "--session-id", session_id,
            "--command", command,
            "--json"
        ], stderr=subprocess.STDOUT)
    except CalledProcessError as e:
        err = e.output.decode("utf-8", errors="ignore")
        raise HTTPException(status_code=500, detail=f"mb browser use failed: {err}")
    data = json.loads(out)
    # The CLI returns result under 'output' or 'result'
    return data.get("result") or data.get("output") or ""

def mb_stop_browser_py(session_id: str):
    # uses the 'mb' CLI to stop the browser session
    try:
        subprocess.check_call([
            "mb", "browser", "stop",
            "--session-id", session_id
        ])
    except CalledProcessError as e:
        err = e.output.decode("utf-8", errors="ignore") if hasattr(e, "output") and e.output else str(e)
        raise HTTPException(status_code=500, detail=f"mb browser stop failed: {err}")

# Load environment variables
load_dotenv()

app = FastAPI(title="MarinaBox Browser API")

# Pydantic models
class StartResponse(BaseModel):
    session_id: str

class ToolRequest(BaseModel):
    session_id: str
    command: str

class ToolResponse(BaseModel):
    result: str

class StopRequest(BaseModel):
    session_id: str

# Endpoints
@app.post("/api/browser/start", response_model=StartResponse)
async def start_browser():
    # Start browser via CLI function
    sid = mb_start_browser_py()
    return StartResponse(session_id=sid)

@app.post("/api/browser/tool", response_model=ToolResponse)
async def use_browser_tool(req: ToolRequest):
    try:
        result = mb_use_browser_tool_py(req.session_id, req.command)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    # coerce to string
    if result is None:
        result_str = ""
    elif not isinstance(result, str):
        result_str = str(result)
    else:
        result_str = result
    return ToolResponse(result=result_str)

@app.post("/api/browser/stop")
async def stop_browser(req: StopRequest):
    mb_stop_browser_py(req.session_id)
    return {"status": "stopped"}