/**
 * useAgentChat
 *
 * Handles the full send → receive → dispatch cycle for the AI chat panel.
 *
 * Responsibilities:
 *  1. Append the user message to chatHistory immediately (optimistic update).
 *  2. Capture the *current* dashboardState before any async gap.
 *  3. POST to /api/chat with the message + dashboard context.
 *  4. Parse and validate the response.
 *  5. Append the assistant reply and dispatch any visualization command.
 *  6. Manage isGenerating and surface error states without crashing.
 */

import { useCallback } from 'react';
import config from '../config';
import { useDashboardStore } from '../store/dashboardStore';
import { executeAgentCommand } from '../utils/commandDispatcher';
import type {
  AgentApiRequest,
  AgentApiResponse,
  ChatMessage,
} from '../types/agent';

// ---------------------------------------------------------------------------
// Hook -----------------------------------------------------------------------
// ---------------------------------------------------------------------------

export interface UseAgentChatReturn {
  chatHistory: ChatMessage[];
  isGenerating: boolean;
  /** Submit a new user message. Safe to call while isGenerating is true — it no-ops. */
  submitMessage: (text: string) => Promise<void>;
  /**
   * Fire once when the chat panel opens (or a new use case loads).
   * Fetches a use-case summary from the agent with no visible user message.
   * No-ops if chat already has messages or metadata isn't loaded yet.
   */
  initChat: () => Promise<void>;
  clearChat: () => void;
}

export function useAgentChat(): UseAgentChatReturn {
  const {
    chatHistory,
    isGenerating,
    dashboardState,
    appendMessage,
    updateLastAssistantMessage,
    setIsGenerating,
    clearChat,
  } = useDashboardStore();

  const submitMessage = useCallback(
    async (text: string): Promise<void> => {
      // Debounce: ignore double-submits while a request is in flight.
      if (isGenerating) return;

      const trimmed = text.trim();
      if (!trimmed) return;

      // ── 1. Optimistic user message ─────────────────────────────────────────
      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        text: trimmed,
        timestamp: Date.now(),
      };
      appendMessage(userMessage);

      // ── 2. Placeholder while waiting ──────────────────────────────────────
      const placeholderId = crypto.randomUUID();
      appendMessage({
        id: placeholderId,
        role: 'assistant',
        text: '…',
        timestamp: Date.now(),
      });

      setIsGenerating(true);

      // Snapshot dashboard context *before* the await so any concurrent
      // user interaction during fetch doesn't pollute the request body.
      const contextSnapshot = { ...dashboardState };

      try {
        // ── 3. POST to /api/chat ─────────────────────────────────────────────
        const requestBody: AgentApiRequest = {
          message: trimmed,
          dashboard_context: contextSnapshot,
        };

        const response = await fetch(`${config.API_BASE_URL}/api/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        // ── 4. Parse response ────────────────────────────────────────────────
        const data: unknown = await response.json();

        if (!isAgentApiResponse(data)) {
          throw new Error('Malformed response: missing response_text field.');
        }

        // ── 5a. Replace placeholder with real assistant message ───────────────
        updateLastAssistantMessage({
          id: placeholderId,
          text: data.response_text,
          timestamp: Date.now(),
          command: data.visualization_command,
          suggestedQuestions: data.suggested_questions,
        });

        // ── 5b. Dispatch visualization command ────────────────────────────────
        const storeSnapshot = useDashboardStore.getState();
        const result = executeAgentCommand(data.visualization_command ?? null, storeSnapshot);

        if (result.status !== 'ok' && result.status !== 'skipped') {
          // Log non-fatal command errors to the console for debugging.
          console.warn('[AgentChat] Command dispatcher warning:', result.message);
        }
      } catch (err) {
        const errorText =
          err instanceof Error ? err.message : 'An unknown error occurred. Please try again.';

        // Replace placeholder with an error message so the user gets feedback.
        updateLastAssistantMessage({
          id: placeholderId,
          role: 'error',
          text: `Could not reach the AI agent: ${errorText}`,
          timestamp: Date.now(),
        });
      } finally {
        setIsGenerating(false);
      }
    },
    [
      isGenerating,
      dashboardState,
      appendMessage,
      updateLastAssistantMessage,
      setIsGenerating,
    ],
  );

  const initChat = useCallback(async (): Promise<void> => {
    // Read fresh state to avoid stale closures and race with proactive fetch.
    const { chatHistory: current, dashboardState: snap, isGenerating: gen, isProactiveGenerating } =
      useDashboardStore.getState();
    if (gen || isProactiveGenerating) return;
    if (current.length > 0 || !snap.availableMetadata) return;


    const placeholderId = crypto.randomUUID();
    appendMessage({ id: placeholderId, role: 'assistant', text: '…', timestamp: Date.now() });
    setIsGenerating(true);

    try {
      const response = await fetch(`${config.API_BASE_URL}/api/chat/init`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ dashboard_context: snap }),
      });
      if (!response.ok) throw new Error(`${response.status}: ${response.statusText}`);
      const data: unknown = await response.json();
      if (!isAgentApiResponse(data)) throw new Error('Malformed init response.');
      updateLastAssistantMessage({
        text: data.response_text,
        timestamp: Date.now(),
        suggestedQuestions: data.suggested_questions,
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Could not load use case summary.';
      updateLastAssistantMessage({ role: 'error', text: msg, timestamp: Date.now() });
    } finally {
      setIsGenerating(false);
    }
  }, [appendMessage, updateLastAssistantMessage, setIsGenerating]);

  return { chatHistory, isGenerating, submitMessage, initChat, clearChat };
}

// ---------------------------------------------------------------------------
// Type guard for API response ------------------------------------------------
// ---------------------------------------------------------------------------

function isAgentApiResponse(data: unknown): data is AgentApiResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'response_text' in data &&
    typeof (data as Record<string, unknown>)['response_text'] === 'string'
  );
}
