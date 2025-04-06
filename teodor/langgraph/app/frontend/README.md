# Next.js Chat Application

This is a simple chat application built using Next.js. It utilizes WebSocket for real-time communication and provides a responsive layout that adapts to different screen sizes.

## Project Structure

The project is organized as follows:

```
nextjs-chat-app
├── app
│   ├── favicon.ico          # Favicon for the application
│   ├── globals.css          # Global CSS styles
│   ├── layout.js            # Layout component for consistent structure
│   ├── page.js              # Main entry point for the application
│   └── app
│       └── chat
│           └── page.js      # Chat page component
├── contexts
│   ├── ViewportContext.js    # Context provider for viewport-related state
│   └── WebSocketContext.js    # Context provider for WebSocket connections
├── services
│   └── websocket.js          # Functions for handling WebSocket connections
├── public                    # Directory for static assets
├── .gitignore                # Files and directories to ignore by Git
├── eslint.config.mjs        # ESLint configuration
├── next.config.js           # Next.js application configuration
├── package.json              # npm configuration file
├── postcss.config.mjs       # PostCSS configuration
└── README.md                 # Documentation for the project
```

## Installation

To get started with the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```
   cd nextjs-chat-app
   ```

3. Install the dependencies:
   ```
   npm install
   ```

## Usage

To run the application in development mode, use the following command:

```
npm run dev
```

This will start the Next.js development server, and you can view the application in your browser at `http://localhost:3000`.

## Features

- Real-time chat functionality using WebSocket.
- Responsive design that adapts to different screen sizes.
- Context API for managing global state related to viewport and WebSocket connections.

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.