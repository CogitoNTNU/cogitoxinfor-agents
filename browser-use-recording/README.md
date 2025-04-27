# Browser-Use Activity Recording

This project implements a Browser-Use agent that records its activity and sends the data to a FastAPI server for storage and analysis. The agent captures various aspects of its browsing session, including HTML content, screenshots, and model thoughts.

## Project Structure

```
browser-use-recording
├── src
│   ├── api.py               # FastAPI server for recording agent activity
│   ├── client.py            # Client to run the Browser-Use agent
│   ├── utils
│   │   ├── __init__.py      # Initialization file for utils module
│   │   └── data_processing.py # Utility functions for data processing
│   └── config
│       ├── __init__.py      # Initialization file for config module
│       └── settings.py       # Configuration settings for the application
├── data
│   ├── screenshots           # Directory for storing screenshots
│   ├── html_content          # Directory for storing HTML content
│   └── agent_history         # Directory for storing recorded agent history
├── .env                      # Environment variables (e.g., API keys)
├── requirements.txt          # Required Python packages and dependencies
└── README.md                 # Project documentation
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd browser-use-recording
   ```

2. **Install dependencies:**
   Make sure you have Python 3.7 or higher installed. Then, install the required packages using pip:
   ```
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the root directory and add any necessary environment variables, such as API keys.

4. **Run the FastAPI server:**
   Start the server by running:
   ```
   python src/api.py
   ```

5. **Run the Browser-Use agent:**
   In a separate terminal, run the client to start the agent:
   ```
   python src/client.py
   ```

## Usage Guidelines

- The agent will automatically record its activity and send the data to the FastAPI server.
- Screenshots and HTML content will be saved in their respective directories under `data/`.
- Agent history will be stored in JSON format in the `data/agent_history` directory.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.