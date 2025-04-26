// mcp-browser-bridge.js
// This server acts as a bridge between Playwright MCP and your frontend

const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const { spawn } = require('child_process');
const cors = require('cors');
const fetch = require('node-fetch');

// Create Express app
const app = express();
app.use(cors());
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: '*',
    methods: ['GET', 'POST']
  }
});

// Track active MCP server process
let mcpProcess = null;
let mcpPort = 8931; // Default port for MCP
let screenshotInterval = null;

// Start MCP server with specified options
function startMCPServer(options = {}) {
  const args = [
    '@playwright/mcp@latest',
    '--port', mcpPort.toString()
  ];
  
  // Add additional options
  if (options.headless) args.push('--headless');
  if (options.vision) args.push('--vision');
  if (options.browser) {
    args.push('--browser', options.browser);
  }
  if (options.userDataDir) {
    args.push('--user-data-dir', options.userDataDir);
  }
  
  console.log(`Starting MCP server with args: npx ${args.join(' ')}`);
  
  mcpProcess = spawn('npx', args, {
    stdio: 'pipe',
    shell: true
  });
  
  mcpProcess.stdout.on('data', (data) => {
    console.log(`MCP stdout: ${data}`);
    io.emit('mcp-log', { type: 'stdout', data: data.toString() });
  });
  
  mcpProcess.stderr.on('data', (data) => {
    console.error(`MCP stderr: ${data}`);
    io.emit('mcp-log', { type: 'stderr', data: data.toString() });
  });
  
  mcpProcess.on('close', (code) => {
    console.log(`MCP process exited with code ${code}`);
    io.emit('mcp-status', { status: 'stopped', exitCode: code });
    mcpProcess = null;
    
    // Stop screenshot interval if it's running
    if (screenshotInterval) {
      clearInterval(screenshotInterval);
      screenshotInterval = null;
    }
  });
  
  // Wait a moment for the server to start
  setTimeout(() => {
    io.emit('mcp-status', { status: 'running', port: mcpPort });
    
    // Start capturing screenshots if not headless
    if (!options.headless) {
      startScreenshotCapture();
    }
  }, 2000);
}

// Stop the MCP server
function stopMCPServer() {
  if (mcpProcess) {
    mcpProcess.kill();
    mcpProcess = null;
    
    if (screenshotInterval) {
      clearInterval(screenshotInterval);
      screenshotInterval = null;
    }
    
    io.emit('mcp-status', { status: 'stopped' });
    return true;
  }
  return false;
}

// Start capturing screenshots at regular intervals
function startScreenshotCapture(interval = 1000) {
  if (screenshotInterval) {
    clearInterval(screenshotInterval);
  }
  
  screenshotInterval = setInterval(async () => {
    try {
      // Make an MCP tool call to take a screenshot
      const response = await fetch(`http://localhost:${mcpPort}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tool: 'browser_take_screenshot',
          input: {}
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        if (result.output && result.output.data) {
          // Send screenshot to connected clients
          io.emit('screenshot', { data: result.output.data });
        }
      }
    } catch (err) {
      console.error('Error capturing screenshot:', err.message);
    }
  }, interval);
}

// Execute an MCP tool directly
async function executeMCPTool(tool, input = {}) {
  try {
    const response = await fetch(`http://localhost:${mcpPort}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        tool,
        input
      })
    });
    
    return await response.json();
  } catch (err) {
    console.error(`Error executing MCP tool ${tool}:`, err.message);
    return { error: err.message };
  }
}

// Express Routes
app.get('/', (req, res) => {
  res.send('MCP Browser Bridge Server');
});

app.get('/status', (req, res) => {
  res.json({
    mcpRunning: mcpProcess !== null,
    mcpPort
  });
});

app.post('/start', (req, res) => {
  if (mcpProcess) {
    return res.status(400).json({ error: 'MCP server already running' });
  }
  
  startMCPServer(req.body || {});
  res.json({ success: true, message: 'MCP server starting' });
});

app.post('/stop', (req, res) => {
  const stopped = stopMCPServer();
  res.json({ success: stopped });
});

app.post('/execute', async (req, res) => {
  if (!mcpProcess) {
    return res.status(400).json({ error: 'MCP server not running' });
  }
  
  const { tool, input } = req.body;
  if (!tool) {
    return res.status(400).json({ error: 'Tool name required' });
  }
  
  try {
    const result = await executeMCPTool(tool, input || {});
    res.json(result);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// Socket.IO event handlers
io.on('connection', (socket) => {
  console.log('Client connected');
  
  // Send current status
  socket.emit('mcp-status', { 
    status: mcpProcess ? 'running' : 'stopped',
    port: mcpPort
  });
  
  socket.on('start-mcp', (options) => {
    if (!mcpProcess) {
      startMCPServer(options);
    }
  });
  
  socket.on('stop-mcp', () => {
    stopMCPServer();
  });
  
  socket.on('execute-tool', async (data, callback) => {
    if (!mcpProcess) {
      callback({ error: 'MCP server not running' });
      return;
    }
    
    try {
      const result = await executeMCPTool(data.tool, data.input || {});
      callback(result);
    } catch (err) {
      callback({ error: err.message });
    }
  });
  
  socket.on('disconnect', () => {
    console.log('Client disconnected');
  });
});

// Start server
const PORT = process.env.PORT || 3100;
server.listen(PORT, () => {
  console.log(`MCP Browser Bridge running on port ${PORT}`);
});