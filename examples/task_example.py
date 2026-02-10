"""
Task runner example for Valohai LLM.

This fetches the current active task from the server, downloads any
associated datasets, and runs the evaluation function over the
cartesian product of parameters and dataset items.

To use this example:
1. Create a workspace in the UI
2. Create a task with parameters like {"model": ["gpt-4", "gpt-3.5"]}
3. Optionally attach datasets (.jsonl, .csv, .tsv, or .json files)
4. Mark the task as active
5. Run from the project root: uv run --env-file=.env --with-editable=. examples/task_example.py
"""

import random
import time

import valohai_llm


def simulate_evaluation(model: str, question: str, answer: str) -> dict:
    """Simulate running an LLM evaluation and return metrics."""
    base_accuracy = 0.85 if "gpt-4" in model else 0.75
    confabulation_score = len(question) / (len(answer) + 1)  # An entirely confabulated metric
    time.sleep(random.uniform(0.1, 0.3))
    return {
        "confabulation_score": confabulation_score,
        "accuracy": base_accuracy + random.uniform(-0.05, 0.05),
        "latency_ms": random.uniform(100, 500) if "gpt-4" in model else random.uniform(50, 200),
    }


def main():
    print("Fetching current task from server...")
    task = valohai_llm.get_current_task()
    print(f"Task: {task.name}")
    print(f"Parameters: {task.parameters}")
    print(f"Datasets: {[ds.name for ds in task.datasets]}")
    print("-" * 50)

    def evaluate(*, params: dict, item: dict) -> dict:
        """Evaluation function called for each (params, item) combination."""
        model = params.get("model", "gpt-4")
        # In a real scenario you'd use `item` data and call an actual LLM here
        return simulate_evaluation(
            model,
            question=str(item.get("question", "")),
            answer=str(item.get("answer", "")),
        )

    task.run(evaluate)


if __name__ == "__main__":
    main()
