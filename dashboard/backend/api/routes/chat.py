import json
import logging

import openai
import pandas as pd
from flask import Blueprint, jsonify, request
from flask_cors import cross_origin

import cache
from helpers.agent_runner import run_agent
from helpers.ai_client import (
    CHAT_SYSTEM_PROMPT,
    INIT_SYSTEM_PROMPT,
    PROACTIVE_SYSTEM_PROMPT,
    chat_completion,
    extract_json,
)

bp = Blueprint('chat', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _filter_df(df: pd.DataFrame, active_filters: dict) -> pd.DataFrame:
    """Apply active_filters (key → [values]) directly to a DataFrame."""
    result = df.copy()
    for key, values in active_filters.items():
        if values and key in result.columns:
            result = result[result[key].isin(values)]
    return result


def _build_tool_context(dashboard_ctx: dict) -> dict:
    """
    Construct the context dict passed to every tool executor.

    Returns an empty dict when no use case is loaded (tools will be
    disabled by the agent runner in that case).
    """
    metadata        = (dashboard_ctx.get("availableMetadata") or {})
    use_case        = metadata.get("useCaseName")
    sidebar_filters = dashboard_ctx.get("sidebarFilters") or {}
    agent_filters   = dashboard_ctx.get("activeFilters") or {}
    active_weights  = dashboard_ctx.get("activeWeights") or {}

    if not use_case:
        return {}

    try:
        data = cache.get_or_load(use_case)
    except Exception as exc:
        logger.warning("[chat] Could not load use case '%s': %s", use_case, exc)
        return {}

    # Mirror the frontend's effectiveFilters logic: sidebar filters as base,
    # agent-applied filters override on conflict.
    effective_filters = {**sidebar_filters, **agent_filters}
    filtered_df = _filter_df(data["csv_data"], effective_filters)
    return {
        "df":                  filtered_df,
        "objective_keys":      list(data["objective_functions"].keys()),
        "decision_keys":       list(data["decision_variables"].keys()),
        "objective_functions": data["objective_functions"],
        "active_weights":      active_weights,
    }


def _get_full_filter_options(use_case: str) -> dict:
    """
    Load the complete set of valid filter values for each hyperparameter
    directly from the use-case cache.

    The frontend only sends currently-selected values (which start as empty
    arrays), so the agent would otherwise not know which values are valid.
    """
    try:
        data = cache.get_or_load(use_case)
        return {
            k: v.get("values", [])
            for k, v in data["hyperparameters"].items()
            if isinstance(v, dict) and v.get("values")
        }
    except Exception:
        return {}


def _build_user_turn(user_message: str, dashboard_ctx: dict) -> str:
    """
    Assemble the full user turn sent to the model.

    Includes the dashboard state snapshot so the agent always knows:
      • which use case and metadata are active
      • what filters and weights are currently applied
      • ALL valid values for each filter key (loaded from cache, not from frontend)
      • a sample of the current top-ranked solutions
    """
    metadata        = (dashboard_ctx.get("availableMetadata") or {})
    sidebar_filters         = dashboard_ctx.get("sidebarFilters") or {}
    agent_filters           = dashboard_ctx.get("activeFilters") or {}
    active_weights          = dashboard_ctx.get("activeWeights") or {}
    solution_sample         = dashboard_ctx.get("activeSolutionSample") or []
    chart_type              = dashboard_ctx.get("activeChartType", "unknown")
    tab_index               = dashboard_ctx.get("activeTabIndex", 0)
    tab_names               = {0: "Decision Making", 1: "Scenario Comparison", 2: "Cameo"}
    tab_label               = tab_names.get(tab_index, f"tab {tab_index}")
    active_scenario_keys    = dashboard_ctx.get("activeScenarioKeys") or []
    available_scenario_keys = dashboard_ctx.get("availableScenarioKeys") or []

    use_case = metadata.get("useCaseName", "")
    full_filter_options = _get_full_filter_options(use_case) if use_case else {}

    # Merged view: sidebar as base, agent overrides on conflict — same as frontend effectiveFilters.
    effective_filters = {**sidebar_filters, **agent_filters}

    ctx_lines = [
        f"Use case:        {use_case or 'not loaded'}",
        f"Objectives:      {', '.join(metadata.get('objectiveKeys', []))}",
        f"Decision vars:   {', '.join(metadata.get('decisionKeys', []))}",
        f"Hyperparameters: {', '.join(metadata.get('hyperparameterKeys', []))}",
        f"Active tab:      {tab_label} (index {tab_index})",
        f"Active chart:    {chart_type}",
        f"Active filters:  {json.dumps(effective_filters)}",
        f"Active weights:  {json.dumps(active_weights)}",
        f"Available filter options (key → ALL valid values): {json.dumps(full_filter_options)}",
        f"Aggregation level (selected): {json.dumps(active_scenario_keys)}",
        f"Aggregation level (available keys): {json.dumps(available_scenario_keys)}",
    ]
    if solution_sample:
        ctx_lines.append(
            f"Top solutions sample ({len(solution_sample)} rows):\n"
            + json.dumps(solution_sample, indent=2)
        )

    context_block = "\n".join(ctx_lines)
    return (
        f"=== CURRENT DASHBOARD STATE ===\n{context_block}\n"
        f"=== USER QUESTION ===\n{user_message}"
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@bp.route('/chat/init', methods=['POST'])
@cross_origin()
def chat_init():
    """
    Fire once when the chat panel opens.
    Returns a structured welcome / use-case summary.
    No tool calling needed here — uses a simple completion.
    """
    try:
        body     = request.get_json(force=True) or {}
        metadata = (body.get('dashboard_context') or {}).get('availableMetadata') or {}

        if not metadata:
            return jsonify({'response_text': 'Welcome to PyMOODS! Load a use case to get started.'})

        use_case = metadata.get("useCaseName", "unknown")
        full_filter_options = _get_full_filter_options(use_case)
        context_summary = (
            f"Use case: {use_case}\n"
            f"Objectives: {', '.join(metadata.get('objectiveKeys', []))}\n"
            f"Decision variables: {', '.join(metadata.get('decisionKeys', []))}\n"
            f"Hyperparameters: {', '.join(metadata.get('hyperparameterKeys', []))}\n"
            f"Available filter options (key → ALL valid values): {json.dumps(full_filter_options)}"
        )
        user_turn = (
            f"The user just opened the dashboard. Loaded data schema:\n{context_summary}\n\n"
            f"Greet the user with a structured summary following the formatting rules."
        )

        raw = chat_completion(INIT_SYSTEM_PROMPT, user_turn)
        try:
            result = extract_json(raw)
        except (json.JSONDecodeError, ValueError):
            result = {'response_text': raw}
        result.setdefault('response_text', raw)
        return jsonify(result)

    except openai.AuthenticationError:
        return jsonify({'response_text': 'AI service unavailable — check LLM_API_KEY.'}), 503
    except Exception as e:
        logger.error("[chat/init] %s", e)
        return jsonify({'response_text': 'Could not load use case summary.'}), 500


@bp.route('/chat', methods=['POST'])
@cross_origin()
def chat():
    """
    Main chat endpoint — uses the agentic loop with tool calling.

    The agent may call data tools (query_solutions, get_variable_statistics, etc.)
    before composing its final response.  Tool results are invisible to the user
    but ground the answer in real data from the active use case.
    """
    try:
        body          = request.get_json(force=True) or {}
        user_message  = (body.get("message") or "").strip()
        dashboard_ctx = body.get("dashboard_context") or {}

        if not user_message:
            return jsonify({"error": "message is required"}), 400

        # Build the tool context (filtered DataFrame + metadata).
        # Empty dict → no use case loaded → tools disabled.
        tool_context = _build_tool_context(dashboard_ctx)

        # Assemble the enriched user turn with full dashboard state.
        user_turn = _build_user_turn(user_message, dashboard_ctx)

        # Run the agentic loop.
        raw = run_agent(CHAT_SYSTEM_PROMPT, user_turn, tool_context)

        try:
            result = extract_json(raw)
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("[chat] JSON parse failed: %s\nRaw response: %s", exc, raw[:500])
            # Model returned plain text (no JSON) — surface it as-is.
            return jsonify({"response_text": raw})

        result.setdefault("response_text", raw)
        return jsonify(result)

    except openai.AuthenticationError:
        logger.error("[chat] Invalid or missing LLM_API_KEY")
        return jsonify({"error": "AI service authentication failed. Check LLM_API_KEY."}), 503
    except openai.APIConnectionError as e:
        logger.error("[chat] Could not reach AI incubator: %s", e)
        return jsonify({"error": "Could not reach the AI service. Check network/VPN."}), 503
    except Exception as e:
        logger.error("[chat] Unexpected error: %s", e, exc_info=True)
        return jsonify({"error": str(e)}), 500


@bp.route('/chat/proactive', methods=['POST'])
@cross_origin()
def chat_proactive():
    """
    Background analysis triggered by a dashboard state change.
    Returns a short unsolicited insight without a user message.
    Silently returns empty on any error so the UI is never blocked.
    """
    try:
        body          = request.get_json(force=True) or {}
        trigger       = (body.get('trigger') or 'state changed').strip()
        dashboard_ctx = body.get('dashboard_context') or {}

        use_case = (dashboard_ctx.get('availableMetadata') or {}).get('useCaseName', '')
        if not use_case:
            return jsonify({'response_text': '', 'suggested_questions': []}), 200

        tool_context = _build_tool_context(dashboard_ctx)
        user_turn    = _build_user_turn(
            f"Dashboard event: {trigger}. "
            "Follow the two-part template: (1) summarise this action in one sentence, "
            "then (2) call the data tools and share a specific, data-driven insight "
            "that directly relates to what the user just did.",
            dashboard_ctx,
        )

        raw = run_agent(PROACTIVE_SYSTEM_PROMPT, user_turn, tool_context)

        try:
            result = extract_json(raw)
        except (json.JSONDecodeError, ValueError):
            result = {'response_text': raw}

        result.setdefault('response_text', raw)
        # Proactive insights never mutate the dashboard on their own.
        result.pop('visualization_command', None)
        return jsonify(result)

    except (openai.AuthenticationError, openai.APIConnectionError) as e:
        logger.warning("[chat/proactive] API unavailable: %s", e)
        return jsonify({'response_text': ''}), 503
    except Exception as e:
        logger.error("[chat/proactive] %s", e, exc_info=True)
        return jsonify({'response_text': ''}), 500
