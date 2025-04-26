export const API_BASE_URL = 'http://localhost:8000';
export const WS_BASE_URL = 'ws://localhost:8000';

export const endpoints = {
  runAgent: '/api/agent/run',
  websocket: (sessionId) => `/api/ws/${sessionId}`,
  screenshot: (sessionId, step) => `/api/history/${sessionId}/${step}`
};