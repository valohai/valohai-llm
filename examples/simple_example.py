# /// script
# dependencies = ["rich"]
# ///

import random
import time

from rich.progress import Progress

import valohai_llm


def simulate_evaluation(model: str) -> dict:
    """Simulate running an LLM evaluation and return metrics."""
    base_accuracy = 0.85 if "gpt-4" in model else 0.75
    time.sleep(random.uniform(1, 3))
    return {
        "accuracy": base_accuracy + random.uniform(-0.05, 0.05),
        "recall": base_accuracy + random.uniform(-0.03, 0.07),
        "f1_score": base_accuracy + random.uniform(-0.04, 0.04),
        "latency_ms": random.uniform(100, 500) if "gpt-4" in model else random.uniform(50, 200),
        "cost_usd": 0.03 if "gpt-4" in model else 0.002,
    }


def main():
    models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]
    datasets = ["mmlu", "hellaswag", "truthfulqa"]

    print("Running simulated evaluations...")
    print("-" * 50)

    for model in models:
        for dataset in datasets:
            with Progress(transient=True) as progress:
                progress.add_task(f"Evaluating {model} on {dataset}...", total=None)
                metrics = simulate_evaluation(model)

            # Post the result to Valohai LLM
            result = valohai_llm.post_result(
                task="benchmark-eval",
                labels={"model": model, "dataset": dataset},
                metrics=metrics,
            )
            print("=>", result)


if __name__ == "__main__":
    main()
