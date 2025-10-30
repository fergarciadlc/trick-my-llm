# trick-my-llm

This is a small, reproducible pipeline to test whether LLMs follow **provided context** over their **training priors**,
and whether they return **exactly** the answer we requested.

## Key Features
- **Prompts as files** with the expected answer embedded inline (Option 2 format).
- **Config-driven** orchestration: models + scenarios in `configs/experiment.yaml`.
- **OpenAI-compatible** client (e.g., Groq) using HTTPX + retries.
- **Deterministic by default**: temperature=0; optional seed when supported.
- **Auto-scoring**: parses `Expected Answer` and compares literal final string.
- **Outputs**: timestamped JSONL + CSV summaries.

## Folder Structure
```
project/
  README.md
  requirements.txt
  configs/
    experiment.yaml
  prompts/
    system__use_provided_data_only.md
    scenarios/
      user__contradictory_table.md.j2
      user__two_sources_hierarchy.md.j2
      user__recompute_mean.md.j2
      user__custom_units.md.j2
  src/
    core/
      client.py
      prompts.py
      runner.py
      io.py
    runners/
      run_experiment.py
  outputs/                # created automatically
  analysis/
    quicklook.ipynb
```

## Prompt File Format (MANDATORY)

Each prompt file MUST follow this exact layout:

```
Expected Answer: <the single canonical output string>
---
Prompt:
<the exact user-visible prompt to send to the model>
```

Parsing is trivial and whitespace-insensitive. No extra sections.

## Good Practices
- **Separation of concerns:** prompts (content), configs (what to run), src (code), outputs (results).
- **Reproducibility:** temperature=0, fix any randomization, set seed if available.
- **Idempotence:** create a new timestamped `outputs/<run>/` on every run.
- **Observability:** log latency, token usage, model params, and finish_reason.
- **Literal scoring:** expected answer is compared to the model final string after `.strip()` ONLY.

## Requirements
```
pip install -r requirements.txt
```
Set your key:
```
export GROQ_API_KEY=sk-...   # macOS/Linux
# $Env:GROQ_API_KEY="sk-..." # Windows PowerShell
```

## Run
```
python -m src.runners.run_experiment --config configs/experiment.yaml
```

Open `analysis/quicklook.ipynb` to browse the latest CSV summary.
