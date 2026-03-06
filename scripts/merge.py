from __future__ import annotations

from copy import deepcopy
from typing import Any

from scripts.common import dedupe_keep_order, is_blank


def _merge_lists(base: list[Any], update: list[Any], key: str) -> list[Any]:
    if is_blank(update):
        return base
    if key in {"services_supported", "emergency_definition", "integration_constraints"}:
        merged = [str(item) for item in base] + [str(item) for item in update]
        return dedupe_keep_order(merged)
    return update


def _compare_and_set(
    result: dict[str, Any],
    update_value: Any,
    path: str,
    changes: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> None:
    key = path.split(".")[-1]
    base_value = result.get(key)
    if isinstance(base_value, list) and isinstance(update_value, list):
        merged_list = _merge_lists(base_value, update_value, key)
        if merged_list != base_value:
            changes.append(
                {
                    "path": path,
                    "old": base_value,
                    "new": merged_list,
                    "reason": "onboarding_update",
                }
            )
            result[key] = merged_list
        return

    if base_value != update_value:
        if not is_blank(base_value) and not is_blank(update_value):
            conflicts.append(
                {
                    "path": path,
                    "base": base_value,
                    "incoming": update_value,
                    "resolution": "incoming_overrides_base",
                }
            )
        changes.append(
            {
                "path": path,
                "old": base_value,
                "new": update_value,
                "reason": "onboarding_update",
            }
        )
        result[key] = update_value


def _deep_merge(
    base: dict[str, Any],
    update: dict[str, Any],
    parent_path: str,
    changes: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
) -> dict[str, Any]:
    result = deepcopy(base)
    for key, update_value in update.items():
        if key in {"source", "notes", "questions_or_unknowns"}:
            continue
        path = f"{parent_path}.{key}" if parent_path else key
        if is_blank(update_value):
            continue

        if isinstance(update_value, dict):
            base_value = result.get(key)
            if isinstance(base_value, dict):
                result[key] = _deep_merge(base_value, update_value, path, changes, conflicts)
            else:
                _compare_and_set(result, update_value, path, changes, conflicts)
            continue

        _compare_and_set(result, update_value, path, changes, conflicts)
    return result


def merge_memos(base_memo: dict[str, Any], onboarding_update: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    changes: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    merged = _deep_merge(base_memo, onboarding_update, "", changes, conflicts)
    merged["notes"] = f"{base_memo.get('notes', '').strip()} | Updated with onboarding data".strip(" |")
    merged["source"] = {
        "stage": "onboarding",
        "base_source": base_memo.get("source", {}),
        "update_source": onboarding_update.get("source", {}),
    }
    return merged, changes, conflicts

