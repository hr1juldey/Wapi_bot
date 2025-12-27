'use client';

import React, { useEffect, useState, useRef } from 'react';
import { useConversationStore } from '@/hooks/useConversations';
import Button from '@/components/ui/Button';
import SettingsPanel from '@/components/settings/SettingsPanel';
import { Settings, Send } from 'lucide-react';
import { selectBestAvailableModel } from '@/lib/utils';
import { OLLAMA_PREFERRED_MODEL } from '@/lib/constants';
import { useToast } from '@/hooks/useToast';

export default function Header() {
  const {
    backendMode,
    setBackendMode,
    selectedOllamaModel,
    setSelectedOllamaModel,
    availableOllamaModels,
    backendSettings,
    updateBackendSettings,
    conversations,
    activeConversationId,
  } = useConversationStore();

  const [isLoading, setIsLoading] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [noModelsAvailable, setNoModelsAvailable] = useState(false);

  const { toast } = useToast();
  const previousModelRef = useRef<string | null>(selectedOllamaModel);

  // Fetch Ollama models on mount
  useEffect(() => {
    const fetchModels = async () => {
      if (backendMode !== 'ollama') return;

      try {
        setIsLoading(true);
        setNoModelsAvailable(false);
        const response = await fetch('/api/ollama/models');

        if (!response.ok) {
          throw new Error(`Failed to fetch models: ${response.statusText}`);
        }

        const data = await response.json();
        const modelNames = (data.models || []).map((m: any) => m.name);

        console.log('[Model Selection] Available models:', modelNames);

        // Update available models in store
        useConversationStore.setState({
          availableOllamaModels: modelNames,
        });

        // Get current selected model
        const currentSelection = selectedOllamaModel;

        // Check if current selection is still valid
        const isCurrentSelectionValid = currentSelection && modelNames.includes(currentSelection);

        // Only update if current selection is invalid or null
        if (!isCurrentSelectionValid) {
          // Select best available model
          const bestModel = selectBestAvailableModel(
            modelNames,
            currentSelection,
            OLLAMA_PREFERRED_MODEL
          );

          if (bestModel) {
            // Update both UI state and backend settings
            console.log('[Model Selection] Updating to:', bestModel);
            setSelectedOllamaModel(bestModel);
            updateBackendSettings({
              ollama: {
                ...backendSettings.ollama,
                model: bestModel,
              },
            });
            setNoModelsAvailable(false);
          } else {
            // No models available - show error to user
            console.warn('No Ollama models found. Please install at least one model.');
            setNoModelsAvailable(true);
          }
        } else {
          // Current selection is valid, keep it
          console.log('[Model Selection] Keeping current selection:', currentSelection);
          setNoModelsAvailable(false);
        }

      } catch (error) {
        console.error('Failed to fetch Ollama models:', error);
        // Fallback: keep current selection or use preference
        if (!selectedOllamaModel) {
          setSelectedOllamaModel(OLLAMA_PREFERRED_MODEL);
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchModels();
  }, [backendMode]);

  // Detect model changes and show toast notification
  useEffect(() => {
    const previousModel = previousModelRef.current;
    const currentModel = selectedOllamaModel;

    // Skip if this is the first render (initialization)
    if (previousModel === null && currentModel !== null) {
      previousModelRef.current = currentModel;
      return;
    }

    // Skip if model hasn't changed
    if (previousModel === currentModel) {
      return;
    }

    // Skip if no model selected
    if (!currentModel || !previousModel) {
      previousModelRef.current = currentModel;
      return;
    }

    // Check if there's an active conversation with messages
    const activeConversation = conversations.find(
      (c) => c.id === activeConversationId
    );

    if (activeConversation && activeConversation.messages.length > 0) {
      // Show toast notification about model switch
      toast.info(
        `Switched to ${currentModel}. Previous messages were from ${previousModel}.`,
        5000 // Show for 5 seconds
      );
      console.log(
        `[Model Switch] ${previousModel} → ${currentModel} (${activeConversation.messages.length} messages in conversation)`
      );
    }

    // Update the ref for next change
    previousModelRef.current = currentModel;
  }, [selectedOllamaModel, conversations, activeConversationId, toast]);

  return (
    <header className="border-b border-white/10 bg-zinc-900/80 backdrop-blur-xl shadow-lg">
      <div className="flex items-center justify-between px-6 py-4">
        {/* Left: Branding */}
        <div className="flex-shrink-0">
          <h1 className="text-2xl font-bold text-white tracking-tight">WapiBot</h1>
          <p className="text-xs text-gray-500 mt-0.5">WhatsApp Testing Interface</p>
        </div>

        {/* Center: Mode Switcher & Model Selector */}
        <div className="flex items-center gap-3">
          {/* Backend Mode */}
          <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-4 py-2 hover:bg-white/10 transition-all">
            <label className="text-sm font-medium text-gray-400">Backend:</label>
            <select
              value={backendMode}
              onChange={(e) =>
                setBackendMode(e.target.value as 'ollama' | 'fastapi' | 'websocket')
              }
              className="bg-transparent text-white font-medium outline-none text-sm cursor-pointer"
            >
              <option value="ollama" className="bg-zinc-800">Ollama</option>
              <option value="fastapi" className="bg-zinc-800">FastAPI (HTTP)</option>
              <option value="websocket" className="bg-zinc-800">WebSocket (Real-time)</option>
            </select>
          </div>

          {/* No Models Error (only for Ollama) */}
          {backendMode === 'ollama' && noModelsAvailable && (
            <div className="flex items-center gap-2 bg-red-500/10 border border-red-500/30 rounded-lg px-4 py-2">
              <span className="text-xs text-red-400">
                No Ollama models found. Run: <code className="bg-red-900/30 px-1.5 py-0.5 rounded font-mono">ollama pull {OLLAMA_PREFERRED_MODEL}</code>
              </span>
            </div>
          )}

          {/* Model Selector (only for Ollama) */}
          {backendMode === 'ollama' && availableOllamaModels.length > 0 && (
            <div className="flex items-center gap-2 bg-white/5 border border-white/10 rounded-lg px-4 py-2 hover:bg-white/10 transition-all">
              <label className="text-sm font-medium text-gray-400">Model:</label>
              <select
                value={selectedOllamaModel || ''}
                onChange={(e) => setSelectedOllamaModel(e.target.value)}
                className="bg-transparent text-white font-medium outline-none text-sm cursor-pointer max-w-xs"
                disabled={isLoading}
              >
                {availableOllamaModels.map((model) => (
                  <option key={model} value={model} className="bg-zinc-800">
                    {model}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Right: Settings */}
        <div className="flex-shrink-0">
          <Button
            variant="secondary"
            size="icon"
            title="Settings"
            onClick={() => setShowSettings(true)}
            className="hover:bg-white/10"
          >
            <Settings className="w-5 h-5" />
          </Button>
        </div>
      </div>

      {/* Settings Panel Modal (renders via portal to body) */}
      <SettingsPanel isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </header>
  );
}
