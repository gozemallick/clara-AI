def format_business_hours(hours):

    days = ", ".join(hours.get("days", [])) if hours.get("days") else "unknown days"
    start = hours.get("start") or "unknown"
    end = hours.get("end") or "unknown"

    return f"{days}, {start} to {end}"


def generate_agent_spec(memo, version):

    business_hours_text = format_business_hours(memo["business_hours"])

    emergency_triggers = ", ".join(memo.get("emergency_definition", []))

    prompt = f"""
You are Clara, an AI phone assistant for {memo.get("company_name","the company")}.

SYSTEM RULES:
- Do not mention tools or system logic.
- Only collect information required for routing.
- Be concise and professional.

BUSINESS HOURS FLOW:
1. Greet the caller
2. Ask the purpose of the call
3. Collect caller name and phone number
4. Determine if issue is emergency
5. If emergency transfer immediately
6. If transfer fails apologize and inform dispatch will follow up
7. If non-emergency route appropriately
8. Ask if anything else
9. Close politely

AFTER HOURS FLOW:
1. Greet caller
2. Ask purpose
3. Confirm emergency
4. If emergency collect name, phone, and address
5. Attempt transfer to on-call technician
6. If transfer fails apologize and assure quick follow-up
7. If non-emergency collect message and confirm callback
8. Ask if anything else
9. Close

Emergency Triggers:
{emergency_triggers}

Business Hours:
{business_hours_text}

Integration Constraints:
{", ".join(memo.get("integration_constraints", [])) or "None"}
"""

    return {
        "agent_name": memo.get("company_name", "Clara Agent"),
        "voice_style": "professional",
        "system_prompt": prompt.strip(),
        "key_variables": {
            "business_hours": memo["business_hours"],
            "address": memo["office_address"],
            "emergency_routing": memo["emergency_routing_rules"]
        },
        "call_transfer_protocol": memo["call_transfer_rules"],
        "fallback_protocol": "Notify dispatch if transfer fails",
        "version": version
    }