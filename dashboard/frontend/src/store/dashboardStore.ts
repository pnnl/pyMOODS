/**
 * Global Zustand store for dashboard + chat state.
 *
 * Install: yarn add zustand
 *
 * Two logical slices live here intentionally — they are tightly coupled
 * (the agent reads dashboardState and writes chatHistory in one operation)
 * and co-locating them avoids cross-store synchronisation boilerplate.
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type {
  AvailableMetadata,
  ChartType,
  ChatMessage,
  DashboardState,
  ProactiveBubble,
} from '../types/agent';

// ---------------------------------------------------------------------------
// Default / reset values -----------------------------------------------------
// ---------------------------------------------------------------------------

const DEFAULT_DASHBOARD: DashboardState = {
  activeChartType: 'scatter',
  activeFilters: {},
  highlightedVariables: [],
  availableMetadata: null,
  activeWeights: {},
  agentWeightOverrides: {},
  activeSolutionSample: [],
  activeTabIndex: 0,
  activeScenarioKeys: [],
  availableScenarioKeys: [],
  sidebarFilters: {},
  sidebarWeights: {},
};

// ---------------------------------------------------------------------------
// Store shape ----------------------------------------------------------------
// ---------------------------------------------------------------------------

export interface DashboardStore {
  // ── State ────────────────────────────────────────────────────────────────
  dashboardState: DashboardState;
  chatHistory: ChatMessage[];
  isGenerating: boolean;
  /** Floating insight bubble shown while the chat panel is closed. */
  proactiveBubble: ProactiveBubble | null;
  /** True while a background proactive fetch is in flight. */
  isProactiveGenerating: boolean;

  // ── Dashboard actions ─────────────────────────────────────────────────────

  /** Swap the active chart without touching filters or highlights. */
  setChartType: (chartType: ChartType) => void;

  /**
   * Add or overwrite a single filter dimension.
   * Pass an empty array to effectively clear that filter key.
   */
  setFilter: (key: string, values: string[]) => void;

  /** Remove an entire filter dimension from the active state. */
  removeFilter: (key: string) => void;

  /** Replace the full highlighted-variable list (agent HIGHLIGHT_VARIABLES). */
  setHighlightedVariables: (variables: string[]) => void;

  /** Populate schema metadata after a use case loads. Clears chat so the agent re-greets. */
  setAvailableMetadata: (metadata: AvailableMetadata) => void;

  /** Sync the active tab index so the agent knows which view is visible. */
  setActiveTabIndex: (index: number) => void;

  /** Update the active objective weights (called whenever weights change). */
  setActiveWeights: (weights: Record<string, number>) => void;

  /** Set a single weight override from the agent (key → value). */
  setAgentWeightOverride: (key: string, value: number) => void;

  /** Set selected aggregation-level keys in the TradeoffLatticePlot. */
  setActiveScenarioKeys: (keys: string[]) => void;

  /** Populate the full list of available aggregation keys (set by the plot on first load). */
  setAvailableScenarioKeys: (keys: string[]) => void;

  /** Store the top-N solution rows from the most recent fetch. */
  setActiveSolutionSample: (solutions: Record<string, unknown>[]) => void;

  /** Sync the sidebar filter selection so useProactiveInsights can detect changes. */
  setSidebarFilters: (filters: Record<string, string[]>) => void;

  /** Sync the sidebar objective weights so useProactiveInsights can detect changes. */
  setSidebarWeights: (weights: Record<string, number>) => void;

  /** Return dashboardState to defaults — does not clear chat. */
  resetDashboard: () => void;

  // ── Chat actions ──────────────────────────────────────────────────────────

  /** Push a single message onto the end of chatHistory. */
  appendMessage: (message: ChatMessage) => void;

  /**
   * Replace the last assistant message in-place.
   * Used to swap a "…thinking" placeholder with the real response.
   */
  updateLastAssistantMessage: (patch: Partial<ChatMessage>) => void;

  /** Toggle API loading indicator. */
  setIsGenerating: (value: boolean) => void;

  /** Wipe chatHistory (keeps dashboardState intact). */
  clearChat: () => void;

  // ── Proactive insight actions ─────────────────────────────────────────────

  /** Show or clear the floating insight bubble. */
  setProactiveBubble: (bubble: ProactiveBubble | null) => void;
  /** Toggle proactive-fetch loading indicator (distinct from user-chat isGenerating). */
  setIsProactiveGenerating: (value: boolean) => void;
}

// ---------------------------------------------------------------------------
// Store implementation -------------------------------------------------------
// ---------------------------------------------------------------------------

export const useDashboardStore = create<DashboardStore>()(
  devtools(
    (set) => ({
      // ── Initial state ──────────────────────────────────────────────────────
      dashboardState: { ...DEFAULT_DASHBOARD },
      chatHistory: [],
      isGenerating: false,
      proactiveBubble: null,
      isProactiveGenerating: false,

      // ── Dashboard actions ──────────────────────────────────────────────────
      setChartType: (chartType) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, activeChartType: chartType },
          }),
          false,
          'setChartType',
        ),

      setFilter: (key, values) =>
        set(
          (state) => ({
            dashboardState: {
              ...state.dashboardState,
              activeFilters: { ...state.dashboardState.activeFilters, [key]: values },
            },
          }),
          false,
          'setFilter',
        ),

      removeFilter: (key) =>
        set(
          (state) => {
            const { [key]: _removed, ...rest } = state.dashboardState.activeFilters;
            return { dashboardState: { ...state.dashboardState, activeFilters: rest } };
          },
          false,
          'removeFilter',
        ),

      setHighlightedVariables: (variables) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, highlightedVariables: variables },
          }),
          false,
          'setHighlightedVariables',
        ),

      setAvailableMetadata: (metadata) =>
        set(
          (state) => {
            const useCaseChanged =
              state.dashboardState.availableMetadata?.useCaseName !== metadata.useCaseName;
            return {
              dashboardState: { ...state.dashboardState, availableMetadata: metadata },
              // Only clear chat when the user switches to a different use case.
              // Filter/weight refreshes call this too — those must not wipe history.
              chatHistory: useCaseChanged ? [] : state.chatHistory,
            };
          },
          false,
          'setAvailableMetadata',
        ),

      setActiveTabIndex: (index) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, activeTabIndex: index },
          }),
          false,
          'setActiveTabIndex',
        ),

      setActiveWeights: (weights) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, activeWeights: weights },
          }),
          false,
          'setActiveWeights',
        ),

      setActiveScenarioKeys: (keys) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, activeScenarioKeys: keys },
          }),
          false,
          'setActiveScenarioKeys',
        ),

      setAvailableScenarioKeys: (keys) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, availableScenarioKeys: keys },
          }),
          false,
          'setAvailableScenarioKeys',
        ),

      setAgentWeightOverride: (key, value) =>
        set(
          (state) => ({
            dashboardState: {
              ...state.dashboardState,
              agentWeightOverrides: {
                ...state.dashboardState.agentWeightOverrides,
                [key]: value,
              },
            },
          }),
          false,
          'setAgentWeightOverride',
        ),

      setActiveSolutionSample: (solutions) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, activeSolutionSample: solutions },
          }),
          false,
          'setActiveSolutionSample',
        ),

      setSidebarFilters: (filters) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, sidebarFilters: filters },
          }),
          false,
          'setSidebarFilters',
        ),

      setSidebarWeights: (weights) =>
        set(
          (state) => ({
            dashboardState: { ...state.dashboardState, sidebarWeights: weights },
          }),
          false,
          'setSidebarWeights',
        ),

      resetDashboard: () =>
        set(
          (state) => ({ dashboardState: { ...DEFAULT_DASHBOARD, activeWeights: state.dashboardState.activeWeights } }),
          false,
          'resetDashboard',
        ),

      // ── Chat actions ───────────────────────────────────────────────────────
      appendMessage: (message) =>
        set(
          (state) => ({ chatHistory: [...state.chatHistory, message] }),
          false,
          'appendMessage',
        ),

      updateLastAssistantMessage: (patch) =>
        set(
          (state) => {
            const idx = [...state.chatHistory]
              .reverse()
              .findIndex((m) => m.role === 'assistant');
            if (idx === -1) return state;

            const realIdx = state.chatHistory.length - 1 - idx;
            const updated = [...state.chatHistory];
            updated[realIdx] = { ...updated[realIdx], ...patch };
            return { chatHistory: updated };
          },
          false,
          'updateLastAssistantMessage',
        ),

      setIsGenerating: (value) => set({ isGenerating: value }, false, 'setIsGenerating'),

      clearChat: () => set({ chatHistory: [] }, false, 'clearChat'),

      // ── Proactive insight actions ──────────────────────────────────────────
      setProactiveBubble: (bubble) =>
        set({ proactiveBubble: bubble }, false, 'setProactiveBubble'),

      setIsProactiveGenerating: (value) =>
        set({ isProactiveGenerating: value }, false, 'setIsProactiveGenerating'),
    }),
    { name: 'PyMOODS-Dashboard' }, // label shown in Redux DevTools
  ),
);
