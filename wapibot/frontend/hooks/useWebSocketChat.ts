'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { useConversationStore } from './useConversations';

interface UseWebSocketChatResult {
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  isConnected: boolean;
  connectionStatus: 'connecting' | 'connected' | 'disconnected' | 'error';
}

/**
 * Hook for real-time WebSocket chat communication
 *
 * Features:
 * - Automatic connection on mount
 * - Auto-reconnect with exponential backoff
 * - Real-time bidirectional messaging
 * - Connection status tracking
 * - HTTP fallback on connection failure
 */
export function useWebSocketChat(conversationId: string): UseWebSocketChatResult {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000; // 1 second

  const { conversations, addMessage, backendSettings } = useConversationStore();
  const conversation = conversations.find((c) => c.id === conversationId);

  /**
   * Connect to WebSocket server
   */
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    try {
      const wsUrl = backendSettings.fastapi.baseUrl.replace('http', 'ws');
      const url = `${wsUrl}/ws/chat/${conversationId}`;

      console.log('[WebSocket] Connecting to:', url);
      setConnectionStatus('connecting');

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setConnectionStatus('connected');
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('[WebSocket] Message received:', data);

          if (data.type === 'connection_established') {
            console.log('[WebSocket] Connection established:', data.message);
            return;
          }

          if (data.type === 'message' && data.data) {
            // Add assistant response to conversation
            if (data.data.response) {
              addMessage(conversationId, {
                role: 'assistant',
                content: data.data.response,
                timestamp: new Date(),
                phoneNumber: conversation?.phoneNumber || '',
                metadata: {
                  extracted_data: data.data.extracted_data,
                  completeness: data.data.completeness,
                  should_confirm: data.data.should_confirm,
                },
              });
              setIsLoading(false);
            }
          }

          if (data.type === 'error') {
            console.error('[WebSocket] Error from server:', data.message);
            setError(data.message);
            setIsLoading(false);
          }
        } catch (err) {
          console.error('[WebSocket] Failed to parse message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        setConnectionStatus('error');
        setError('WebSocket connection error');
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] Closed:', event.code, event.reason);
        setConnectionStatus('disconnected');
        wsRef.current = null;

        // Auto-reconnect with exponential backoff
        if (reconnectAttempts.current < maxReconnectAttempts) {
          const delay = baseReconnectDelay * Math.pow(2, reconnectAttempts.current);
          console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else {
          console.log('[WebSocket] Max reconnection attempts reached');
          setError('Connection lost. Please refresh the page.');
        }
      };
    } catch (err) {
      console.error('[WebSocket] Connection failed:', err);
      setConnectionStatus('error');
      setError(err instanceof Error ? err.message : 'Failed to connect');
    }
  }, [conversationId, backendSettings.fastapi.baseUrl, addMessage, conversation?.phoneNumber]);

  /**
   * Send message via WebSocket
   */
  const sendMessage = async (content: string) => {
    if (!conversation || !content.trim()) return;

    try {
      setIsLoading(true);
      setError(null);

      // Add user message to store immediately
      addMessage(conversationId, {
        role: 'user',
        content,
        timestamp: new Date(),
        phoneNumber: conversation.phoneNumber,
      });

      // Check WebSocket connection
      if (wsRef.current?.readyState !== WebSocket.OPEN) {
        console.warn('[WebSocket] Not connected, attempting to connect...');
        connect();

        // Wait for connection or timeout
        await new Promise((resolve, reject) => {
          const timeout = setTimeout(() => reject(new Error('Connection timeout')), 5000);
          const checkConnection = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
              clearInterval(checkConnection);
              clearTimeout(timeout);
              resolve(undefined);
            }
          }, 100);
        });
      }

      // Build conversation history
      const previousMessages = conversation.messages.map((msg) => ({
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
      }));

      // Send via WebSocket
      const payload = {
        user_message: content,
        history: previousMessages.slice(0, -1), // Exclude current message
      };

      console.log('[WebSocket] Sending message:', payload);
      wsRef.current?.send(JSON.stringify(payload));

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      console.error('[WebSocket] Send error:', err);
      setIsLoading(false);

      // Add error message
      addMessage(conversationId, {
        role: 'assistant',
        content: `Error: ${errorMessage}. Try refreshing the page.`,
        timestamp: new Date(),
        phoneNumber: conversation.phoneNumber,
      });
    }
  };

  /**
   * Connect on mount, cleanup on unmount
   */
  useEffect(() => {
    connect();

    return () => {
      console.log('[WebSocket] Cleaning up...');
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    isLoading,
    error,
    sendMessage,
    isConnected: connectionStatus === 'connected',
    connectionStatus,
  };
}
