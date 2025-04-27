import { useAgent } from '../context/AgentContext';
import { useState, useEffect } from 'react';
import { agentApi } from '../services/api';
import type { Screenshot } from '../components/ScreenshotDisplay';

interface LogEntry {
  id: string;
  message: string;
  level: string;
  timestamp: string;
}

export function useAgentStream(agentId: string | null) {
  const { screenshots: historyScreenshots } = useAgent();
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [screenshots, setScreenshots] = useState<Screenshot[]>(
    historyScreenshots.map(s => ({
      id: `${agentId}-${s.step_number}`,
      url: s.url,
    }))
  );
  const [isRunning, setIsRunning] = useState<boolean>(false);

  useEffect(() => {
    if (!agentId) return;

    // Reset state and seed from history
    setLogs([]);
    setScreenshots(
      historyScreenshots.map(s => ({
        id: `${agentId}-${s.step_number}`,
        url: s.url,
      }))
    );
    setIsRunning(true);

    // Open SSE stream
    const es = agentApi.streamAgentEvents(agentId);

    es.addEventListener('log', (e: MessageEvent) => {
      let entry: any;
      try {
        entry = JSON.parse(e.data);
      } catch {
        entry = { timestamp: new Date().toISOString(), message: e.data, level: 'info' };
      }
      if (entry.agent_id && entry.agent_id !== agentId) return;
      setLogs(prev => [
        ...prev,
        {
          id: entry.timestamp,
          message: entry.message ?? JSON.stringify(entry.actions || entry),
          level: entry.level ?? 'info',
          timestamp: entry.timestamp,
        },
      ]);
    });

    es.addEventListener('screenshot', (e: MessageEvent) => {
      let entry: any;
      try {
        entry = JSON.parse(e.data);
      } catch {
        return;
      }
      if (entry.agent_id && entry.agent_id !== agentId) return;
      const raw = entry.data;
      const dataUrl = typeof raw === 'string' && raw.startsWith('data:')
        ? raw
        : `data:image/png;base64,${raw}`;
      const step = entry.step ?? Date.now();
      const uniqueId = `${agentId}-${step}-${Date.now()}`;
      setScreenshots(prev => [
        ...prev,
        { id: uniqueId, url: dataUrl },
      ]);
    });

    // Cleanup
    return () => {
      es.close();
      setIsRunning(false);
    };
  }, [agentId, historyScreenshots]);

  return { logs, screenshots, isRunning };
}