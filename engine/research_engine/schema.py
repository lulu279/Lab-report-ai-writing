"""JSON configuration schema with conservative validation."""
from __future__ import annotations
from dataclasses import dataclass
import re
from typing import Any

PHASES = {"melting", "crystallization", "cold_crystallization"}
BASELINE_METHODS = {"linear_endpoint_mean", "constant_endpoint_mean"}


class InputError(ValueError):
    """Input does not meet the documented contract."""


@dataclass(frozen=True)
class Sample:
    sample_id: str
    polymer: str
    mass_mg: float
    endotherm_up: bool
    delta_h0_j_g: float | None
    delta_h0_reference: str | None
    reference_verified: bool
    cold_crystallization_excluded: bool | None


@dataclass(frozen=True)
class Window:
    event_id: str
    sample_id: str
    segment: str
    phase: str
    start_c: float
    end_c: float
    baseline_method: str = "linear_endpoint_mean"


@dataclass(frozen=True)
class Config:
    dataset_type: str
    dataset_label: str
    measurement_units: dict[str, str]
    samples: tuple[Sample, ...]
    windows: tuple[Window, ...]
    baseline_fraction: float


def _num(d: dict, name: str) -> float:
    try:
        v = float(d[name])
    except (KeyError, TypeError, ValueError) as e:
        raise InputError(f"Missing/invalid numeric field: {name}") from e
    import math
    if not math.isfinite(v):
        raise InputError(f"Non-finite number: {name}")
    return v


def _safe_id(value: str, field: str) -> str:
    # IDs also become filenames; do not allow traversal or filesystem control characters.
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", value):
        raise InputError(f"Unsafe {field}: use only A-Z, 0-9, underscore, hyphen")
    return value


def _text(d: dict, name: str) -> str:
    v = d.get(name)
    if not isinstance(v, str) or not v.strip():
        raise InputError(f"Missing/invalid text field: {name}")
    return v.strip()


def parse_config(raw: Any, require_windows: bool = True) -> Config:
    if not isinstance(raw, dict):
        raise InputError("Configuration root must be a JSON object")
    typ = _text(raw, "dataset_type")
    if typ not in {"synthetic", "experimental"}:
        raise InputError("dataset_type must be 'synthetic' or 'experimental'")
    units = raw.get("measurement_units")
    if units != {"time_s": "s", "temperature_c": "degC", "heat_flow_mw": "mW"}:
        raise InputError("measurement_units must explicitly specify s, degC and mW. No guessing or conversion.")
    out_samples = []
    sample_ids = set()
    for d in raw.get("samples", []):
        if not isinstance(d, dict):
            raise InputError("Each sample must be an object")
        sid = _safe_id(_text(d, "sample_id"), "sample_id")
        if sid in sample_ids:
            raise InputError(f"Duplicate sample: {sid}")
        sample_ids.add(sid)
        mass = _num(d, "mass_mg")
        if mass <= 0:
            raise InputError(f"Mass must be positive for {sid}")
        if type(d.get("endotherm_up")) is not bool:
            raise InputError(f"endotherm_up must be explicit Boolean for {sid}")
        h0 = d.get("delta_h0_j_g")
        if h0 is not None:
            h0 = _num(d, "delta_h0_j_g")
            if h0 <= 0:
                raise InputError("delta_h0_j_g must be positive")
        verified = d.get("reference_verified", False)
        if type(verified) is not bool:
            raise InputError("reference_verified must be Boolean")
        cc = d.get("cold_crystallization_excluded", None)
        if cc is not None and type(cc) is not bool:
            raise InputError("cold_crystallization_excluded must be Boolean or null")
        out_samples.append(Sample(sid, _text(d,"polymer"), mass, d["endotherm_up"],
                                  h0, d.get("delta_h0_reference"), verified, cc))
    if not out_samples:
        raise InputError("At least one sample required")
    out_windows = []
    event_ids = set()
    for d in raw.get("windows", []):
        if not isinstance(d, dict):
            raise InputError("Each window must be an object")
        event = _safe_id(_text(d, "event_id"), "event_id")
        if event in event_ids:
            raise InputError(f"Duplicate event_id: {event}")
        event_ids.add(event)
        sid = _safe_id(_text(d, "sample_id"), "sample_id")
        if sid not in sample_ids:
            raise InputError(f"Unknown sample_id in window: {sid}")
        kind = _text(d, "phase")
        if kind not in PHASES:
            raise InputError(f"Unknown phase {kind}")
        start, end = _num(d, "start_c"), _num(d, "end_c")
        if start >= end:
            raise InputError(f"Window needs start_c < end_c: {event}")
        baseline = d.get("baseline_method", "linear_endpoint_mean")
        if baseline not in BASELINE_METHODS:
            raise InputError(f"Unsupported baseline_method for {event}: {baseline}")
        out_windows.append(Window(event,sid,_safe_id(_text(d,"segment"),"segment"),kind,start,end,baseline))
    if not out_windows and require_windows:
        raise InputError("At least one explicit temperature window required")
    baseline_fraction = float(raw.get("baseline_fraction", 0.1))
    if not (0.03 <= baseline_fraction <= 0.20):
        raise InputError("baseline_fraction outside [0.03,0.20]")
    return Config(typ, str(raw.get("dataset_label", "Untitled")), units,
                  tuple(out_samples), tuple(out_windows), baseline_fraction)
