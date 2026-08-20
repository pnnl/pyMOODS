/**
 * useProactiveInsights
 *
 * Watches key dashboard-state changes and fires a background AI analysis after
 * each one (debounced). The response is appended to chatHistory and displayed
 * in the ProactiveInsightBubble — without requiring the user to open the chat.
 *
 * Trigger priority (first match wins when multiple fields change at once):
 *   1. Use-case load        → immediate (100 ms)
 *   2. Filter change        → 1 500 ms
 *   3. Chart type change    → 800 ms
 *   4. Tab change           → 500 ms
 *
 * Intentionally NOT triggered by: activeWeights (changes on every fetch),
 * agentWeightOverrides (agent-initiated), activeSolutionSample, or
 * highlightedVariables (cosmetic).
 */

import { useEffect, useRef, useCallback } from 'react';
import config from '../config';
import { useDashboardStore } from '../store/dashboardStore';
import type { ChatMessage, DashboardState, ProactiveBubble } from '../types/agent';

const BUBBLE_DURATION_MS = 8_000;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function detectTrigger(
  prev: DashboardState,
  next: DashboardState,
): { trigger: string; delay: number } | null {
  if (!next.availableMetadata) return null;

  // 1. Use-case load (or switch)
  if (prev.availableMetadata?.useCaseName !== next.availableMetadata.useCaseName) {
    return { trigger: `Use case "${next.availableMetadata.useCaseName}" loaded`, delay: 100 };
  }

  // 2. Sidebar filter change (user-applied via the left panel)
  if (JSON.stringify(prev.sidebarFilters) !== JSON.stringify(next.sidebarFilters)) {
    const details = Object.keys({ ...prev.sidebarFilters, ...next.sidebarFilters })
      .filter((k) => JSON.stringify(prev.sidebarFilters[k]) !== JSON.stringify(next.sidebarFilters[k]))
      .map((k) => {
        const vals = next.sidebarFilters[k];
        return vals && vals.length > 0 ? `${k} → [${vals.join(', ')}]` : `${k} cleared`;
      })
      .join('; ');
    return { trigger: `Filter changed: ${details}`, delay: 1_500 };
  }

  // 3. Agent-applied filter change (from command dispatcher)
  if (JSON.stringify(prev.activeFilters) !== JSON.stringify(next.activeFilters)) {
    const details = Object.keys({ ...prev.activeFilters, ...next.activeFilters })
      .filter((k) => JSON.stringify(prev.activeFilters[k]) !== JSON.stringify(next.activeFilters[k]))
      .map((k) => {
        const vals = next.activeFilters[k];
        return vals && vals.length > 0 ? `${k} → [${vals.join(', ')}]` : `${k} cleared`;
      })
      .join('; ');
    return { trigger: `Filter changed: ${details}`, delay: 1_500 };
  }

  // 4. Sidebar weight change (user-adjusted via the left panel)
  if (JSON.stringify(prev.sidebarWeights) !== JSON.stringify(next.sidebarWeights)) {
    const details = Object.keys({ ...prev.sidebarWeights, ...next.sidebarWeights })
      .filter((k) => prev.sidebarWeights[k] !== next.sidebarWeights[k])
      .map((k) => `${k}: ${prev.sidebarWeights[k] ?? '—'} → ${next.sidebarWeights[k]}`)
      .join('; ');
    return { trigger: `Objective weight changed: ${details}`, delay: 2_000 };
  }

  // 5. Chart type change
  if (prev.activeChartType !== next.activeChartType) {
    return { trigger: `Chart type changed to ${next.activeChartType}`, delay: 800 };
  }

  // 6. Tab change
  if (prev.activeTabIndex !== next.activeTabIndex) {
    const names: Record<number, string> = { 0: 'Decision Making', 1: 'Scenario Comparison', 2: 'Cameo' };
    return {
      trigger: `Switched to ${names[next.activeTabIndex] ?? `tab ${next.activeTabIndex}`}`,
      delay: 500,
    };
  }

  return null;
}

function isProactiveResponse(data: unknown): data is { response_text: string; suggested_questions?: string[] } {
  return (
    typeof data === 'object' &&
    data !== null &&
    'response_text' in data &&
    typeof (data as Record<string, unknown>)['response_text'] === 'string'
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useProactiveInsights(): void {
  const {
    dashboardState,
    appendMessage,
    setProactiveBubble,
    setIsProactiveGenerating,
  } = useDashboardStore();

  const prevStateRef  = useRef<DashboardState | null>(null);
  const debounceRef   = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef      = useRef<AbortController | null>(null);
  const dismissRef    = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchInsight = useCallback(
    async (trigger: string, context: DashboardState): Promise<void> => {
      // Cancel any in-flight request and its dismiss timer.
      abortRef.current?.abort();
      if (dismissRef.current) clearTimeout(dismissRef.current);

      const controller = new AbortController();
      abortRef.current = controller;

      setIsProactiveGenerating(true);

      try {
        const response = await fetch(`${config.API_BASE_URL}/api/chat/proactive`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ trigger, dashboard_context: context }),
          signal: controller.signal,
        });

        if (!response.ok) return;

        const data: unknown = await response.json();
        if (!isProactiveResponse(data) || !data.response_text) return;

        // Append to chat history (persists even if bubble is dismissed).
        const msg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          text: data.response_text,
          timestamp: Date.now(),
          suggestedQuestions: data.suggested_questions,
          isProactive: true,
        };
        appendMessage(msg);

        // Show the bubble.
        const bubble: ProactiveBubble = { id: msg.id, text: data.response_text, timestamp: Date.now() };
        setProactiveBubble(bubble);

        // Auto-dismiss after BUBBLE_DURATION_MS.
        dismissRef.current = setTimeout(() => setProactiveBubble(null), BUBBLE_DURATION_MS);

      } catch (err) {
        if ((err as Error).name !== 'AbortError') {
          console.warn('[ProactiveInsights]', err);
        }
      } finally {
        setIsProactiveGenerating(false);
      }
    },
    [appendMessage, setProactiveBubble, setIsProactiveGenerating],
  );

  useEffect(() => {
    const prev = prevStateRef.current;
    prevStateRef.current = dashboardState;

    // Skip the initial mount render — there is no "previous" state yet.
    if (!prev) return;

    const match = detectTrigger(prev, dashboardState);
    if (!match) return;

    // Debounce: cancel any pending trigger and schedule a new one.
    if (debounceRef.current) clearTimeout(debounceRef.current);
    const { trigger, delay } = match;
    const snapshot = { ...dashboardState };
    debounceRef.current = setTimeout(() => {
      void fetchInsight(trigger, snapshot);
    }, delay);
  }, [dashboardState, fetchInsight]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      debounceRef.current && clearTimeout(debounceRef.current);
      dismissRef.current  && clearTimeout(dismissRef.current);
      abortRef.current?.abort();
    };
  }, []);
}
