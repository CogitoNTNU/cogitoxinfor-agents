import os
import requests
import asyncio
import subprocess
from typing import Dict, Any, Optional

class MCPBridgeManager:
    """Manages the lifecycle of the MCP bridge server and MCP server"""
    
    def __init__(self, bridge_url: str = "http://localhost:3100"):
        self.bridge_url = bridge_url
        self.bridge_process = None
        self.mcp_running = False
        self.mcp_port = 8931
        
    async def start_bridge(self) -> bool:
        """Start the MCP bridge server if not already running"""
        try:
            # Check if bridge is already running
            try:
                response = requests.get(f"{self.bridge_url}/status", timeout=2)
                if response.ok:
                    print("Bridge server is already running")
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                print("Bridge server not running, starting it...")
            
            # Get absolute path to bridge script
            bridge_script = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), 
                "server", 
                "mcp-browser-bridge.js"
            )
            
            if not os.path.exists(bridge_script):
                print(f"Bridge script not found at: {bridge_script}")
                print(f"Current directory: {os.getcwd()}")
                print(f"Directory contents: {os.listdir(os.path.dirname(os.path.abspath(__file__)))}")
                return False
                
            # Print absolute path for debugging
            print(f"Starting bridge server from: {os.path.abspath(bridge_script)}")
            
            # Check if Node.js is installed
            try:
                node_version = subprocess.check_output(["node", "--version"], text=True).strip()
                print(f"Node.js version: {node_version}")
            except Exception as e:
                print(f"Error checking Node.js: {e}")
                print("Is Node.js installed? This is required for the browser bridge.")
                return False
                
            # Make sure required npm packages are installed
            server_dir = os.path.dirname(bridge_script)
            try:
                # Check if package.json exists
                if not os.path.exists(os.path.join(server_dir, "package.json")):
                    print("Creating package.json...")
                    subprocess.run(["npm", "init", "-y"], cwd=server_dir, check=True)
                
                # Install required packages
                print("Installing required npm packages...")
                subprocess.run(
                    ["npm", "install", "express", "cors", "socket.io", "node-fetch@2"],
                    cwd=server_dir,
                    check=True
                )
                print("Npm packages installed successfully")
            except Exception as e:
                print(f"Error installing npm packages: {e}")
                # Continue anyway, they might already be installed
            
            # Start Node.js process with more verbose output
            env = os.environ.copy()
            env["DEBUG"] = "socket.io:*"  # Enable Socket.IO debug logs
            
            # Kill any existing node processes running the bridge
            try:
                subprocess.run(["pkill", "-f", f"node {bridge_script}"], stderr=subprocess.DEVNULL)
                print("Killed any existing bridge processes")
                await asyncio.sleep(1)  # Give processes time to die
            except Exception as e:
                print(f"Error killing existing processes: {e}")
            
            # Start the bridge process
            self.bridge_process = subprocess.Popen(
                ["node", bridge_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.path.dirname(bridge_script)
            )
            
            # Start capturing stdout and stderr in background tasks
            asyncio.create_task(self._capture_process_output(self.bridge_process.stdout, "BRIDGE STDOUT"))
            asyncio.create_task(self._capture_process_output(self.bridge_process.stderr, "BRIDGE STDERR"))
            
            # Wait for the bridge server to start
            max_attempts = 15
            for attempt in range(max_attempts):
                await asyncio.sleep(1)
                try:
                    response = requests.get(f"{self.bridge_url}/status", timeout=2)
                    if response.ok:
                        print(f"Bridge server started successfully after {attempt+1} attempts")
                        return True
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                    if attempt % 5 == 0:
                        print(f"Waiting for bridge server to start (attempt {attempt+1}/{max_attempts})...")
            
            # If we get here, the server didn't start
            print("Failed to start bridge server after multiple attempts")
            print("Checking if the process is still running...")
            if self.bridge_process.poll() is None:
                print("Process is still running, but not responding to HTTP requests")
                # Kill the process and try again with direct console output
                self.bridge_process.terminate()
                await asyncio.sleep(1)
                
                # Start again with direct console output
                print("Starting bridge server with direct console output...")
                result = subprocess.run(
                    ["node", bridge_script],
                    text=True,
                    capture_output=True,
                    timeout=10
                )
                print(f"Bridge server output: {result.stdout}")
                print(f"Bridge server error: {result.stderr}")
            else:
                print(f"Process exited with code: {self.bridge_process.returncode}")
                
            return False
        except Exception as e:
            print(f"Error starting bridge server: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    async def start_mcp(self, headless: bool = True, browser: str = "chrome", 
                       vision: bool = True) -> Dict[str, Any]:
        """Start the MCP server via the bridge"""
        try:
            # Ensure bridge is running
            bridge_running = await self.start_bridge()
            if not bridge_running:
                return {"success": False, "message": "Bridge server not running"}
                
            # First, make sure we have Playwright MCP installed
            try:
                subprocess.run(["npx", "@playwright/mcp@latest", "--help"], 
                               stdout=subprocess.DEVNULL, 
                               stderr=subprocess.DEVNULL, 
                               check=True)
                print("Playwright MCP is available")
            except Exception:
                print("Playwright MCP not found, attempting to install...")
                try:
                    subprocess.run(["npm", "install", "-g", "@playwright/mcp"], check=True)
                    print("Playwright MCP installed globally")
                except Exception as e:
                    print(f"Failed to install Playwright MCP: {e}")
                    return {"success": False, "message": "Failed to install Playwright MCP"}
            
            # Kill any existing Chrome instances that might interfere
            try:
                print("Cleaning up any existing Chrome processes...")
                subprocess.run(["pkill", "-f", "chrome"], stderr=subprocess.DEVNULL)
                await asyncio.sleep(2)  # Give processes time to die
            except Exception:
                # It's okay if this fails - there might not be any Chrome processes running
                pass

            # Create a unique profile directory for Chrome
            import uuid
            import time
            unique_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
            profile_dir = os.path.abspath(f"/tmp/playwright-profile-{unique_id}")
            os.makedirs(profile_dir, exist_ok=True)
            print(f"Using unique browser profile at: {profile_dir}")
            
            # Set environment variables for headless browser
            os.environ["PLAYWRIGHT_CHROMIUM_HEADLESS"] = "1"
            os.environ["DISPLAY"] = ""  # Unset display to prevent window creation
            
            # Start the MCP server via the bridge
            print("Starting MCP server via bridge...")
            
            start_payload = {
                "browser": browser,
                "vision": vision, 
                "headless": headless,
                "new_headless": True,
                "userDataDir": profile_dir,
                "sse_timeout": 60000,
                "args": [
                    "--headless=new",
                    "--disable-gpu",
                    "--no-sandbox",
                    "--disable-dev-shm-usage"
                ]
            }
            
            response = requests.post(
                f"{self.bridge_url}/start",
                json=start_payload,
                headers={"Content-Type": "application/json"},
                timeout=20  # Increased timeout for server start
            )
            
            if not response.ok:
                print(f"Failed to start MCP server: {response.text}")
                return {"success": False, "message": f"Failed to start MCP server: {response.text}"}
                
            # Wait longer for the server to start
            print("Waiting for MCP server to start...")
            await asyncio.sleep(8)
            
            # Check if server is running
            max_checks = 5
            for i in range(max_checks):
                status = await self.check_status()
                if status.get("running", False):
                    self.mcp_running = True
                    return {"success": True, "port": self.mcp_port}
                
                print(f"MCP server not running yet. Check {i+1}/{max_checks}. Waiting...")
                await asyncio.sleep(2)  # Wait between checks
            
            # If we get here, the server didn't start properly
            print("MCP server didn't start properly after multiple checks")
            return {"success": False, "message": "MCP server started but not responding"}
                
        except Exception as e:
            print(f"Error starting MCP server: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e)}
            
    async def check_status(self) -> Dict[str, Any]:
        """Check if the MCP server is running"""
        try:
            # Check bridge server first
            try:
                bridge_response = requests.get(f"{self.bridge_url}/status", timeout=2)
                if not bridge_response.ok:
                    return {"running": False, "message": "Bridge server not running"}
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                return {"running": False, "message": "Bridge server not running"}
                
            # Get status from bridge
            try:
                status_response = requests.get(f"{self.bridge_url}/mcp/status", timeout=2)
                if status_response.ok:
                    status_data = status_response.json()
                    return {
                        "running": status_data.get("status") == "running",
                        "port": self.mcp_port,
                        **status_data
                    }
                else:
                    print(f"Failed to get MCP status: {status_response.status_code} {status_response.text}")
                    return {"running": False, "message": "Failed to get MCP status"}
            except Exception as e:
                print(f"Error checking MCP status: {e}")
                return {"running": False, "message": str(e)}
                
        except Exception as e:
            print(f"Error checking status: {e}")
            return {"running": False, "message": str(e)}
            
    async def stop_mcp(self) -> Dict[str, Any]:
        """Stop the MCP server"""
        try:
            response = requests.post(f"{self.bridge_url}/stop")
            if response.ok:
                self.mcp_running = False
                return {"success": True, "message": "MCP server stopped"}
            else:
                return {"success": False, "message": f"Failed to stop MCP server: {response.text}"}
        except Exception as e:
            return {"success": False, "message": str(e)}
            
    async def _capture_process_output(self, stream, prefix):
        """Capture and log output from a subprocess stream"""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, stream.readline)
                if not line:
                    break
                print(f"{prefix}: {line.strip()}")
            except Exception as e:
                print(f"Error capturing process output: {e}")
                break