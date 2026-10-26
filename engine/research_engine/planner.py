"""LLM-guided DSC analysis method planning: proposals are never executable code.

Only intentionally small, metadata+downsampled curves leave the local computer when
user explicitly requests API planning. No model call is made during tests.
"""
from __future__ import annotations
import copy
import json
import os
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from .schema import parse_config, InputError, BASELINE_METHODS
from .loader import parse_csv
from .pipeline import load_config
from .formula_registry import public_catalog

METHOD_CATALOG = {
    "dsc_peak_area_time_v1": {
        "status": "implemented",
        "equation": "ΔH [J/g] = ∫(heat_flow_mW − baseline_mW) dt[s] / mass_mg; mW·s=mJ",
        "phases": ["melting", "crystallization", "cold_crystallization"],
        "baselines": sorted(BASELINE_METHODS),
        "assumptions": ["heat flow mW and time seconds calibrated", "sample mass known", "one resolvable transition", "integration window contains peak and baselines"],
    },
    "dsc_tg_midpoint_v1": {
        "status": "NOT_IMPLEMENTED",
        "equation": "Tg by extrapolated baseline and step midpoint",
        "phases": ["glass_transition"],
        "baselines": [],
    },
}


def load_planning_inputs(data_path: Path, config_path: Path) -> tuple[pd.DataFrame, dict]:
    config_raw = load_config(Path(config_path))
    if "windows" not in config_raw:
        config_raw["windows"] = []
    config_obj = parse_config(config_raw, require_windows=False)
    df = parse_csv(Path(data_path), config_obj)
    return df, config_raw


def data_profile(df: pd.DataFrame, config: dict, n_preview: int = 32) -> dict:
    """Use sparse binned means for model review; never send complete raw curves by default."""
    if n_preview < 8 or n_preview > 48:
        raise InputError("Preview count must be between 8 and 48")
    segments = []
    for (sid, seg), sub in df.groupby(["sample_id", "segment"], sort=False):
        arr_t = sub.temperature_c.to_numpy(dtype=float)
        arr_y = sub.heat_flow_mw.to_numpy(dtype=float)
        parts = np.array_split(np.arange(len(sub)), min(n_preview, len(sub)))
        curve_preview = [
            [round(float(np.mean(arr_t[p])), 3), round(float(np.mean(arr_y[p])), 5)] for p in parts
        ]
        increments = np.diff(arr_t)
        segments.append({
            "sample_id": sid, "segment": seg, "n_points": len(sub),
            "temperature_min_c": round(float(arr_t.min()), 3),
            "temperature_max_c": round(float(arr_t.max()), 3),
            "temperature_direction": "heating" if np.median(increments)>0 else "cooling",
            "heat_flow_min_mw": round(float(arr_y.min()), 4),
            "heat_flow_max_mw": round(float(arr_y.max()), 4),
            "temperature_heat_flow_preview": curve_preview,
            "preview_description": "[mean measured temperature °C, mean heat flow mW] in sequential time bins; approximate, not full-resolution peak positions",
        })
    return {
        "dataset_type": config["dataset_type"],
        "dataset_label": config.get("dataset_label"),
        "measurement_units": config["measurement_units"],
        "samples": config["samples"],
        "segments": segments,
        "existing_windows_are_reference_only": bool(config.get("windows")),
        "existing_windows": config.get("windows", []),
        "supported_methods": METHOD_CATALOG,
        "reference_formulas_not_event_executors": [
            {"id": m["id"], "equation": m["equation"], "status": m["status"]}
            for m in public_catalog("DSC")
        ],
        "raw_data_sent": False,
    }

SYSTEM_INSTRUCTIONS = """You are a DSC analytical method PLANNER, not a numerical calculator.
Propose an analysis plan from the supplied metadata and sampled signal overview.
Do NOT fabricate peaks, invent physical constants, alter sample metadata, or claim that a result is verified.
Some reference formula cards are provided for physical context only. Their IDs are NOT eligible as event method_id.
Supported executable event algorithm ONLY: dsc_peak_area_time_v1 with baseline_method either
linear_endpoint_mean or constant_endpoint_mean. Formula is specified in method catalog.
Identify candidate windows that include full transitions AND useful pre/post transition baselines.
Temperature window start_c < end_c ALWAYS, even for cooling segments.
melting must occur on heating and have endothermic signal; crystallization cooling exothermic;
cold_crystallization heating exothermic. If ambiguous, DO NOT create a false event.
For unresolved Tg steps, subtle overlap, or unsupported methods use deferred_events and describe why.
Prefer physical plausibility and uncertainty disclosure over forced event detection.
Do not compute crystallinity unless metadata already provides appropriate verified reference and
cold crystallization has been assessed; leave original metadata unchanged.
Reply with a SINGLE JSON OBJECT, without markdown fences, according to the schema:
{
  "plan_version":"0.2", "experiment_type":"DSC", "baseline_fraction":0.1,
  "events":[{"event_id":"ASCII_safe_unique", "sample_id":"...", "segment":"...",
             "phase":"melting|crystallization|cold_crystallization", "method_id":"dsc_peak_area_time_v1",
             "baseline_method":"linear_endpoint_mean|constant_endpoint_mean",
             "start_c": 0, "end_c":100, "confidence":0.8,
             "reason":"why this formula and baseline are appropriate",
             "evidence":"observable signal evidence, not a claim of quantitative validation"}],
  "deferred_events":[{"sample_id":"...", "segment":"...", "suggested_method_id":"...", "reason":"..."}],
  "questions_for_user":["..."], "general_limitations":["..."]
}
The JSON response is an UNTRUSTED proposal. All output is subject to local schema checks,
method allowlisting, numeric tests and explicit user approval before any computation.
"""


def _strip_json(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[-1].strip()=="```":
            text = "\n".join(lines[1:-1]).strip()
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise InputError("Model must return one JSON object")
    return obj


def request_ai_plan(profile: dict, model: str, base_url: str | None = None) -> tuple[dict,dict]:
    """Calls an optional OpenAI-compatible endpoint. No default model or key."""
    if not model or not model.strip():
        raise InputError("Model ID must be specified explicitly")
    secret = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not secret:
        raise InputError("Set AI_API_KEY or OPENAI_API_KEY to enable genuine AI planning")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install optional AI dependency: pip install -r requirements-ai.txt") from exc
    opts = {"api_key": secret, "timeout": 90.0}
    base_url = base_url or os.getenv("AI_BASE_URL")
    if base_url:
        if not (base_url.startswith("https://") or base_url.startswith("http://localhost:") or base_url.startswith("http://127.0.0.1:")):
            raise InputError("API base_url must be HTTPS or localhost")
        opts["base_url"] = base_url
    client = OpenAI(**opts)
    response = client.chat.completions.create(
        model=model,
        messages=[{"role":"system", "content": SYSTEM_INSTRUCTIONS},
                  {"role":"user", "content": json.dumps(profile,ensure_ascii=False)}],
        temperature=0,
    )
    content = response.choices[0].message.content
    if not content:
        raise InputError("Model returned empty proposal")
    metadata = {"model_requested":model,"base_url":base_url or "OpenAI SDK default", "api_invoked":True}
    return _strip_json(content), metadata


def _text(d:dict, field:str, minlen:int=1) -> str:
    value=d.get(field)
    if not isinstance(value,str) or len(value.strip())<minlen:
        raise InputError(f"Invalid plan field {field}")
    return value.strip()


def validate_ai_plan(plan:dict,df:pd.DataFrame,config_raw:dict) -> tuple[dict,list[dict]]:
    """Reject unknown methods, unsupported formulae, incompatible segments and invented metadata.

    Raises InputError for any structurally invalid proposal. Warnings must be reviewed manually.
    """
    if not isinstance(plan,dict) or plan.get("plan_version")!="0.2" or plan.get("experiment_type")!="DSC":
        raise InputError("Unexpected AI plan schema/version or experiment type")
    events=plan.get("events")
    if not isinstance(events,list) or not events or len(events)>100:
        raise InputError("AI plan needs 1–100 candidate events; no executable events means stop for manual review")
    deferred=plan.get("deferred_events",[])
    if not isinstance(deferred,list):
        raise InputError("deferred_events must be list")
    warnings=[]
    known_samples={x["sample_id"]:x for x in config_raw["samples"]}
    known_segments={(str(s),str(g)) for s,g in df[["sample_id","segment"]].itertuples(index=False,name=None)}
    safe_id=__import__('re').compile(r'^[A-Za-z0-9_\-]+$')
    mapped=[]
    ids=set()
    for event in events:
        if not isinstance(event,dict):
            raise InputError("Invalid event object")
        eid=_text(event,"event_id")
        if not safe_id.fullmatch(eid) or eid in ids:
            raise InputError(f"Duplicate or unsafe event ID: {eid}")
        ids.add(eid)
        sid=_text(event,"sample_id"); seg=_text(event,"segment")
        phase=_text(event,"phase")
        if sid not in known_samples or (sid,seg) not in known_segments:
            raise InputError(f"Hallucinated sample/segment in plan: {sid}/{seg}")
        method=_text(event,"method_id")
        if method!="dsc_peak_area_time_v1":
            raise InputError(f"Unsupported algorithm {method}. Must defer, not execute")
        baseline=_text(event,"baseline_method")
        if baseline not in BASELINE_METHODS:
            raise InputError(f"Unsupported baseline model {baseline}")
        if phase not in METHOD_CATALOG[method]["phases"]:
            raise InputError(f"Unsupported phase {phase}")
        try:
            start=float(event["start_c"]); end=float(event["end_c"])
            confidence=float(event["confidence"])
        except (TypeError,KeyError,ValueError) as exc:
            raise InputError("Non-numeric plan window or confidence") from exc
        if not (np.isfinite([start,end,confidence]).all() and start<end and 0<=confidence<=1):
            raise InputError("Invalid plan temperature window or confidence")
        _text(event,"reason",8);_text(event,"evidence",8)
        if confidence<0.80:
            warnings.append({"severity":"REVIEW", "code":"LOW_MODEL_CONFIDENCE", "event_id":eid,
                             "message":f"Model confidence {confidence:.2f} below 0.80; human review required"})
        sub=df[(df.sample_id==sid)&(df.segment==seg)]
        scan=sub[(sub.temperature_c>=start)&(sub.temperature_c<=end)]
        if len(scan)<21:
            raise InputError(f"Window does not contain at least 21 points: {eid}")
        direction=float(np.median(np.diff(sub.temperature_c.to_numpy(dtype=float))))
        if (phase=="crystallization" and direction>=0) or (phase!="crystallization" and direction<=0):
            raise InputError(f"Phase does not match scan direction: {eid}")
        if start < float(sub.temperature_c.min()) or end > float(sub.temperature_c.max()):
            raise InputError(f"Window outside recorded temperatures: {eid}")
        mapped.append({"event_id":eid,"sample_id":sid,"segment":seg,"phase":phase,
                       "start_c":start,"end_c":end,"baseline_method":baseline})
    frac=plan.get("baseline_fraction",0.1)
    if isinstance(frac,bool):
        raise InputError("Invalid baseline fraction")
    try:
        frac=float(frac)
    except (TypeError,ValueError) as exc:
        raise InputError("Invalid baseline fraction") from exc
    if not (0.03<=frac<=0.20):
        raise InputError("AI proposed baseline fraction outside supported range")
    covered={(ev["sample_id"],ev["segment"]) for ev in mapped}
    for sid,seg in sorted(known_segments-covered):
        if not any(isinstance(x,dict) and x.get('sample_id')==sid and x.get('segment')==seg for x in deferred):
            warnings.append({"severity":"REVIEW","code":"UNCOVERED_SEGMENT","event_id":None,
                             "message":f"No proposed event or explicit deferral for {sid}/{seg}"})
    candidate=copy.deepcopy(config_raw)
    candidate["windows"]=mapped
    candidate["baseline_fraction"]=frac
    parse_config(candidate)
    return candidate,warnings


def preview_ai_plan(data_path: Path, config_path: Path, *, model: str,
                    base_url: str|None=None) -> dict:
    """Call external AI once; validate output; return preview only (does not execute)."""
    df, raw=load_planning_inputs(data_path,config_path)
    profile=data_profile(df,raw)
    proposal,api_metadata=request_ai_plan(profile,model,base_url)
    candidate,warnings=validate_ai_plan(proposal,df,raw)
    return {"proposal":proposal,"candidate_config":candidate,"local_warnings":warnings,
            "api_metadata":api_metadata,"profile_sent":profile,
            "human_approval_required":True,"executed":False}
