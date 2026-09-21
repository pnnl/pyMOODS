/**
 * Shared types for the AI agent chat + dashboard command system.
 * Import from here to avoid circular dependencies between store / utils / hooks.
 */

// ---------------------------------------------------------------------------
// Chart types ----------------------------------------------------------------
// ---------------------------------------------------------------------------

/** All chart modes the dashboard can render. Extend as new plots are added. */
export type ChartType =
  | 'scatter'
  | 'objective'
  | 'decision'
  | 'parallel_coordinates'
  | 'radar'
  | 'bee_swarm'
  | 'shap_waterfall'
  | 'tradeoff_lattice';

// ---------------------------------------------------------------------------
// Available metadata (populated after a use case loads) ----------------------
// ---------------------------------------------------------------------------

/**
 * Schema-level facts about the loaded use case.
 * Sent with every request so the agent understands what dimensions exist
 * without the user having to know column names.
 */
export interface AvailableMetadata {
  useCaseName: string;
  objectiveKeys: string[];
  decisionKeys: string[];
  hyperparameterKeys: string[];
  inputParameterKeys: string[];
  objectiveUnits: Record<string, string>;
  /** All possible filter values — key → candidate values. */
  availableFilterValues: Record<string, string[]>;
}

// ---------------------------------------------------------------------------
// Dashboard state ------------------------------------------------------------
// ---------------------------------------------------------------------------

export interface DashboardState {
  /** Currently rendered chart type. */
  activeChartType: ChartType;
  /** Key → allowed values map, mirrors the filter shape used by existing API calls. */
  activeFilters: Record<string, string[]>;
  /** Variable names to highlight / emphasise in the active chart. */
  highlightedVariables: string[];
  /** Null until a use case is loaded. Sent to the agent so it knows the data schema. */
  availableMetadata: AvailableMetadata | null;
  /** Current objective weights. Populated after each solutions fetch. */
  activeWeights: Record<string, number>;
  /** Weight overrides issued by the agent (key → value). Merged on top of sidebar weights. */
  agentWeightOverrides: Record<string, number>;
  /** Top-5 solutions from the most recent fetch for agent context. */
  activeSolutionSample: Record<string, unknown>[];
  /** Which tab is currently visible (0 = Decision Making, 1 = Scenario Comparison). */
  activeTabIndex: number;
  /** Aggregation-level keys selected in the TradeoffLatticePlot checkboxes. */
  activeScenarioKeys: string[];
  /** All available scenario/aggregation keys for the loaded use case. */
  availableScenarioKeys: string[];
  /**
   * Mirror of the sidebar filter selection — kept in the store solely so
   * useProactiveInsights can detect user-initiated filter changes, which
   * live outside the store in App.tsx local state.
   */
  sidebarFilters: Record<string, string[]>;
  /**
   * Mirror of the sidebar objective weights — kept in the store solely so
   * useProactiveInsights can detect user-initiated weight changes.
   */
  sidebarWeights: Record<string, number>;
}

// ---------------------------------------------------------------------------
// Agent commands -------------------------------------------------------------
// ---------------------------------------------------------------------------

/** All action verbs the AI may issue.  Add new ones here and handle in commandDispatcher. */
export type AgentAction =
  | 'CHANGE_CHART_TYPE'
  | 'UPDATE_FILTER'
  | 'REMOVE_FILTER'
  | 'HIGHLIGHT_VARIABLES'
  | 'UPDATE_WEIGHT'
  | 'SET_AGGREGATION_LEVEL'
  | 'RESET';

export interface VisualizationCommand {
  action: AgentAction;
  /** Variable or filter key the command applies to (may be absent for RESET). */
  target_variable?: string;
  /** Action-specific payload — validated at runtime in commandDispatcher. */
  parameters: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Chat messages --------------------------------------------------------------
// ---------------------------------------------------------------------------

export interface ChatMessage {
  /** Stable UUID created on insertion so React lists never need index keys. */
  id: string;
  role: 'user' | 'assistant' | 'error';
  text: string;
  timestamp: number;
  /** Optional command that accompanied this assistant message. */
  command?: VisualizationCommand;
  /** Clickable follow-up questions suggested by the agent. */
  suggestedQuestions?: string[];
  /** True when this message was generated proactively (not in response to a user message). */
  isProactive?: boolean;
}

/** The floating insight bubble shown while the chat panel is closed. */
export interface ProactiveBubble {
  id: string;
  text: string;
  timestamp: number;
}

// ---------------------------------------------------------------------------
// API request / response shapes ----------------------------------------------
// ---------------------------------------------------------------------------

export interface AgentApiRequest {
  message: string;
  /** Snapshot of dashboard state at the moment the user pressed send. */
  dashboard_context: DashboardState;
}

export interface AgentApiResponse {
  response_text: string;
  /** Absent when the agent only returns prose (no chart change needed). */
  visualization_command?: VisualizationCommand;
  /** 2-3 contextual follow-up questions the user can click to continue exploring. */
  suggested_questions?: string[];
}

// ---------------------------------------------------------------------------
// Command dispatcher result --------------------------------------------------
// ---------------------------------------------------------------------------

export type CommandStatus = 'ok' | 'unknown_action' | 'invalid_parameters' | 'skipped';

export interface CommandResult {
  status: CommandStatus;
  /** Human-readable explanation — useful for dev-mode toast / console. */
  message: string;
}
