import json
import os


def generate_pipeline_metrics(output_dir, demo_count, onboarding_count):

    metrics = {
        "accounts_processed": demo_count,
        "agents_generated": demo_count * 2,
        "updates_applied": onboarding_count
    }

    path = os.path.join(output_dir, "pipeline_summary.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return metrics