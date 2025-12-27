/**
 * Core type definitions for WapiBot frontend
 */

export type BackendMode = 'ollama' | 'fastapi' | 'websocket';

export type MessageRole = 'user' | 'assistant' | 'system';

/**
 * Individual message in a conversation
 */
export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  phoneNumber: string; // Which contact sent this
  metadata?: MessageMetadata;
}

/**
 * Additional message metadata for interactive elements
 */
export interface MessageMetadata {
  buttons?: Button[];
  mediaUrl?: string;
  mediaType?: 'image' | 'document';
  error?: string;
}

/**
 * WhatsApp-style interactive button
 */
export interface Button {
  id: string;
  label: string;
  action?: string;
}

/**
 * Single conversation/contact
 */
export interface Conversation {
  id: string; // UUID
  phoneNumber: string; // Unique contact identifier
  displayName: string; // Display name for sidebar
  messages: Message[];
  createdAt: Date;
  lastMessageAt: Date;
  unreadCount: number;
}

/**
 * Ollama model information
 */
export interface OllamaModel {
  name: string;
  id: string;
  size: string;
  modified: string;
}

/**
 * Response from FastAPI backend
 */
export interface FastAPIResponse {
  message: string;
  buttons?: Button[];
  mediaUrl?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Chat message request to backend
 */
export interface ChatRequest {
  phoneNumber: string;
  messageBody: string;
  conversationId?: string;
}

/**
 * Backend configuration settings
 */
export interface BackendSettings {
  ollama: {
    baseUrl: string;
    model: string | null; // Allow null during initialization
    timeout: number;
    maxTokens: number;
    temperature: number;
  };
  fastapi: {
    baseUrl: string;
    endpoint: string;
    timeout: number;
    retries: number;
  };
}

/**
 * Global app state (managed by Zustand)
 */
export interface AppState {
  conversations: Conversation[];
  activeConversationId: string | null;
  backendMode: BackendMode;
  selectedOllamaModel: string | null; // Allow null during initialization
  availableOllamaModels: string[];
  backendSettings: BackendSettings;
}
