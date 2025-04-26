# FastAPI Browser Agent Example

This example demonstrates how to create a web interface for controlling a Browser Agent using FastAPI.

## Requirements

```bash
uv pip install fastapi uvicorn sse-starlette langchain-openai
```

## Running the Example

1. Navigate to the fastapi example directory:
```bash
cd examples/fastapi
```

2. Run the FastAPI application:
```bash
python main.py
```

3. Open your web browser and navigate to `http://localhost:8000`


## API Endpoints

- `GET /` - Serves the web interface
- `POST /agent/run` - Creates and runs an agent with the specified task
- `POST /agent/pause` - Pauses the current agent
- `POST /agent/resume` - Resumes the paused agent
- `POST /agent/stop` - Stops the current agent
- `GET /agent/status` - Gets the current status of the agent
- `GET /logs` - Server-sent events endpoint for real-time logs 