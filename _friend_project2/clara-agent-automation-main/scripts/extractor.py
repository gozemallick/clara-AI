import re
import spacy

nlp = spacy.load("en_core_web_sm")


def safe_append(lst, value):
    if value and value not in lst:
        lst.append(value)


def extract_account_data(text, account_id):

    lower_text = text.lower()

    data = {
        "account_id": account_id,
        "company_name": None,
        "business_hours": {
            "days": [],
            "start": None,
            "end": None,
            "timezone": None
        },
        "office_address": None,
        "services_supported": [],
        "emergency_definition": [],
        "emergency_routing_rules": {
            "primary_contact": None,
            "secondary_contact": None,
            "fallback_action": None
        },
        "non_emergency_routing_rules": {},
        "call_transfer_rules": {
            "timeout_seconds": None,
            "retry_attempts": None,
            "failure_message": None
        },
        "integration_constraints": [],
        "after_hours_flow_summary": None,
        "office_hours_flow_summary": None,
        "questions_or_unknowns": [],
        "notes": ""
    }

    doc = nlp(text)

    for ent in doc.ents:
        if ent.label_ == "ORG":
            data["company_name"] = ent.text
            break

    match = re.search(r'from\s+([A-Z][A-Za-z\s]+)', text)
    if match and not data["company_name"]:
        data["company_name"] = match.group(1).strip()

    gpe_entities = [ent.text for ent in doc.ents if ent.label_ == "GPE"]

    if gpe_entities:
        data["office_address"] = ", ".join(gpe_entities)

    # Handle "to" and "until"
    hours = re.search(r'(\d{1,2}(?::\d{2})?am)\s*(?:to|until)\s*(\d{1,2}(?::\d{2})?pm)', lower_text)

    # Handle word-form numbers
    word_hours = re.search(r'(nine|eight|seven|six|ten)\s*am\s*(?:to|until)\s*(five|six|seven|eight|nine|ten)\s*pm', lower_text)
    word_map = {"six":"6","seven":"7","eight":"8","nine":"9","ten":"10","five":"5"}
    if not hours and word_hours:
        data["business_hours"]["start"] = word_map.get(word_hours.group(1), word_hours.group(1)) + "am"
        data["business_hours"]["end"] = word_map.get(word_hours.group(2), word_hours.group(2)) + "pm"

    # Handle "weekdays"
    if "monday to friday" in lower_text or "monday through friday" in lower_text or "weekdays" in lower_text:
        data["business_hours"]["days"] = ["Monday","Tuesday","Wednesday","Thursday","Friday"]

    if "sprinkler" in lower_text:
        safe_append(data["services_supported"], "sprinkler systems")

    if "fire alarm" in lower_text:
        safe_append(data["services_supported"], "fire alarms")

    emergency_keywords = [
        "sprinkler leak",
        "fire alarm triggered",
        "alarm fault"
    ]

    for keyword in emergency_keywords:
        if keyword in lower_text:
            safe_append(data["emergency_definition"], keyword)

    if "dispatch" in lower_text:
        data["emergency_routing_rules"]["primary_contact"] = "dispatch"

    timeout = re.search(r'(\d+)\s*seconds', lower_text)

    if timeout:
        data["call_transfer_rules"]["timeout_seconds"] = int(timeout.group(1))

    data["office_hours_flow_summary"] = (
        "During business hours the agent collects caller information "
        "and transfers emergencies immediately."
    )

    data["after_hours_flow_summary"] = (
        "After hours the agent collects emergency details and attempts "
        "on-call technician transfer."
    )

    if not data["company_name"]:
        data["questions_or_unknowns"].append("company_name missing")

    if not data["business_hours"]["start"]:
        data["questions_or_unknowns"].append("business hours not confirmed")

    if not data["emergency_routing_rules"]["primary_contact"]:
        data["questions_or_unknowns"].append(
            "emergency routing contact not specified"
        )

    return data