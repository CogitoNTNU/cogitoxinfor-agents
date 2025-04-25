# mcp_bridge.py
# This module provides integration between your Python MCPAgent and the JavaScript bridge server

import asyncio
import json
import os
import requests
import websockets
from typing import Dict, Any, Optional, Callable, List

class MCPBridge:
    """Bridge between Python MCPAgent and the JS-based MCP server"""
    
    def __init__(self, bridge_url: str = "http://localhost:3100", websocket_url: str = "ws://localhost:3100"):
        self.bridge_url = bridge_url
        self.websocket_url = websocket_url
        self.websocket = None
        self.screenshot_callbacks = []
        self.log_callbacks = []
        self.status_callbacks = []
        self._ws_task = None
        
    async def start(self, options: Dict[str, Any] = None) -> bool:
        """Start the MCP server with the given options"""
        try:
            # Check if server is already running
            response = requests.get(f"{self.bridge_url}/status")
            status = response.json()
            
            if status.get("mcpRunning"):
                print("MCP server is already running")
                return True
                
            # Start server
            if options is None:
                options = {}
                
            response = requests.post(
                f"{self.bridge_url}/start",
                json=options,
                headers={"Content-Type": "application/json"}
            )
            
            result = response.json()
            if result.get("success"):
                print("MCP server starting")
                # Start WebSocket listener if not already running
                await self._ensure_websocket_connected()
                return True
            else:
                print(f"Failed to start MCP server: {result.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"Error starting MCP server: {str(e)}")
            return False
            
    async def stop(self) -> bool:
        """Stop the MCP server"""
        try:
            response = requests.post(f"{self.bridge_url}/stop")
            result = response.json()
            
            if result.get("success"):
                print("MCP server stopped")
                # Close websocket connection
                await self._close_websocket()
                return True
            else:
                print("Failed to stop MCP server")
                return False
                
        except Exception as e:
            print(f"Error stopping MCP server: {str(e)}")
            return False
            
    async def execute_tool(self, tool: str, input_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute an MCP tool on the server"""
        if input_data is None:
            input_data = {}
            
        try:
            response = requests.post(
                f"{self.bridge_url}/execute",
                json={"tool": tool, "input": input_data},
                headers={"Content-Type": "application/json"}
            )
            
            return response.json()
        except Exception as e:
            print(f"Error executing tool {tool}: {str(e)}")
            return {"error": str(e)}
            
    async def take_screenshot(self) -> Optional[str]:
        """Take a screenshot and return the base64 data"""
        result = await self.execute_tool("browser_take_screenshot")
        if "error" not in result and "output" in result and "data" in result["output"]:
            return result["output"]["data"]
        return None
        
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate the browser to a URL"""
        return await self.execute_tool("browser_navigate", {"url": url})
        
    # WebSocket handling
    async def _ensure_websocket_connected(self):
        """Ensure the WebSocket connection is active"""
        if self._ws_task is None or self._ws_task.done():
            self._ws_task = asyncio.create_task(self._websocket_listener())
            
    async def _close_websocket(self):
        """Close the WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None
            
    async def _websocket_listener(self):
        """Listen for WebSocket messages"""
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                self.websocket = websocket
                
                while True:
                    message = await websocket.recv()
                    data = json.loads(message)
                    
                    event_type = data.get("type")
                    if event_type == "screenshot" and "data" in data:
                        for callback in self.screenshot_callbacks:
                            callback(data["data"])
                    elif event_type == "mcp-log" and "data" in data:
                        for callback in self.log_callbacks:
                            callback(data["data"], data.get("type", "stdout"))
                    elif event_type == "mcp-status":
                        for callback in self.status_callbacks:
                            callback(data.get("status"), data)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"WebSocket error: {str(e)}")
        finally:
            self.websocket = None
            
    # Callback registration
    def on_screenshot(self, callback: Callable[[str], None]):
        """Register callback for screenshot events"""
        self.screenshot_callbacks.append(callback)
        return self
        
    def on_log(self, callback: Callable[[str, str], None]):
        """Register callback for log events"""
        self.log_callbacks.append(callback)
        return self
        
    def on_status(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Register callback for status events"""
        self.status_callbacks.append(callback)
        return self


# Integration with your MCPAgent class

async def integrate_mcp_agent_with_bridge(mcp_agent, bridge_url="http://localhost:3100"):
    """Connect your MCPAgent with the MCP Bridge"""
    bridge = MCPBridge(bridge_url)
    
    # Override the initialize method to use the bridge
    original_initialize = mcp_agent.initialize
    
    async def new_initialize():
        # First start the bridge server
        success = await bridge.start({
            "vision": True,  # Enable vision mode for screenshots
            "browser": "chrome"
        })
        
        if not success:
            print("Failed to start MCP bridge server")
            return False
            
        # Now run the original initialize
        return await original_initialize()
    
    # Replace the method
    mcp_agent.initialize = new_initialize
    
    # Add method to get screenshots directly
    async def get_screenshot():
        return await bridge.take_screenshot()
    
    mcp_agent.get_screenshot = get_screenshot
    
    # Add the bridge reference
    mcp_agent.bridge = bridge
    
    return bridge


from ..mcp_agent import MCPAgent

async def main():
    agent = MCPAgent()
    bridge = await integrate_mcp_agent_with_bridge(agent)
    
    # Initialize agent (will also start bridge server)
    await agent.initialize()
    
    # Get a screenshot directly
    screenshot_data = await agent.get_screenshot()
    if screenshot_data:
        print("Screenshot taken successfully")
    else:
        print("Failed to take screenshot")
    # Stop the bridge server when done  
    await bridge.stop()

if __name__ == "__main__":
    asyncio.run(main())
    # This is just for testing purposes
    # In a real application, you would integrate this into your existing codebase
# and call the methods as needed.
# Note: This code assumes that the MCP server is running and accessible at the specified URLs.
# You may need to adjust the URLs and options based on your specific setup.