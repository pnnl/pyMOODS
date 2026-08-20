/**
 * executeAgentCommand
 *
 * The single entry-point for all AI-issued visualization mutations.
 * It validates each command before touching the store, so a hallucinated
 * or malformed command degrades gracefully instead of crashing the app.
 *
 * Usage:
 *   const result = executeAgentCommand(command, store);
 *   if (result.status !== 'ok') console.warn(result.message);
 */

import type { DashboardStore } from '../store/dashboardStore';
import type {
  AgentAction,
  ChartType,
  CommandResult,
  VisualizationCommand,
} from '../types/agent';

// ---------------------------------------------------------------------------
// Key resolution -------------------------------------------------------------
// ---------------------------------------------------------------------------

/**
 * Resolve an agent-provided filter key to the actual hyperparameter key.
 * The model sometimes abbreviates keys (e.g. "parameter" instead of
 * "Parameter Set"). We try an exact match first, then a normalised
 * (lowercase, no spaces/underscores) fallback against known keys.
 */
function resolveFilterKey(candidate: string, store: DashboardStore): string {
  const knownKeys = store.dashboardState.availableMetadata?.hyperparameterKeys ?? [];
  if (knownKeys.length === 0) return candidate;

  // Exact match
  if (knownKeys.includes(candidate)) return candidate;

  // Normalise: lowercase + strip spaces and underscores
  const norm = (s: string) => s.toLowerCase().replace(/[\s_-]+/g, '');
  const normCandidate = norm(candidate);
  const matched = knownKeys.find((k) => norm(k) === normCandidate);
  return matched ?? candidate;
}

// ---------------------------------------------------------------------------
// Constants ------------------------------------------------------------------
// ---------------------------------------------------------------------------

/** Keep in sync with the ChartType union in types/agent.ts */
const VALID_CHART_TYPES = new Set<ChartType>([
  'scatter',
  'objective',
  'decision',
  'parallel_coordinates',
  'radar',
  'bee_swarm',
  'shap_waterfall',
  'tradeoff_lattice',
]);

const VALID_ACTIONS = new Set<AgentAction>([
  'CHANGE_CHART_TYPE',
  'UPDATE_FILTER',
  'REMOVE_FILTER',
  'HIGHLIGHT_VARIABLES',
  'UPDATE_WEIGHT',
  'SET_AGGREGATION_LEVEL',
  'RESET',
]);

// ---------------------------------------------------------------------------
// Individual action handlers -------------------------------------------------
// ---------------------------------------------------------------------------

function handleChangeChartType(
  command: VisualizationCommand,
  store: DashboardStore,
): CommandResult {
  const chartType = command.parameters['chart_type'];
  if (typeof chartType !== 'string' || !VALID_CHART_TYPES.has(chartType as ChartType)) {
    return {
      status: 'invalid_parameters',
      message: `CHANGE_CHART_TYPE: unknown chart_type "${chartType}". Valid types: ${[...VALID_CHART_TYPES].join(', ')}.`,
    };
  }
  store.setChartType(chartType as ChartType);
  return { status: 'ok', message: `Chart type changed to "${chartType}".` };
}

function handleUpdateFilter(
  command: VisualizationCommand,
  store: DashboardStore,
): CommandResult {
  const rawKey = command.target_variable;
  const values = command.parameters['values'];

  if (!rawKey || typeof rawKey !== 'string') {
    return {
      status: 'invalid_parameters',
      message: 'UPDATE_FILTER: target_variable (filter key) is required.',
    };
  }
  if (!Array.isArray(values) || !values.every((v) => typeof v === 'string')) {
    return {
      status: 'invalid_parameters',
      message: `UPDATE_FILTER: parameters.values must be a string[]. Received: ${JSON.stringify(values)}.`,
    };
  }
  const key = resolveFilterKey(rawKey, store);
  store.setFilter(key, values as string[]);
  return { status: 'ok', message: `Filter "${key}" updated to [${values.join(', ')}].` };
}

function handleRemoveFilter(
  command: VisualizationCommand,
  store: DashboardStore,
): CommandResult {
  const rawKey = command.target_variable;
  if (!rawKey || typeof rawKey !== 'string') {
    return {
      status: 'invalid_parameters',
      message: 'REMOVE_FILTER: target_variable (filter key) is required.',
    };
  }
  const key = resolveFilterKey(rawKey, store);
  store.removeFilter(key);
  return { status: 'ok', message: `Filter "${key}" removed.` };
}

function handleHighlightVariables(
  command: VisualizationCommand,
  store: DashboardStore,
): CommandResult {
  const variables = command.parameters['variables'];
  if (!Array.isArray(variables) || !variables.every((v) => typeof v === 'string')) {
    return {
      status: 'invalid_parameters',
      message: `HIGHLIGHT_VARIABLES: parameters.variables must be a string[]. Received: ${JSON.stringify(variables)}.`,
    };
  }
  store.setHighlightedVariables(variables as string[]);
  return {
    status: 'ok',
    message: `Highlighted variables: [${(variables as string[]).join(', ')}].`,
  };
}

function handleUpdateWeight(
  command: VisualizationCommand,
  store: DashboardStore,
): CommandResult {
  const key = command.target_variable;
  const value = command.parameters['value'];

  if (!key || typeof key !== 'string') {
    return {
      status: 'invalid_parameters',
      message: 'UPDATE_WEIGHT: target_variable (objective key) is required.',
    };
  }
  if (typeof value !== 'number' || isNaN(value) || value < 0) {
    return {
      status: 'invalid_parameters',
      message: `UPDATE_WEIGHT: parameters.value must be a non-negative number. Received: ${JSON.stringify(value)}.`,
    };
  }

  // Resolve abbreviated key against known objective keys
  const knownObjectiveKeys = store.dashboardState.availableMetadata?.objectiveKeys ?? [];
  let resolvedKey = key;
  if (knownObjectiveKeys.length > 0 && !knownObjectiveKeys.includes(key)) {
    const norm = (s: string) => s.toLowerCase().replace(/[\s_-]+/g, '');
    const matched = knownObjectiveKeys.find((k) => norm(k) === norm(key));
    if (matched) resolvedKey = matched;
  }

  store.setAgentWeightOverride(resolvedKey, value);
  return { status: 'ok', message: `Weight for "${resolvedKey}" updated to ${value}.` };
}

function handleSetAggregationLevel(
  command: VisualizationCommand,
  store: DashboardStore,
): CommandResult {
  const keys = command.parameters['keys'];
  if (!Array.isArray(keys) || !keys.every((k) => typeof k === 'string')) {
    return {
      status: 'invalid_parameters',
      message: `SET_AGGREGATION_LEVEL: parameters.keys must be a string[]. Received: ${JSON.stringify(keys)}.`,
    };
  }

  // Resolve each key against available scenario keys (fuzzy match)
  const available = store.dashboardState.availableScenarioKeys;
  const norm = (s: string) => s.toLowerCase().replace(/[\s_-]+/g, '');
  const resolved = (keys as string[]).map((k) => {
    if (available.includes(k)) return k;
    return available.find((a) => norm(a) === norm(k)) ?? k;
  });

  store.setActiveScenarioKeys(resolved);
  return { status: 'ok', message: `Aggregation level set to [${resolved.join(', ')}].` };
}

function handleReset(_command: VisualizationCommand, store: DashboardStore): CommandResult {
  store.resetDashboard();
  return { status: 'ok', message: 'Dashboard reset to defaults.' };
}

// ---------------------------------------------------------------------------
// Main dispatcher ------------------------------------------------------------
// ---------------------------------------------------------------------------

/**
 * Validate and dispatch a VisualizationCommand to the Zustand store.
 *
 * @param command - The command object from the AI response (may be undefined / malformed).
 * @param store   - A snapshot of store actions (pass the result of useDashboardStore.getState()).
 * @returns       CommandResult describing what happened — log or surface as needed.
 */
export function executeAgentCommand(
  command: VisualizationCommand | null | undefined,
  store: DashboardStore,
): CommandResult {
  // ── Guard: no command is valid (agent returned prose only) ────────────────
  if (!command) {
    return { status: 'skipped', message: 'No visualization command in agent response.' };
  }

  // ── Guard: unknown action type ────────────────────────────────────────────
  if (!VALID_ACTIONS.has(command.action as AgentAction)) {
    return {
      status: 'unknown_action',
      message: `Unrecognised action "${command.action}". Valid actions: ${[...VALID_ACTIONS].join(', ')}.`,
    };
  }

  // ── Guard: parameters must be an object ──────────────────────────────────
  if (typeof command.parameters !== 'object' || command.parameters === null) {
    return {
      status: 'invalid_parameters',
      message: `Action "${command.action}": parameters must be an object, got ${typeof command.parameters}.`,
    };
  }

  // ── Dispatch ──────────────────────────────────────────────────────────────
  try {
    switch (command.action) {
      case 'CHANGE_CHART_TYPE':
        return handleChangeChartType(command, store);
      case 'UPDATE_FILTER':
        return handleUpdateFilter(command, store);
      case 'REMOVE_FILTER':
        return handleRemoveFilter(command, store);
      case 'HIGHLIGHT_VARIABLES':
        return handleHighlightVariables(command, store);
      case 'UPDATE_WEIGHT':
        return handleUpdateWeight(command, store);
      case 'SET_AGGREGATION_LEVEL':
        return handleSetAggregationLevel(command, store);
      case 'RESET':
        return handleReset(command, store);
      default:
        // TypeScript exhaustiveness guard — should never reach here.
        return { status: 'unknown_action', message: `Unhandled action: ${command.action}` };
    }
  } catch (err) {
    // Catch unexpected store errors so the chat UI never white-screens.
    const msg = err instanceof Error ? err.message : String(err);
    return { status: 'invalid_parameters', message: `Dispatcher threw unexpectedly: ${msg}` };
  }
}
