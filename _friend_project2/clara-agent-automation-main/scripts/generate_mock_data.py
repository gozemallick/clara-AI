import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEMO_DIR = os.path.join(BASE_DIR, "dataset", "demo_calls")
ONBOARD_DIR = os.path.join(BASE_DIR, "dataset", "onboarding_calls")

os.makedirs(DEMO_DIR, exist_ok=True)
os.makedirs(ONBOARD_DIR, exist_ok=True)


demo_transcripts = [

"""
Hello this is John from ABC Fire Protection.

We install and maintain sprinkler systems and fire alarms.

Our office hours are 8am to 5pm Monday to Friday.

If there is a sprinkler leak or fire alarm triggered, that is an emergency.

Our office is located in Dallas Texas.
""",

"""
Hi this is Maria calling from Lone Star Fire Safety.

We handle fire alarm systems and sprinkler maintenance.

Our office hours run from nine am to five pm during weekdays.

A sprinkler leak or triggered fire alarm should be treated as an emergency.

We are based in Austin Texas.
""",

"""
Good morning. This is Kevin with SafeGuard Fire Systems.

We support commercial fire alarm monitoring and sprinkler repairs.

Our business hours are 7am to 4pm Monday through Friday.

Emergency situations include sprinkler leaks or active fire alarms.

Our office address is Houston Texas.
""",

"""
Hello, this is David representing Metro Fire Protection.

Our team services sprinkler networks and alarm panels.

We operate from 8:30am until 5:30pm weekdays.

If a fire alarm activates or a sprinkler pipe leaks, that should be handled as urgent.

Our main office is in San Antonio Texas.
""",

"""
Hi this is Lisa from Guardian Fire Services.

We specialize in fire alarms and building sprinkler systems.

The office is open Monday to Friday from 9am to 6pm.

Sprinkler failures or alarm triggers should be considered emergency calls.

We are located in Fort Worth Texas.
"""
]


onboarding_transcripts = [

"""
During onboarding we confirmed business hours are actually 7am to 6pm.

Emergency issues include sprinkler leak, fire alarm triggered, and alarm faults.

Emergency calls should go directly to dispatch.
""",

"""
During onboarding the hours were updated to 6am to 5pm Monday through Friday.

Emergency cases include sprinkler leaks, fire alarms, and alarm panel faults.

Emergency calls must be transferred to dispatch immediately.
""",

"""
The confirmed schedule is 8am until 6pm weekdays.

Emergency events include sprinkler system leaks and triggered fire alarms.

Emergency calls should route to our dispatch center.
""",

"""
Business hours are confirmed as 7am to 7pm.

Emergency calls such as sprinkler failures or alarm faults should go to dispatch.

Dispatch should be contacted immediately.
""",

"""
Hours were finalized as 6:30am to 5:30pm Monday to Friday.

Emergency calls include alarm triggers and sprinkler leaks.

All emergency calls should be routed to dispatch.
"""
]


for i, text in enumerate(demo_transcripts, start=1):

    with open(os.path.join(DEMO_DIR, f"demo{i}.txt"), "w") as f:
        f.write(text.strip())


for i, text in enumerate(onboarding_transcripts, start=1):

    with open(os.path.join(ONBOARD_DIR, f"onboard{i}.txt"), "w") as f:
        f.write(text.strip())


print("Generated diverse mock dataset:")
print("• 5 demo transcripts with varied phrasing")
print("• 5 onboarding transcripts with varied updates")