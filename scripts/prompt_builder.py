from __future__ import annotations

from typing import Any


def _value_or_unknown(value: Any, fallback: str = "Unknown") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value if value.strip() else fallback
    if isinstance(value, list):
        return ", ".join(value) if value else fallback
    return str(value)


def build_system_prompt(memo: dict[str, Any]) -> str:
    bh = memo.get("business_hours", {})
    emergency_rules = memo.get("emergency_routing_rules", {})
    transfer = memo.get("call_transfer_rules", {})

    prompt_lines = [
        "You are Clara, the inbound call agent for a commercial service-trade company.",
        "Your job is to route calls safely and efficiently. Never mention internal tools or implementation details.",
        "",
        "Account Profile",
        f"- Company: {_value_or_unknown(memo.get('company_name'))}",
        f"- Services supported: {_value_or_unknown(memo.get('services_supported'))}",
        f"- Office address: {_value_or_unknown(memo.get('office_address'))}",
        f"- Business hours: {_value_or_unknown(bh.get('days'))}, {_value_or_unknown(bh.get('start'))} to {_value_or_unknown(bh.get('end'))} {_value_or_unknown(bh.get('timezone'))}",
        f"- Emergency triggers: {_value_or_unknown(memo.get('emergency_definition'))}",
        "",
        "Call Transfer Protocol",
        f"- Primary emergency destination: {_value_or_unknown(emergency_rules.get('primary_contact'))}",
        f"- Secondary emergency destination: {_value_or_unknown(emergency_rules.get('secondary_contact'))}",
        f"- Transfer timeout seconds: {_value_or_unknown(transfer.get('timeout_seconds'))}",
        f"- Retries: {_value_or_unknown(transfer.get('retries'), fallback='1')}",
        "",
        "Office Hours Flow",
        "1. Greet caller and identify the company.",
        "2. Ask purpose of the call.",
        "3. Collect caller full name and callback number.",
        "4. Determine emergency vs non-emergency using defined triggers.",
        "5. Route or transfer based on routing rules.",
        "6. If transfer fails, apologize and explain next step based on fail protocol.",
        "7. Ask if the caller needs anything else.",
        "8. If no, close politely.",
        "",
        "After-Hours Flow",
        "1. Greet caller and state they reached after-hours service.",
        "2. Ask purpose of the call.",
        "3. Confirm whether this is an emergency.",
        "4. If emergency: collect name, callback number, and service address immediately.",
        "5. Attempt emergency transfer using transfer protocol.",
        "6. If transfer fails: apologize and assure rapid human follow-up.",
        "7. If non-emergency: collect needed details and confirm business-hours follow-up.",
        "8. Ask if the caller needs anything else.",
        "9. If no, close politely.",
        "",
        "Conversation Guardrails",
        "- Ask only questions needed for routing and dispatch.",
        "- Keep responses concise and calm.",
        "- Do not invent policy details that are not in the configuration.",
    ]
    return "\n".join(prompt_lines).strip() + "\n"


def build_agent_spec(memo: dict[str, Any], version: str) -> dict[str, Any]:
    transfer = memo.get("call_transfer_rules", {})
    emergency_rules = memo.get("emergency_routing_rules", {})
    bh = memo.get("business_hours", {})
    return {
        "agent_name": f"clara_{memo.get('account_id', 'unknown')}_{version}",
        "voice_style": "calm-professional",
        "system_prompt": build_system_prompt(memo),
        "key_variables": {
            "account_id": memo.get("account_id"),
            "company_name": memo.get("company_name"),
            "timezone": bh.get("timezone"),
            "business_hours": bh,
            "office_address": memo.get("office_address"),
            "emergency_routing": emergency_rules,
            "integration_constraints": memo.get("integration_constraints", []),
        },
        "tool_invocation_placeholders": {
            "dispatch_notify": "placeholder_dispatch_notify",
            "create_ticket": "placeholder_create_ticket",
            "lookup_account": "placeholder_lookup_account",
        },
        "call_transfer_protocol": {
            "destinations": emergency_rules.get("transfer_order", []),
            "timeout_seconds": transfer.get("timeout_seconds"),
            "retries": transfer.get("retries", 1),
        },
        "fallback_protocol_if_transfer_fails": {
            "caller_message": transfer.get("transfer_fail_message")
            or "I could not complete the transfer. Our dispatch team will call you back as quickly as possible.",
            "required_capture_fields": ["caller_name", "caller_phone", "service_address", "issue_summary"],
        },
        "version": version,
    }

