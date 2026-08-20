"""
mooCHAT agentic loop using OpenAI native tool/function calling.

Flow:
  1. Build messages: system prompt + enriched user turn.
  2. Call model with TOOL_SCHEMAS available.
  3. If model issues tool_calls, execute each, append results, loop.
  4. Repeat up to MAX_ITERATIONS.
  5. Return the model's final text content for response parsing.

If the model or API does not support tool calling (e.g. older deployments),
the loop transparently falls back to a plain completion.
"""
import json
import logging

from config import AI_MODEL
from helpers.ai_client import get_client
from helpers.agent_tools import TOOL_SCHEMAS, execute_tool

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 4   # guard against infinite tool-call loops


def run_agent(system_prompt: str, user_turn: str, context: dict) -> str:
    """
    Execute the agentic loop and return the raw text response.

    Parameters
    ----------
    system_prompt : str
        The system instructions for this call.
    user_turn : str
        The assembled user message (includes dashboard state snapshot).
    context : dict
        Tool execution context built from the active use case:
        keys: df, objective_keys, decision_keys, objective_functions, active_weights.
        Pass an empty dict to disable tool calling (e.g. /chat/init).
    """
    client   = get_client()
    tools    = TOOL_SCHEMAS if context else []
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_turn},
    ]

    for iteration in range(MAX_ITERATIONS):
        try:
            kwargs: dict = {"model": AI_MODEL, "messages": messages}
            if tools:
                kwargs["tools"]       = tools
                kwargs["tool_choice"] = "auto"

            response = client.chat.completions.create(**kwargs)

        except Exception as api_err:
            # If the model rejects tool params (e.g. unsupported), retry without tools.
            logger.warning("[agent] API error with tools (iter %d), retrying plain: %s", iteration, api_err)
            plain = client.chat.completions.create(model=AI_MODEL, messages=messages)
            return plain.choices[0].message.content or ""

        choice = response.choices[0]
        finish = choice.finish_reason

        # ── No tool calls: model produced its final answer ─────────────────
        if finish != "tool_calls" or not getattr(choice.message, "tool_calls", None):
            return choice.message.content or ""

        # ── Tool calls requested ───────────────────────────────────────────
        # Append the assistant turn so the model retains its reasoning chain.
        messages.append(choice.message)

        for tc in choice.message.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            result_str = execute_tool(tc.function.name, args, context)
            logger.debug(
                "[agent] iter=%d tool=%s args=%s result_preview=%s",
                iteration, tc.function.name, args, result_str[:300],
            )
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      result_str,
            })

    # ── Fallback: max iterations hit, force a text answer ─────────────────
    logger.warning("[agent] max iterations (%d) reached; forcing final answer", MAX_ITERATIONS)
    messages.append({
        "role":    "user",
        "content": "Based on the tool results above, provide your final answer now.",
    })
    fallback = client.chat.completions.create(model=AI_MODEL, messages=messages)
    return fallback.choices[0].message.content or ""
