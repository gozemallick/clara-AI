from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from scripts.common import dedupe_keep_order, normalize_whitespace, sentence_chunks

PHONE_PATTERN = re.compile(r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}")
TIME_RANGE_PATTERN = re.compile(
    r"(\d{1,2}(?::\d{2})?\s?(?:am|pm))\s*(?:to|-)\s*(\d{1,2}(?::\d{2})?\s?(?:am|pm))",
    re.IGNORECASE,
)

TIMEZONE_PATTERN = re.compile(
    r"\b(EST|EDT|CST|CDT|MST|MDT|PST|PDT|UTC|GMT|IST|ET|CT|MT|PT)\b",
    re.IGNORECASE,
)

DAY_PATTERN = re.compile(
    r"(monday\s*(?:to|-)\s*friday|mon\s*(?:to|-)\s*fri|"
    r"monday\s*(?:to|-)\s*saturday|mon\s*(?:to|-)\s*sat|"
    r"monday\s*(?:to|-)\s*sunday|mon\s*(?:to|-)\s*sun|24/7|seven days)",
    re.IGNORECASE,
)

ADDRESS_PATTERN = re.compile(
    r"(\d{2,6}\s+[a-z0-9\.\s,\-#]+(?:street|road|avenue|boulevard|lane|drive|way|st\.|rd\.|ave\.|blvd\.|ln\.|dr\.)\b[^\n\.]*)",
    re.IGNORECASE,
)

SERVICE_KEYWORDS = [
    "sprinkler",
    "fire alarm",
    "alarm",
    "extinguisher",
    "backflow",
    "electrical",
    "hvac",
    "maintenance",
    "inspection",
    "generator",
    "panel",
]

EMERGENCY_TRIGGERS = [
    "sprinkler leak",
    "burst pipe",
    "water flow alarm",
    "fire alarm triggered",
    "active fire alarm",
    "no power",
    "smell smoke",
    "urgent",
    "emergency",
    "after-hours emergency",
]

INTEGRATION_KEYWORDS = ["servicetrade", "service trade", "integration", "do not create", "never create", "must not"]


def _match_first(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1).strip() if match else None


def _extract_company_name(text: str) -> str | None:
    lines = [line.strip() for line in normalize_whitespace(text).split("\n") if line.strip()]
    patterns = [
        re.compile(r"(?:company|business|client|account)\s*(?:name)?\s*[:\-]\s*(.+)", re.IGNORECASE),
        re.compile(r"(?:this is|we are)\s+([a-z0-9&\-\s]+(?:llc|inc|co|corp|corporation|services|systems|solutions))", re.IGNORECASE),
    ]
    for line in lines[:25]:
        for pattern in patterns:
            match = pattern.search(line)
            if match:
                return _clean_value(match.group(1))
    title_case_guess = re.search(r"\b([A-Z][a-zA-Z0-9&]+\s+[A-Z][a-zA-Z0-9&]+(?:\s+(?:LLC|Inc|Co|Corp|Services|Systems))?)\b", text)
    if title_case_guess:
        return _clean_value(title_case_guess.group(1))
    return None


def _extract_business_hours(text: str) -> dict[str, Any]:
    lower = text.lower()
    days = _match_first(DAY_PATTERN, lower)
    start = None
    end = None
    tz_match = TIMEZONE_PATTERN.search(text)
    timezone = tz_match.group(1).upper() if tz_match else None

    hours_line_patterns = [
        re.compile(r"(?:business|office)\s*hours?\s*[:\-]\s*([^\n\.]+)", re.IGNORECASE),
        re.compile(r"open\s*[:\-]?\s*([^\n\.]+)", re.IGNORECASE),
    ]
    candidate = ""
    for pattern in hours_line_patterns:
        match = pattern.search(text)
        if match:
            candidate = match.group(1)
            break
    if not candidate:
        for line in normalize_whitespace(text).split("\n"):
            if "hour" in line.lower() or "open" in line.lower():
                candidate = line
                break

    time_match = TIME_RANGE_PATTERN.search(candidate or text)
    if time_match:
        start = _normalize_time(time_match.group(1))
        end = _normalize_time(time_match.group(2))

    if "24/7" in lower or "24 x 7" in lower or "twenty four seven" in lower:
        days = "Monday-Sunday"
        start = "12:00 AM"
        end = "11:59 PM"

    if days:
        days = _normalize_days(days)

    return {
        "days": days,
        "start": start,
        "end": end,
        "timezone": timezone,
    }


def _normalize_time(value: str) -> str:
    value = value.strip().lower().replace(".", "")
    match = re.match(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", value)
    if not match:
        return value.upper()
    hour = int(match.group(1))
    minute = int(match.group(2) or "0")
    ampm = match.group(3).upper()
    return f"{hour:02d}:{minute:02d} {ampm}"


def _normalize_days(value: str) -> str:
    lower = value.lower().replace(" ", "")
    mapping = {
        "mondaytofriday": "Monday-Friday",
        "montofri": "Monday-Friday",
        "mondaytosaturday": "Monday-Saturday",
        "montosat": "Monday-Saturday",
        "mondaytosunday": "Monday-Sunday",
        "montosun": "Monday-Sunday",
        "24/7": "Monday-Sunday",
        "sevendays": "Monday-Sunday",
    }
    return mapping.get(lower, value.title())


def _extract_office_address(text: str) -> str | None:
    explicit = re.search(r"(?:office\s*address|address)\s*[:\-]\s*([^\n]+)", text, re.IGNORECASE)
    if explicit:
        return _clean_value(explicit.group(1))
    match = ADDRESS_PATTERN.search(text)
    if match:
        return _clean_value(match.group(1))
    return None


def _extract_services(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    for keyword in SERVICE_KEYWORDS:
        if keyword in lower:
            found.append(keyword.title())
    return dedupe_keep_order(found)


def _extract_emergency_definition(text: str) -> list[str]:
    sentences = sentence_chunks(text)
    candidates: list[str] = []
    for sentence in sentences:
        lower = sentence.lower()
        if "emergency" in lower:
            candidates.append(_clean_value(sentence))
            continue
        for trigger in EMERGENCY_TRIGGERS:
            if trigger in lower:
                candidates.append(_clean_value(sentence))
                break
    return dedupe_keep_order(candidates)


def _extract_integration_constraints(text: str) -> list[str]:
    constraints: list[str] = []
    for sentence in sentence_chunks(text):
        lower = sentence.lower()
        if any(keyword in lower for keyword in INTEGRATION_KEYWORDS):
            constraints.append(_clean_value(sentence))
    return dedupe_keep_order(constraints)


def _extract_transfer_rules(text: str) -> dict[str, Any]:
    timeout = None
    retries = None
    fail_phrase = None

    timeout_patterns = [
        re.compile(r"(?:after|within|for)\s*(\d{1,3})\s*(?:seconds|second|sec|s)\s*(?:if transfer fails|before fallback|before voicemail)?", re.IGNORECASE),
        re.compile(r"(?:timeout|ring)\s*(?:is|for|to)?\s*(\d{1,3})\s*(?:seconds|second|sec|s)", re.IGNORECASE),
    ]
    for pattern in timeout_patterns:
        match = pattern.search(text)
        if match:
            timeout = int(match.group(1))
            break

    retries_match = re.search(r"(\d+)\s*(?:retry|retries|attempt|attempts|times)", text, re.IGNORECASE)
    if retries_match:
        retries = int(retries_match.group(1))

    for sentence in sentence_chunks(text):
        lower = sentence.lower()
        if "transfer fails" in lower or "nobody answers" in lower or "if no answer" in lower:
            fail_phrase = _clean_value(sentence)
            break

    return {
        "timeout_seconds": timeout,
        "retries": retries,
        "transfer_fail_message": fail_phrase,
    }


def _extract_routing_rules(text: str) -> tuple[dict[str, Any], dict[str, Any]]:
    sentences = sentence_chunks(text)
    phone_numbers = PHONE_PATTERN.findall(text)
    unique_numbers = dedupe_keep_order(phone_numbers)

    emergency_lines: list[str] = []
    non_emergency_lines: list[str] = []

    for sentence in sentences:
        lower = sentence.lower()
        if "emergency" in lower:
            emergency_lines.append(_clean_value(sentence))
        if "non-emergency" in lower or "non emergency" in lower:
            non_emergency_lines.append(_clean_value(sentence))

    primary = unique_numbers[0] if unique_numbers else None
    secondary = unique_numbers[1] if len(unique_numbers) > 1 else None

    emergency = {
        "primary_contact": primary,
        "secondary_contact": secondary,
        "transfer_order": dedupe_keep_order(unique_numbers[:2]),
        "fallback": emergency_lines[0] if emergency_lines else None,
    }
    non_emergency = {
        "routing_summary": non_emergency_lines[0] if non_emergency_lines else None,
        "intake_required_fields": ["caller_name", "caller_phone", "service_issue"],
        "follow_up_window": _extract_follow_up_window(text),
    }
    return emergency, non_emergency


def _extract_follow_up_window(text: str) -> str | None:
    match = re.search(
        r"(same day|next business day|within\s+\d+\s*(?:hours|hour|days|day))",
        text,
        re.IGNORECASE,
    )
    return _clean_value(match.group(1)) if match else None


def _extract_flow_summaries(memo: dict[str, Any]) -> tuple[str, str]:
    hours = memo["business_hours"]
    timezone = hours.get("timezone") or "local timezone"
    office = (
        f"During office hours ({hours.get('days') or 'configured days'} "
        f"{hours.get('start') or '?'}-{hours.get('end') or '?'} {timezone}), "
        "the agent greets the caller, collects purpose/name/number, and routes according to emergency rules."
    )
    after = (
        "After hours, the agent confirms emergency status immediately. "
        "For emergencies, it captures name, number, and address before transfer. "
        "For non-emergencies, it logs details and confirms next-business-hours follow-up."
    )
    return office, after


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" -:\t\n")


def _build_unknowns(memo: dict[str, Any]) -> list[str]:
    unknowns: list[str] = []
    if not memo.get("company_name"):
        unknowns.append("Company name was not clearly stated.")
    bh = memo.get("business_hours", {})
    if not bh.get("days") or not bh.get("start") or not bh.get("end"):
        unknowns.append("Business hours are incomplete (days/start/end missing).")
    if not bh.get("timezone"):
        unknowns.append("Business timezone was not confirmed.")
    if not memo.get("emergency_definition"):
        unknowns.append("Emergency definition triggers were not explicitly provided.")
    if not memo.get("emergency_routing_rules", {}).get("primary_contact"):
        unknowns.append("Primary emergency transfer destination is missing.")
    if not memo.get("call_transfer_rules", {}).get("timeout_seconds"):
        unknowns.append("Transfer timeout seconds were not specified.")
    return unknowns


def extract_account_memo(
    transcript_text: str,
    account_id: str,
    stage: str,
    source_file: Path,
    include_unknowns: bool = True,
) -> dict[str, Any]:
    text = normalize_whitespace(transcript_text)
    company_name = _extract_company_name(text)
    business_hours = _extract_business_hours(text)
    office_address = _extract_office_address(text)
    services = _extract_services(text)
    emergency_definition = _extract_emergency_definition(text)
    emergency_rules, non_emergency_rules = _extract_routing_rules(text)
    call_transfer_rules = _extract_transfer_rules(text)
    integration_constraints = _extract_integration_constraints(text)

    memo: dict[str, Any] = {
        "account_id": account_id,
        "company_name": company_name,
        "business_hours": business_hours,
        "office_address": office_address,
        "services_supported": services,
        "emergency_definition": emergency_definition,
        "emergency_routing_rules": emergency_rules,
        "non_emergency_routing_rules": non_emergency_rules,
        "call_transfer_rules": call_transfer_rules,
        "integration_constraints": integration_constraints,
        "after_hours_flow_summary": "",
        "office_hours_flow_summary": "",
        "questions_or_unknowns": [],
        "notes": f"Generated from {stage} input: {source_file.name}",
        "source": {
            "stage": stage,
            "file_name": source_file.name,
        },
    }
    office_summary, after_summary = _extract_flow_summaries(memo)
    memo["office_hours_flow_summary"] = office_summary
    memo["after_hours_flow_summary"] = after_summary

    if include_unknowns:
        memo["questions_or_unknowns"] = _build_unknowns(memo)
    return memo
