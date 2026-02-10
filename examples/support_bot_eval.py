"""
Customer Support Bot evaluation example.

Evaluates how well different LLMs answer support tickets using
provided documentation context (RAG-style evaluation).

This example simulates model responses to demonstrate the evaluation
workflow. In production, you would:
1. Call actual LLM APIs with the question + context
2. Use LLM-as-judge or heuristics to score responses

Setup:
1. Create a workspace in the UI
2. Create a task with parameters: {"model": ["gpt-4o", "claude-3-opus", "llama-3-70b"]}
3. Upload data/support_tickets.jsonl as a dataset and attach it to the task
4. Mark the task as active
5. Run from the project root: uv run --env-file=.env --with-editable=. examples/support_bot_eval.py
"""

import random

import valohai_llm

# Model profiles for simulation
# These represent typical quality/cost tradeoffs between different providers
MODEL_PROFILES = {
    "gpt-4o": {
        "relevance_base": 0.90,
        "faithfulness_base": 0.88,
        "completeness_base": 0.85,
        "latency_range": (200, 500),
        "tokens_per_char": 0.30,
    },
    "claude-3-opus": {
        "relevance_base": 0.92,
        "faithfulness_base": 0.90,
        "completeness_base": 0.88,
        "latency_range": (300, 600),
        "tokens_per_char": 0.28,
    },
    "llama-3-70b": {
        "relevance_base": 0.82,
        "faithfulness_base": 0.78,
        "completeness_base": 0.75,
        "latency_range": (150, 400),
        "tokens_per_char": 0.32,
    },
}

# Default profile for unknown models
DEFAULT_PROFILE = {
    "relevance_base": 0.80,
    "faithfulness_base": 0.75,
    "completeness_base": 0.70,
    "latency_range": (200, 500),
    "tokens_per_char": 0.30,
}


def simulate_response(model: str, ticket: dict) -> dict:
    """
    Simulate LLM response quality based on model profile.

    In a real evaluation, this would:
    1. Call the LLM API with: f"Context: {ticket['context']}\n\nQuestion: {ticket['question']}"
    2. Get the model's response
    3. Use an LLM-as-judge to score relevance, faithfulness, completeness
       (or compare against expected_answer with embeddings/heuristics)

    Returns:
        Dict with metric values (all metrics are 0.0-1.0 or numeric)
    """
    profile = MODEL_PROFILES.get(model, DEFAULT_PROFILE)

    # Questions requiring reasoning are harder for all models
    difficulty_modifier = -0.10 if ticket.get("requires_reasoning") else 0.0

    # Simulate realistic metric values with some variance
    return {
        "answer_relevance": max(
            0.0,
            min(1.0, profile["relevance_base"] + difficulty_modifier + random.uniform(-0.08, 0.08)),
        ),
        "faithfulness": max(
            0.0,
            min(1.0, profile["faithfulness_base"] + difficulty_modifier + random.uniform(-0.10, 0.05)),
        ),
        "completeness": max(
            0.0,
            min(1.0, profile["completeness_base"] + difficulty_modifier + random.uniform(-0.10, 0.10)),
        ),
        "latency_ms": random.uniform(*profile["latency_range"]),
        "output_tokens": int(
            len(ticket.get("expected_answer", "")) * profile["tokens_per_char"] * random.uniform(0.8, 1.5),
        ),
    }


def evaluate(*, params: dict, item: dict) -> dict:
    """
    Evaluation function called for each (params, item) combination.

    In real code, this would:
    1. Call the LLM API with the question + context
    2. Score the response quality
    """
    model = params.get("model", "unknown")
    return simulate_response(model, item)


def main():
    # Fetch task configuration from server
    task = valohai_llm.get_current_task()
    print(f"Running evaluation: {task.name}")
    print(f"Models: {task.parameters.get('model', [])}")
    print(f"Datasets: {[ds.name for ds in task.datasets]}")
    print("-" * 50)

    # Run evaluation over all (model, item) combinations
    # item_labels specifies which item fields to include as labels for filtering
    results = task.run(evaluate, item_labels=["category", "requires_reasoning"])

    print(f"\nEvaluation complete! Posted {len(results)} results.")


if __name__ == "__main__":
    main()
