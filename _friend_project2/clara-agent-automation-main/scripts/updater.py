import copy


def deep_merge(original, updates, changes, parent_key=""):

    for key in updates:

        full_key = f"{parent_key}.{key}" if parent_key else key

        if key == "questions_or_unknowns":
            continue

        if isinstance(updates[key], dict) and key in original:
            deep_merge(original[key], updates[key], changes, full_key)

        else:

            if updates[key] and original.get(key) != updates[key]:

                changes.append(
                    f"{full_key} updated from {original.get(key)} -> {updates[key]}"
                )

                original[key] = updates[key]


def merge_unknowns(original, updates):

    original_unknowns = set(original.get("questions_or_unknowns", []))
    update_unknowns = set(updates.get("questions_or_unknowns", []))

    resolved = set()

    # If a previously unknown field is now filled → resolve it
    if original.get("company_name"):
        resolved.add("company_name missing")

    if original.get("business_hours", {}).get("start"):
        resolved.add("business hours not confirmed")

    original_unknowns = original_unknowns - resolved

    merged = original_unknowns.union(update_unknowns)

    return list(merged)


def update_account(existing, updates):

    updated = copy.deepcopy(existing)

    changes = []

    deep_merge(updated, updates, changes)

    updated["questions_or_unknowns"] = merge_unknowns(existing, updates)

    return updated, changes