import time
from dataclasses import dataclass
from typing import Dict, Any, List
from pathlib import Path
import yaml
from tqdm import tqdm  # Added for progress bars

from .prompts import render_prompts
from .client import LLMClient, build_payload
from .io import make_output_dir, write_jsonl, write_csv

@dataclass
class Scenario:
    id: str
    system_prompt: str
    user_prompt_template: str

@dataclass
class ModelSpec:
    name: str
    provider: str
    model_params: Dict[str, Any]

@dataclass
class ExperimentConfig:
    base_url: str
    api_key_env: str
    models: List[ModelSpec]
    defaults: Dict[str, Any]
    replications: int
    scenarios: List[Scenario]

def load_config(path: str) -> ExperimentConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    models = [ModelSpec(**m) for m in raw["models"]]
    scenarios = [Scenario(**s) for s in raw["scenarios"]]
    return ExperimentConfig(
        base_url=raw["base_url"],
        api_key_env=raw["api_key_env"],
        models=models,
        defaults=raw.get("defaults", {}),
        replications=raw.get("replications", 1),
        scenarios=scenarios,
    )

def run_experiment(cfg: ExperimentConfig) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    client = LLMClient(base_url=cfg.base_url, api_key_env=cfg.api_key_env, timeout_s=cfg.defaults.get("timeout_s", 60))
    
    # Rate limiting: delay between requests (configurable, default 1 second)
    request_delay = cfg.defaults.get("request_delay_s", 1.0)

    for scenario in tqdm(cfg.scenarios, desc="Scenarios", unit="scenario"):
        for rep in range(cfg.replications):
            rendered = render_prompts(scenario.system_prompt, scenario.user_prompt_template, variables=None)

            for model in tqdm(cfg.models, desc=f"Models (Scenario {scenario.id}, Rep {rep+1})", unit="model", leave=False):
                mp = {**cfg.defaults, **(model.model_params or {})}
                payload = build_payload(model=model.name, system=rendered.system, user=rendered.user, model_params=mp)

                t0 = time.time()
                error = None
                content = ""
                try:
                    resp = client.chat_completions(payload)
                    latency_s = time.time() - t0
                    choice = resp.get("choices", [{}])[0]
                    content = (choice.get("message", {}) or {}).get("content", "") or ""
                    finish_reason = choice.get("finish_reason", "")
                    usage = resp.get("usage", {})

                except Exception as e:
                    latency_s = time.time() - t0
                    finish_reason = "error"
                    usage = {}
                    error = str(e)
                    print(f"Error during request: {e}, scenario: {scenario.id}, model: {model.name}, rep: {rep+1}")

                # scoring (literal match after strip)
                expected = rendered.expected_answer.strip() if rendered.expected_answer else None
                response_stripped = content.strip()
                is_correct = (expected is not None and response_stripped == expected)

                rows.append({
                    "scenario_id": scenario.id,
                    "rep": rep,
                    "model": model.name,
                    "provider": model.provider,
                    "temperature": mp.get("temperature"),
                    "max_tokens": mp.get("max_tokens"),
                    "top_p": mp.get("top_p"),
                    "seed": mp.get("seed"),
                    "latency_s": round(latency_s, 3),
                    "finish_reason": finish_reason,
                    "prompt_system": rendered.system,
                    "prompt_user": rendered.user,
                    "expected_answer": expected,
                    "response": content,
                    "is_correct": is_correct,
                    "usage_prompt_tokens": usage.get("prompt_tokens"),
                    "usage_completion_tokens": usage.get("completion_tokens"),
                    "usage_total_tokens": usage.get("total_tokens"),
                    "error": error,
                })
                
                # Add delay between requests to avoid rate limiting
                if request_delay > 0:
                    time.sleep(request_delay)

    return rows

def save_outputs(rows: List[Dict[str, Any]]):
    outdir = make_output_dir()
    write_jsonl(outdir / "results.jsonl", rows)

    # CSV summary
    summary = []
    for r in rows:
        preview = None
        if r.get("response"):
            txt = r["response"]
            preview = (txt[:120] + "...") if len(txt) > 120 else txt
        summary.append({
            "scenario_id": r.get("scenario_id"),
            "rep": r.get("rep"),
            "model": r.get("model"),
            "latency_s": r.get("latency_s"),
            "is_correct": r.get("is_correct"),
            "expected_answer": r.get("expected_answer"),
            "response_preview": preview,
            "error": r.get("error"),
        })
    write_csv(outdir / "summary.csv", summary)
    return outdir
