

import { useState, useEffect } from 'react';
import { agentApi } from '../services/api';

interface LogEntry {
  id: string;
  message: string;
  level: string;
  timestamp: string;
}

export function useAgentStream(agentId: string | null) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [screenshots, setScreenshots] = useState<string[]>([]);
  const [isRunning, setIsRunning] = useState<boolean>(false);

  useEffect(() => {
    if (!agentId) return;
    setLogs([]);
    setScreenshots([]);
    setIsRunning(true);

    const es = agentApi.streamAgentEvents();

    es.addEventListener('log', (e: MessageEvent) => {
      let entry: any;
      try {
        entry = JSON.parse(e.data);
      } catch {
        entry = { timestamp: new Date().toISOString(), message: e.data, level: 'info' };
      }
      setLogs(prev => [
        ...prev,
        {
          id: entry.timestamp,
          message: entry.message ?? JSON.stringify(entry.actions || entry),
          level: entry.level ?? 'action',
          timestamp: entry.timestamp,
        },
      ]);
    });

    es.addEventListener('screenshot', (e: MessageEvent) => {
      const { agent_id, data } = JSON.parse(e.data);
      if (agent_id === agentId) {
        setScreenshots(prev => [...prev, data]);
      }
    });

    es.addEventListener('open', () => {
      // connection established
    });
    es.addEventListener('error', (ev) => {
      if (es.readyState === EventSource.CLOSED) {
        setIsRunning(false);
        es.close();
      }
    });

    return () => {
      es.close();
      setIsRunning(false);
    };
  }, [agentId]);

  return { logs, screenshots, isRunning };
}