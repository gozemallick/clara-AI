# Clara Answers Assignment Project

Zero-cost, transcript-first automation pipeline for:

1. Demo call transcript -> `v1` account memo + Retell agent draft spec
2. Onboarding transcript/form -> `v2` merged memo + updated agent draft spec + changelog

The implementation is deterministic, idempotent, and uses Python standard library only.

## Repository Structure

```text
.
|-- data/
|   |-- demo/
|   `-- onboarding/
|-- outputs/
|   `-- accounts/<account_id>/{v1,v2,changes}
|-- schemas/
|   |-- account_memo.schema.json
|   `-- agent_spec.schema.json
|-- scripts/
|   |-- extract.py
|   |-- merge.py
|   |-- prompt_builder.py
|   `-- run_pipeline.py
|-- tracker/
|   `-- tasks.json
`-- workflows/
    |-- n8n_clara_pipeline.json
    |-- n8n_clara_pipeline_cloud.json
    |-- n8n_clara_pipeline_cloud_verbose.json
    |-- n8n_clara_pipeline_cloud_correct.json
    `-- n8n_clara_pipeline_cloud_hybrid.json
```

## What This Pipeline Produces

Per account:

- `outputs/accounts/<account_id>/v1/memo.json`
- `outputs/accounts/<account_id>/v1/agent_spec.json`
- `outputs/accounts/<account_id>/v2/memo.json` (if onboarding exists)
- `outputs/accounts/<account_id>/v2/agent_spec.json` (if onboarding exists)
- `outputs/accounts/<account_id>/changes/v1_to_v2.json` (if onboarding exists)

Global:

- `outputs/run_summary.json`
- `tracker/tasks.json` (task tracker alternative to Asana)

## Input Contract

Place files in:

- `data/demo/`
- `data/onboarding/`

Supported input file types:

- `.txt`
- `.md`
- `.json` (key-value onboarding form style)

Account matching rule:

- Account ID is derived from filename.
- Example: `account_001_demo.txt` and `account_001_onboarding.txt` map to `account_001`.

## Run Locally

```bash
python scripts/run_pipeline.py --input-root data --output-root outputs --tracker-file tracker/tasks.json
```

The command is safe to run multiple times. It rewrites deterministic outputs and updates tracker state.

## Architecture and Data Flow

1. Ingest transcript/form file.
2. Extract structured fields into account memo JSON (rule-based, no paid LLM).
3. Generate Retell agent draft spec and required system prompt flow.
4. Persist `v1` artifacts for demo input.
5. For onboarding input, extract update memo and merge into existing `v1`.
6. Write `v2` artifacts and explicit changelog with conflict records.
7. Update task tracker file with artifact paths and stage completion.

## Prompt Hygiene Coverage

Generated prompt includes required:

- Office-hours flow: greeting, purpose, name+number collection, transfer/route, fallback, anything-else, close.
- After-hours flow: greeting, purpose, emergency confirmation, immediate capture for emergencies (name/number/address), transfer, failure fallback, non-emergency collection, anything-else, close.
- No mention of function calls to callers.
- Transfer and transfer-fail protocols.

## n8n Setup (Free / Local)

1. Start n8n with Docker:

```bash
docker compose -f docker-compose.n8n.yml up -d
```

2. Open `http://localhost:5678`.
3. Import `workflows/n8n_clara_pipeline.json`.
4. Ensure the execute-command node runs from repo root so `python scripts/run_pipeline.py ...` resolves correctly.
5. Trigger workflow manually to process all dataset files.

Alternative:

- You can also run n8n desktop/local without Docker and import the same workflow.

## n8n Cloud Setup (No Docker)

If Docker is not available, you can use n8n Cloud trial and trigger this repo via GitHub Actions.

1. Push this repository to GitHub.
2. In GitHub, keep `.github/workflows/run_clara_pipeline.yml` in your default branch.
3. Create a GitHub Personal Access Token (classic) with `repo` and `workflow` scopes.
4. Open n8n Cloud and import one of:
   - `workflows/n8n_clara_pipeline_cloud.json` (minimal trigger flow)
   - `workflows/n8n_clara_pipeline_cloud_verbose.json` (multi-node visual flow)
   - `workflows/n8n_clara_pipeline_cloud_correct.json` (recommended: explicit input/output guidance)
   - `workflows/n8n_clara_pipeline_cloud_hybrid.json` (recommended visual: Wait + IF + Success/Still Running/Failed)
5. Import into a **new workflow** (not append into an existing canvas).
6. The first node should be `Start Here (Manual Trigger)`.
7. If you do not see it, use n8n canvas "Fit view" once.
8. Open the **Dispatch GitHub Action** node and replace:
   - `REPLACE_WITH_GITHUB_USERNAME`
   - `REPLACE_WITH_REPO_NAME`
   - `REPLACE_WITH_GITHUB_PAT`
9. Execute the workflow.
10. Check GitHub -> Actions -> **Run Clara Pipeline** for status.
11. Download artifact `clara-pipeline-outputs` from the completed run.

Note:
- n8n Cloud does not support local `Execute Command`, so local Python execution must happen through an external runner (GitHub Actions in this setup).

Input/Output in n8n Cloud:
- Input: update transcript files in GitHub under `data/demo/` and `data/onboarding/`, then run workflow.
- Output: open returned `run_url` and download artifact `clara-pipeline-outputs` (contains `outputs/` and `tracker/tasks.json`).

## Retell Setup Notes

If Retell API access is not available in free tier:

1. Open generated `agent_spec.json`.
2. Copy `system_prompt`, transfer protocol fields, and key variables into Retell UI manually.
3. Keep `v1` and `v2` specs as version-controlled source of truth.

## How To Plug In Real Dataset

1. Replace sample files in `data/demo` and `data/onboarding` with actual transcripts.
2. Keep filenames paired by shared account prefix.
3. Re-run pipeline command.
4. Review `outputs/accounts/*/questions_or_unknowns` for missing details.

## Known Limitations

- Extraction is rule-based, so unusual phrasing may reduce recall.
- Audio transcription is intentionally out of scope here (zero-cost transcript-first mode).
- n8n workflow export is intentionally minimal; extend with file watchers/webhooks if needed.

## Production Improvements

- Add robust NLP extraction model (still zero-cost local if feasible).
- Add JSON Schema validation step in pipeline.
- Add UI diff viewer for `v1` vs `v2`.
- Add alerting + retry queue for failed extractions.
