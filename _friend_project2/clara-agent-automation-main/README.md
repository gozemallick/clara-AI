# Clara Agent Automation Pipeline

## 1. What This Project Does

This project automates the process of converting customer call transcripts into operational configuration for an AI phone agent.

It extracts structured business information from demo and onboarding transcripts, generates an **Account Memo**, and automatically produces a **Retell-compatible agent specification**. When onboarding updates occur, the system updates the configuration, tracks differences, and generates a versioned changelog.

The system simulates an internal automation workflow used by operations teams to convert conversations into production-ready AI agent configurations.

---

## 2. Architecture & Data Flow

The pipeline has **two stages** corresponding to the operational lifecycle of an account.

```
                   DEMO CALL PIPELINE
                ------------------------
                demo transcript (.txt)
                         │
                         ▼
                  extractor.py
                         │
                         ▼
                 Account Memo (v1)
                         │
                         ▼
             agent_generator.py
                         │
                         ▼
                Agent Spec (v1)
                         │
                         ▼
              outputs/accounts/acc_X/


               ONBOARDING UPDATE PIPELINE
             --------------------------------
              onboarding transcript (.txt)
                         │
                         ▼
                  extractor.py
                         │
                         ▼
                  updater.py
                         │
                         ▼
                 Updated Memo (v2)
                         │
                         ▼
             agent_generator.py
                         │
                         ▼
                Agent Spec (v2)
                         │
                         ▼
              diff_generator.py
                         │
                         ▼
             changelog.md + diff.json
```

Additional system components:

- **metrics.py** → pipeline metrics summary
- **task_tracker.py** → CSV-based task tracking (mock for Asana)
- **dashboard.py** → Streamlit dashboard for inspection

---

## 3. Project File Structure

```
project_root/
│
├── scripts/
│   ├── extractor.py
│   ├── agent_generator.py
│   ├── updater.py
│   ├── diff_generator.py
│   ├── diff_viewer.py
│   ├── metrics.py
│   ├── task_tracker.py
│   ├── pipeline.py
│   └── generate_mock_data.py
│
├── dataset/
│   ├── demo_calls/
│   └── onboarding_calls/
│
├── outputs/
│   ├── accounts/
│   │   ├── acc_1/
│   │   │   ├── v1/
│   │   │   │   ├── memo.json
│   │   │   │   └── agent_spec.json
│   │   │   ├── v2/
│   │   │   │   ├── memo.json
│   │   │   │   └── agent_spec.json
│   │   │   ├── changelog.md
│   │   │   └── diff.json
│   │   └── ... (acc_2 through acc_5)
│   │
│   ├── task_tracker.csv
│   └── pipeline_summary.json
│
├── dashboard.py
├── requirements.txt
└── README.md
```

---

## 4. How to Run the Project

### Step 1 — Install dependencies

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 2 — Generate mock dataset

The repository includes a dataset generator that creates **5 demo transcripts and 5 onboarding transcripts with varied phrasing**, demonstrating that the extractor handles multiple transcript formats.

```bash
python scripts/generate_mock_data.py
```

### Step 3 — Run the automation pipeline

```bash
python scripts/pipeline.py
```

This will:

- Process all demo transcripts → generate v1 account memos and agent specs
- Process all onboarding transcripts → generate v2 updates
- Generate changelog and diff per account
- Update pipeline metrics
- Update task tracker

### Step 4 — Launch the dashboard

```bash
streamlit run dashboard.py
```

The dashboard allows inspection of:

- v1 and v2 account memos side by side
- Configuration differences (v1 → v2)
- Pipeline metrics

---

## 5. Where Outputs Are Stored

All generated artifacts are saved under:

```
outputs/accounts/<account_id>/
    v1/
        memo.json           ← extracted account data from demo call
        agent_spec.json     ← generated Retell agent configuration
    v2/
        memo.json           ← updated account data after onboarding
        agent_spec.json     ← updated agent configuration
    changelog.md            ← human-readable list of changes
    diff.json               ← machine-readable field-level diff

outputs/pipeline_summary.json   ← counts of accounts processed and agents generated
outputs/task_tracker.csv        ← stage tracking per account
```

---

## 6. Known Limitations

This project uses **deterministic rule-based extraction** to keep the system reproducible and zero-cost.

- Business hours parsing is regex-based. Handles digit formats (`8am`), colon formats (`8:30am`), word formats (`nine am`), and both `to` and `until` connectors. Unusual phrasing outside these patterns may not extract correctly.
- Address extraction relies on spaCy GPE entity detection and may merge unrelated location mentions.
- Emergency definitions are keyword-matched against a fixed list.
- Timezone is not inferred; it remains `null` unless explicitly stated.
- No real Retell API integration — outputs are static JSON specifications.
- Task tracker is a local CSV file, not a live Asana integration.

---

## 7. What I'd Improve With Production Access

**LLM-based extraction** — Replace regex with a structured LLM call (Claude or GPT-4) to extract account configuration from transcripts. This handles any phrasing, infers missing fields, and produces more reliable output across real-world call variety.

**Retell API integration** — Directly create and update agents via the Retell API instead of generating static JSON. The current `agent_spec.json` format mirrors what the API expects, so this is a thin integration layer away.

**Real task tracking** — Replace the CSV tracker with Asana, Linear, or Jira via webhook. Each pipeline stage (v1 generated, v2 updated, review required) maps cleanly to a task state.

**Timezone inference** — Derive timezone from the extracted office address using a geolocation API, eliminating the current `null` timezone field.

**Workflow orchestration** — Move pipeline execution into n8n or Temporal for retry logic, failure alerting, scheduling, and audit logs. The current Python module structure maps directly to n8n nodes.

**Conflict detection in updater** — Flag cases where onboarding data contradicts demo data (e.g., different company name) rather than silently overwriting.
