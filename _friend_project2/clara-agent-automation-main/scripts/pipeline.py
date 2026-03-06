import os
import json
import logging

from extractor import extract_account_data
from agent_generator import generate_agent_spec
from updater import update_account
from diff_generator import generate_changelog
from diff_viewer import compare_versions, save_diff
from metrics import generate_pipeline_metrics
from task_tracker import create_task


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEMO_DIR = os.path.join(BASE_DIR, "dataset", "demo_calls")
ONBOARD_DIR = os.path.join(BASE_DIR, "dataset", "onboarding_calls")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs", "accounts")

os.makedirs(OUTPUT_DIR, exist_ok=True)


logging.basicConfig(
    filename=os.path.join(BASE_DIR, "pipeline.log"),
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_sorted_files(folder):
    if not os.path.exists(folder):
        return []
    return sorted([f for f in os.listdir(folder) if f.endswith(".txt")])


def run_demo_pipeline():

    files = get_sorted_files(DEMO_DIR)

    for i, file in enumerate(files):

        account_id = f"acc_{i+1}"

        text = read_file(os.path.join(DEMO_DIR, file))

        memo = extract_account_data(text, account_id)

        agent = generate_agent_spec(memo, "v1")

        acc_dir = os.path.join(OUTPUT_DIR, account_id, "v1")

        os.makedirs(acc_dir, exist_ok=True)

        memo_path = os.path.join(acc_dir, "memo.json")
        agent_path = os.path.join(acc_dir, "agent_spec.json")

        write_json(memo_path, memo)
        write_json(agent_path, agent)

        create_task(account_id, "v1_generated", OUTPUT_DIR)

        logging.info(f"Generated v1 for {account_id}")

    return len(files)


def run_onboarding_pipeline():

    files = get_sorted_files(ONBOARD_DIR)

    for i, file in enumerate(files):

        account_id = f"acc_{i+1}"

        text = read_file(os.path.join(ONBOARD_DIR, file))

        updates = extract_account_data(text, account_id)

        v1_path = os.path.join(
            OUTPUT_DIR, account_id, "v1", "memo.json"
        )

        if not os.path.exists(v1_path):
            continue

        with open(v1_path, "r", encoding="utf-8") as f:
            existing = json.load(f)

        updated, changes = update_account(existing, updates)

        agent = generate_agent_spec(updated, "v2")

        v2_dir = os.path.join(OUTPUT_DIR, account_id, "v2")

        os.makedirs(v2_dir, exist_ok=True)

        memo_path = os.path.join(v2_dir, "memo.json")
        agent_path = os.path.join(v2_dir, "agent_spec.json")

        write_json(memo_path, updated)
        write_json(agent_path, agent)

        generate_changelog(
            changes,
            os.path.join(OUTPUT_DIR, account_id, "changelog.md")
        )

        diff = compare_versions(v1_path, memo_path)

        save_diff(
            diff,
            os.path.join(OUTPUT_DIR, account_id, "diff.json")
        )

        create_task(account_id, "v2_generated", OUTPUT_DIR)

        logging.info(f"Generated v2 for {account_id}")

    return len(files)


if __name__ == "__main__":

    print("Starting Clara Agent Automation Pipeline...\n")

    demo_count = run_demo_pipeline()

    onboarding_count = run_onboarding_pipeline()

    metrics = generate_pipeline_metrics(
        os.path.join(BASE_DIR, "outputs"),
        demo_count,
        onboarding_count
    )

    print("Pipeline Summary:", metrics)

    print("\nPipeline completed successfully.")