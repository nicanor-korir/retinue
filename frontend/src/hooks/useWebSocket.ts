/**
 * WebSocket hook for real-time event streaming
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { WebSocketMessage, WebSocketEvent } from '@/types/events';

interface UseWebSocketOptions {
  projectId?: string;
  agentId?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
  reconnectInterval?: number;
  reconnectAttempts?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  send: (data: any) => void;
  disconnect: () => void;
  reconnect: () => void;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const {
    projectId,
    agentId,
    onMessage,
    onError,
    reconnectInterval = 3000,
    reconnectAttempts = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  // Build WebSocket URL
  const getWsUrl = useCallback(() => {
    if (projectId) {
      return `${WS_BASE_URL}/api/v1/ws/projects/${projectId}`;
    } else if (agentId) {
      return `${WS_BASE_URL}/api/v1/ws/agents/${agentId}`;
    } else {
      return `${WS_BASE_URL}/api/v1/ws/stream`;
    }
  }, [projectId, agentId]);

  // Send ping to keep connection alive
  const startPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 30000); // Ping every 30 seconds
  }, []);

  // Stop ping interval
  const stopPingInterval = useCallback(() => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      const url = getWsUrl();
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected:', url);
        setIsConnected(true);
        reconnectCountRef.current = 0;
        startPingInterval();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        stopPingInterval();

        // Attempt to reconnect
        if (shouldReconnectRef.current && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current++;
          console.log(`Reconnecting... Attempt ${reconnectCountRef.current}/${reconnectAttempts}`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
    }
  }, [getWsUrl, onMessage, onError, reconnectInterval, reconnectAttempts, startPingInterval, stopPingInterval]);

  // Send message
  const send = useCallback((data: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  // Disconnect
  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    
    stopPingInterval();
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    
    setIsConnected(false);
  }, [stopPingInterval]);

  // Reconnect
  const reconnect = useCallback(() => {
    disconnect();
    shouldReconnectRef.current = true;
    reconnectCountRef.current = 0;
    connect();
  }, [disconnect, connect]);

  // Initialize connection on mount
  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();

    // Cleanup on unmount
    return () => {
      shouldReconnectRef.current = false;
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastMessage,
    send,
    disconnect,
    reconnect,
  };
}

/**
 * Hook for project-specific event stream
 */
export function useProjectEventStream(projectId: string, enabled: boolean = true) {
  const [events, setEvents] = useState<WebSocketEvent[]>([]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    const event: WebSocketEvent = {
      type: message.type as any,
      data: message.data,
    };
    setEvents((prev) => [event, ...prev].slice(0, 100)); // Keep last 100 events
  }, []);

  const ws = useWebSocket({
    projectId: enabled ? projectId : undefined,
    onMessage: handleMessage,
  });

  return {
    ...ws,
    events,
    clearEvents: () => setEvents([]),
  };
}

/**
 * Hook for agent-specific event stream
 */
export function useAgentEventStream(agentId: string, enabled: boolean = true) {
  const [events, setEvents] = useState<WebSocketEvent[]>([]);

  const handleMessage = useCallback((message: WebSocketMessage) => {
    const event: WebSocketEvent = {
      type: message.type as any,
      data: message.data,
    };
    setEvents((prev) => [event, ...prev].slice(0, 100));
  }, []);

  const ws = useWebSocket({
    agentId: enabled ? agentId : undefined,
    onMessage: handleMessage,
  });

  return {
    ...ws,
    events,
    clearEvents: () => setEvents([]),
  };
}

/**
 * Hook for global event stream (all projects and agents)
 */
export function useGlobalEventStream(enabled: boolean = true) {
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [agentActivities, setAgentActivities] = useState<Map<string, any>>(new Map());

  const handleMessage = useCallback((message: WebSocketMessage) => {
    const event: WebSocketEvent = {
      type: message.type as any,
      data: message.data,
    };
    setEvents((prev) => [event, ...prev].slice(0, 100));

    // Track agent activities for status updates
    if (message.type === 'activity_created' || message.type === 'activity_updated') {
      const agentId = message.data.agent_id;
      if (agentId) {
        setAgentActivities((prev) => {
          const newMap = new Map(prev);
          newMap.set(agentId, {
            ...message.data,
            timestamp: new Date(),
          });
          return newMap;
        });
      }
    }

    // Clean up completed activities
    if (message.type === 'activity_completed') {
      const agentId = message.data.agent_id;
      if (agentId) {
        setAgentActivities((prev) => {
          const newMap = new Map(prev);
          newMap.delete(agentId);
          return newMap;
        });
      }
    }
  }, []);

  const ws = useWebSocket({
    // No projectId or agentId = subscribe to all events
    onMessage: enabled ? handleMessage : undefined,
  });

  return {
    ...ws,
    events,
    agentActivities,
    clearEvents: () => setEvents([]),
  };
}
