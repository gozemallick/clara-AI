from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.common import derive_account_id_from_filename, read_json, read_text, write_json
from scripts.extract import extract_account_memo
from scripts.merge import merge_memos
from scripts.prompt_builder import build_agent_spec


def _load_input(path: Path) -> str:
    if path.suffix.lower() == ".json":
        payload = read_json(path)
        lines: list[str] = []
        for key, value in payload.items():
            lines.append(f"{key}: {value}")
        return "\n".join(lines)
    return read_text(path)


def _required_unknowns(memo: dict[str, Any]) -> list[str]:
    unknowns: list[str] = []
    if not memo.get("company_name"):
        unknowns.append("Company name missing.")
    business = memo.get("business_hours", {})
    if not business.get("days"):
        unknowns.append("Business days missing.")
    if not business.get("start") or not business.get("end"):
        unknowns.append("Business start/end time missing.")
    if not business.get("timezone"):
        unknowns.append("Business timezone missing.")
    if not memo.get("emergency_definition"):
        unknowns.append("Emergency definition missing.")
    if not memo.get("emergency_routing_rules", {}).get("primary_contact"):
        unknowns.append("Emergency primary contact missing.")
    return unknowns


def _write_tracker(tracker_file: Path, account_id: str, stage: str, status: str, artifacts: list[str]) -> None:
    tracker_file.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {}
    if tracker_file.exists():
        existing = read_json(tracker_file)
    account = existing.setdefault(account_id, {})
    account[stage] = {
        "status": status,
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "artifacts": artifacts,
    }
    write_json(tracker_file, existing)


def _persist_v1(account_dir: Path, memo: dict[str, Any], agent_spec: dict[str, Any]) -> None:
    v1_dir = account_dir / "v1"
    write_json(v1_dir / "memo.json", memo)
    write_json(v1_dir / "agent_spec.json", agent_spec)


def _persist_v2(account_dir: Path, memo: dict[str, Any], agent_spec: dict[str, Any], changelog: dict[str, Any]) -> None:
    v2_dir = account_dir / "v2"
    changes_dir = account_dir / "changes"
    write_json(v2_dir / "memo.json", memo)
    write_json(v2_dir / "agent_spec.json", agent_spec)
    write_json(changes_dir / "v1_to_v2.json", changelog)


def run_pipeline(input_root: Path, output_root: Path, tracker_file: Path) -> dict[str, Any]:
    demo_dir = input_root / "demo"
    onboarding_dir = input_root / "onboarding"
    output_accounts = output_root / "accounts"
    output_accounts.mkdir(parents=True, exist_ok=True)

    demo_files = sorted([file for file in demo_dir.glob("*") if file.suffix.lower() in {".txt", ".md", ".json"}])
    onboarding_files = sorted([file for file in onboarding_dir.glob("*") if file.suffix.lower() in {".txt", ".md", ".json"}])

    summary = {
        "demo_files_processed": 0,
        "onboarding_files_processed": 0,
        "accounts": [],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    for demo_file in demo_files:
        account_id = derive_account_id_from_filename(demo_file)
        transcript = _load_input(demo_file)
        account_dir = output_accounts / account_id

        v1_memo = extract_account_memo(
            transcript_text=transcript,
            account_id=account_id,
            stage="demo",
            source_file=demo_file,
            include_unknowns=True,
        )
        v1_memo["version"] = "v1"
        v1_memo["questions_or_unknowns"] = _required_unknowns(v1_memo)

        v1_agent = build_agent_spec(v1_memo, "v1")
        _persist_v1(account_dir, v1_memo, v1_agent)

        _write_tracker(
            tracker_file,
            account_id,
            stage="demo",
            status="completed",
            artifacts=[
                str(account_dir / "v1" / "memo.json"),
                str(account_dir / "v1" / "agent_spec.json"),
            ],
        )
        summary["demo_files_processed"] += 1
        summary["accounts"].append(account_id)

    for onboarding_file in onboarding_files:
        account_id = derive_account_id_from_filename(onboarding_file)
        transcript = _load_input(onboarding_file)
        account_dir = output_accounts / account_id

        base_v1_path = account_dir / "v1" / "memo.json"
        if base_v1_path.exists():
            base_v1 = read_json(base_v1_path)
        else:
            base_v1 = {
                "account_id": account_id,
                "company_name": None,
                "business_hours": {"days": None, "start": None, "end": None, "timezone": None},
                "office_address": None,
                "services_supported": [],
                "emergency_definition": [],
                "emergency_routing_rules": {
                    "primary_contact": None,
                    "secondary_contact": None,
                    "transfer_order": [],
                    "fallback": None,
                },
                "non_emergency_routing_rules": {
                    "routing_summary": None,
                    "intake_required_fields": ["caller_name", "caller_phone", "service_issue"],
                    "follow_up_window": None,
                },
                "call_transfer_rules": {
                    "timeout_seconds": None,
                    "retries": None,
                    "transfer_fail_message": None,
                },
                "integration_constraints": [],
                "after_hours_flow_summary": "",
                "office_hours_flow_summary": "",
                "questions_or_unknowns": [],
                "notes": "Base created from onboarding due to missing v1",
                "source": {"stage": "bootstrap"},
                "version": "v1",
            }

        onboarding_update = extract_account_memo(
            transcript_text=transcript,
            account_id=account_id,
            stage="onboarding",
            source_file=onboarding_file,
            include_unknowns=False,
        )

        merged_memo, changes, conflicts = merge_memos(base_v1, onboarding_update)
        merged_memo["version"] = "v2"
        merged_memo["questions_or_unknowns"] = _required_unknowns(merged_memo)
        v2_agent = build_agent_spec(merged_memo, "v2")

        changelog = {
            "account_id": account_id,
            "from_version": "v1",
            "to_version": "v2",
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_file": onboarding_file.name,
            "changes": changes,
            "conflicts": conflicts,
        }

        _persist_v2(account_dir, merged_memo, v2_agent, changelog)
        _write_tracker(
            tracker_file,
            account_id,
            stage="onboarding",
            status="completed",
            artifacts=[
                str(account_dir / "v2" / "memo.json"),
                str(account_dir / "v2" / "agent_spec.json"),
                str(account_dir / "changes" / "v1_to_v2.json"),
            ],
        )
        summary["onboarding_files_processed"] += 1

    summary["accounts"] = sorted(set(summary["accounts"]) | {derive_account_id_from_filename(f) for f in onboarding_files})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Clara assignment pipeline on local transcript dataset.")
    parser.add_argument("--input-root", type=Path, default=Path("data"), help="Root folder containing demo/ and onboarding/ subfolders.")
    parser.add_argument("--output-root", type=Path, default=Path("outputs"), help="Output root folder.")
    parser.add_argument("--tracker-file", type=Path, default=Path("tracker/tasks.json"), help="Tracking file path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = run_pipeline(args.input_root, args.output_root, args.tracker_file)
    write_json(args.output_root / "run_summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
