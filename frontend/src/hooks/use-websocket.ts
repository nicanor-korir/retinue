/**
 * Custom React hook for WebSocket connections
 *
 * Handles:
 * - Connection management with automatic reconnection
 * - Message queuing while disconnected
 * - Event callbacks for open, close, error
 * - Automatic cleanup on unmount
 */

import { useEffect, useRef, useState, useCallback } from "react";

export interface WebSocketOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (event: Event) => void;
  onMessage?: (message: string | ArrayBuffer) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket(
  url: string,
  {
    onOpen,
    onClose,
    onError,
    onMessage,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  }: WebSocketOptions = {}
) {
  const [lastMessage, setLastMessage] = useState<string | ArrayBuffer | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const [url_ref, setUrl] = useState(url);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageQueueRef = useRef<string[]>([]);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (typeof window === "undefined") return; // SSR check

    try {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const fullUrl = url.startsWith("ws") ? url : `${protocol}//${window.location.host}${url}`;

      console.log(`[WebSocket] Connecting to ${fullUrl}`);
      const ws = new WebSocket(fullUrl);

      ws.onopen = () => {
        console.log(`[WebSocket] Connected to ${fullUrl}`);
        setReadyState(WebSocket.OPEN);
        reconnectCountRef.current = 0;

        // Send any queued messages
        while (messageQueueRef.current.length > 0) {
          const msg = messageQueueRef.current.shift();
          if (msg) ws.send(msg);
        }

        onOpen?.();
      };

      ws.onmessage = (event) => {
        setLastMessage(event.data);
        onMessage?.(event.data);
      };

      ws.onerror = (event) => {
        console.error("[WebSocket] Error:", event);
        setReadyState(WebSocket.CLOSED);
        onError?.(event);
      };

      ws.onclose = () => {
        console.log(`[WebSocket] Disconnected from ${fullUrl}`);
        setReadyState(WebSocket.CLOSED);
        onClose?.();

        // Attempt to reconnect
        if (reconnect && reconnectCountRef.current < maxReconnectAttempts) {
          reconnectCountRef.current += 1;
          console.log(
            `[WebSocket] Reconnecting in ${reconnectInterval}ms (attempt ${reconnectCountRef.current}/${maxReconnectAttempts})`
          );
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectInterval);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error("[WebSocket] Connection error:", error);
      setReadyState(WebSocket.CLOSED);
    }
  }, [url, onOpen, onClose, onError, onMessage, reconnect, reconnectInterval, maxReconnectAttempts]);

  // Initial connection
  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  // Reconnect when URL changes
  useEffect(() => {
    if (url !== url_ref) {
      setUrl(url);
      if (wsRef.current) {
        wsRef.current.close();
      }
      reconnectCountRef.current = 0;
      connect();
    }
  }, [url, connect]);

  // Send message
  const send = useCallback(
    (message: string) => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(message);
      } else {
        // Queue message if not connected
        messageQueueRef.current.push(message);
        console.warn("[WebSocket] Message queued - not connected");
      }
    },
    []
  );

  return {
    lastMessage,
    readyState,
    send,
    url: url_ref,
    isConnected: readyState === WebSocket.OPEN,
  };
}
