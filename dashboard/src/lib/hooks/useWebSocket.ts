import { useEffect, useRef, useState, useCallback } from 'react';
import type { LogMessage, SystemEvent } from '../types';
import { getWebSocketBaseUrl } from '../config';

const WS_BASE_URL = getWebSocketBaseUrl();

interface UseWebSocketOptions {
  onMessage?: (message: any) => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export const useWebSocket = (url: string, options: UseWebSocketOptions = {}) => {
  const {
    onMessage,
    onError,
    reconnectInterval = 5000,
    maxReconnectAttempts = 10,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<number | undefined>();
  const isConnectingRef = useRef(false);
  const backoffRef = useRef(reconnectInterval);
  // Keep latest handlers in refs to avoid reconnects on render
  const onMessageRef = useRef<typeof onMessage>();
  const onErrorRef = useRef<typeof onError>();

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  useEffect(() => {
    onErrorRef.current = onError;
  }, [onError]);

  const connect = useCallback(() => {
    if (wsRef.current || isConnectingRef.current) return;
    try {
      isConnectingRef.current = true;
      const fullUrl = url.startsWith('ws') ? url : `${WS_BASE_URL}${url}`;
      console.log(`[WS] connecting ${fullUrl}`);
      const ws = new WebSocket(fullUrl);

      ws.onopen = () => {
        console.log('[WS] open');
        setIsConnected(true);
        setError(null);
        reconnectAttemptsRef.current = 0;
        backoffRef.current = reconnectInterval;
        isConnectingRef.current = false;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          onMessageRef.current?.(data);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.warn('[WS] error');
        setError('WebSocket error occurred');
        onErrorRef.current?.(event);
      };

      ws.onclose = () => {
        console.log('[WS] close');
        setIsConnected(false);
        wsRef.current = null;
        isConnectingRef.current = false;
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          const delay = Math.min(backoffRef.current, 30000);
          console.log(`[WS] reconnect in ${delay}ms`);
          reconnectTimeoutRef.current = window.setTimeout(() => {
            backoffRef.current = Math.min(backoffRef.current * 2, 30000);
            connect();
          }, delay);
        } else {
          setError('Max reconnection attempts reached');
        }
      };

      wsRef.current = ws;
    } catch (err) {
      setError('Failed to create WebSocket connection');
      console.error('WebSocket connection error:', err);
      isConnectingRef.current = false;
    }
  }, [url, reconnectInterval, maxReconnectAttempts]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (wsRef.current) {
        try {
          console.log('[WS] cleanup close');
          wsRef.current.close();
        } catch {}
      }
      wsRef.current = null;
      isConnectingRef.current = false;
    };
  }, [connect]);

  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, error, send };
};

export const useAgentLogs = (agentName: string) => {
  const [logs, setLogs] = useState<LogMessage[]>([]);

  const { isConnected, error } = useWebSocket(`/ws/logs/${agentName}`, {
    onMessage: (message: any) => {
      const t = message?.timestamp;
      const kind = message?.type;
      if (kind === 'connected' || kind === 'status') return;
      let tsNum: number = typeof t === 'number' ? t : Date.now();
      if (tsNum < 1e12) tsNum = Math.floor(tsNum * 1000);
      const level: LogMessage['level'] = String(message?.level || 'INFO').toUpperCase() as any;
      const msgText: string = typeof message?.message === 'string' ? message.message : JSON.stringify(message);
      const log: LogMessage = {
        timestamp: new Date(tsNum).toISOString(),
        level,
        agent_name: agentName,
        message: msgText,
      };
      setLogs((prev) => [...prev, log].slice(-100));
    },
  });

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return { logs, isConnected, error, clearLogs };
};

export const useSystemEvents = () => {
  const [events, setEvents] = useState<SystemEvent[]>([]);

  const { isConnected, error } = useWebSocket('/ws/events', {
    onMessage: (event: any) => {
      const t = event?.timestamp;
      const typ = event?.event_type || event?.type;
      if (typ === 'system_status' || typ === 'connected') return;
      let tsNum: number = typeof t === 'number' ? t : Date.now();
      if (tsNum < 1e12) tsNum = Math.floor(tsNum * 1000);
      const normalized: SystemEvent = {
        event_type: (typ || 'event') as any,
        timestamp: new Date(tsNum).toISOString(),
        data: (event?.data ?? event) as any,
      };
      setEvents((prev) => [normalized, ...prev].slice(0, 50));
    },
  });

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return { events, isConnected, error, clearEvents };
};

export const usePromptTraces = (promptId: string | null) => {
  const [traces, setTraces] = useState<any[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  // Clear traces when promptId changes to prevent mixing traces from different prompts
  useEffect(() => {
    setTraces([]);
    setIsComplete(false);
    setStatus(null);
  }, [promptId]);

  const { isConnected, error } = useWebSocket(
    promptId ? `/ws/prompts/${promptId}` : '',
    {
      onMessage: (message: any) => {
        if (message.type === 'trace' && message.data) {
          setTraces((prev) => [...prev, message.data]);
        } else if (message.type === 'complete' && message.data) {
          setIsComplete(true);
          setStatus(message.data.status);
        } else if (message.type === 'error') {
          setIsComplete(true);
          setStatus('error');
        }
      },
    }
  );

  const clearTraces = useCallback(() => {
    setTraces([]);
    setIsComplete(false);
    setStatus(null);
  }, []);

  return { traces, isConnected, isComplete, status, error, clearTraces };
};

export const usePlaygroundTraces = (playgroundId: string | null) => {
  const [traces, setTraces] = useState<any[]>([]);
  const [isComplete, setIsComplete] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  // Clear traces when playgroundId changes to prevent mixing traces from different runs
  useEffect(() => {
    setTraces([]);
    setIsComplete(false);
    setStatus(null);
  }, [playgroundId]);

  const { isConnected, error } = useWebSocket(
    playgroundId ? `/ws/prompts/${playgroundId}` : '',
    {
      onMessage: (message: any) => {
        if (message.type === 'traces' && message.data) {
          // New hierarchical structure: data contains {spans: [...], count: n}
          if (message.data.spans && Array.isArray(message.data.spans)) {
            // Backend sends incremental updates with new spans
            // We need to merge them with existing spans
            setTraces((prev) => {
              const existingSpans = prev[0]?.spans || [];
              const newSpans = message.data.spans;
              
              // Create a map of existing spans by ID for quick lookup
              const spanMap = new Map();
              
              // Helper to add spans to map recursively
              const addToMap = (spans: any[]) => {
                spans.forEach(span => {
                  spanMap.set(span.id, span);
                  if (span.children && span.children.length > 0) {
                    addToMap(span.children);
                  }
                });
              };
              
              // Add existing spans to map
              addToMap(existingSpans);
              
              // Add/update with new spans (this handles updates to existing spans too)
              addToMap(newSpans);
              
              // For simplicity, just append new unique spans
              const existingIds = new Set(existingSpans.map((s: any) => s.id));
              const spansToAdd = newSpans.filter((s: any) => !existingIds.has(s.id));
              
              return [{ spans: [...existingSpans, ...spansToAdd] }];
            });
          }
        } else if (message.type === 'trace' && message.data) {
          // Legacy flat trace format (fallback)
          setTraces((prev) => [...prev, message.data]);
        } else if (message.type === 'complete' && message.data) {
          setIsComplete(true);
          setStatus(message.data.status);
          // Update with final complete spans if provided (this is the full tree)
          if (message.data.spans && Array.isArray(message.data.spans)) {
            setTraces([{ spans: message.data.spans }]);
          }
        } else if (message.type === 'error') {
          setIsComplete(true);
          setStatus('error');
        }
      },
    }
  );

  const clearTraces = useCallback(() => {
    setTraces([]);
    setIsComplete(false);
    setStatus(null);
  }, []);

  return { traces, isConnected, isComplete, status, error, clearTraces };
};
