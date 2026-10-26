"""DSC integration by measured time; conservative QC and provenance."""
from __future__ import annotations
import numpy as np
import pandas as pd
from .schema import Config, InputError


def _integrate(frame: pd.DataFrame, fraction: float, baseline_method: str = "linear_endpoint_mean") -> dict:
    times = frame.time_s.to_numpy(dtype=float)
    heat = frame.heat_flow_mw.to_numpy(dtype=float)
    n = len(frame)
    endpoints = max(3, int(np.ceil(n * fraction)))
    if 2 * endpoints >= n:
        raise InputError("Not enough interior points to fit an endpoint baseline")
    left, right = float(np.mean(heat[:endpoints])), float(np.mean(heat[-endpoints:]))
    tl, tr = float(np.mean(times[:endpoints])), float(np.mean(times[-endpoints:]))
    if tr <= tl:
        raise InputError("Degenerate baseline timestamps")
    if baseline_method == "linear_endpoint_mean":
        baseline = left + (right - left) * (times - tl) / (tr - tl)
    elif baseline_method == "constant_endpoint_mean":
        baseline = np.full(len(times), (left + right) / 2.0, dtype=float)
    else:
        raise InputError(f"Unsupported baseline method: {baseline_method}")
    corrected = heat - baseline
    # mW * s = mJ. No scan-rate factor required when integrating over time.
    area_mj = float(np.trapezoid(corrected, times))
    return {"baseline": baseline, "corrected": corrected,
            "area_mj": area_mj, "endpoint_count": endpoints}


def analyze(df: pd.DataFrame, config: Config) -> tuple[list[dict], list[dict], dict]:
    by_sample = {s.sample_id: s for s in config.samples}
    events = []
    issues = []
    curves = {}
    for win in config.windows:
        sample = by_sample[win.sample_id]
        group = df[(df.sample_id == win.sample_id) & (df.segment == win.segment)]
        if group.empty:
            raise InputError(f"No raw segment for window {win.event_id}: {win.sample_id}/{win.segment}")
        frame = group[(group.temperature_c >= win.start_c) &
                      (group.temperature_c <= win.end_c)].copy()
        if len(frame) < 21:
            raise InputError(f"Fewer than 21 points in integration window: {win.event_id}")
        temp = frame.temperature_c.to_numpy(dtype=float)
        slope = float(np.median(np.diff(temp)))
        expected_increasing = win.phase != "crystallization"
        # Cold crystallization is an exothermic peak observed on heating.
        if (slope > 0) != expected_increasing or abs(slope) < 1e-9:
            issues.append({"severity": "FAIL", "code": "SCAN_DIRECTION",
                           "event_id": win.event_id, "message": "Scan direction inconsistent with phase"})
        core = _integrate(frame, config.baseline_fraction, win.baseline_method)
        corrected = core["corrected"] * (1 if sample.endotherm_up else -1)
        area_mj = core["area_mj"] * (1 if sample.endotherm_up else -1)
        is_endo = win.phase == "melting"
        peak_idx = int(np.argmax(corrected) if is_endo else np.argmin(corrected))
        peak_temp = float(frame.iloc[peak_idx].temperature_c)
        peak_mw = float(corrected[peak_idx])
        if is_endo != (area_mj > 0):
            issues.append({"severity": "FAIL", "code": "HEAT_FLOW_SIGN",
                           "event_id": win.event_id,
                           "message": "Integrated peak sign does not agree with phase/endotherm_up"})
        if abs(area_mj) < 1e-5 or abs(peak_mw) < 1e-5:
            issues.append({"severity": "FAIL", "code": "NO_DETECTABLE_PEAK", "event_id": win.event_id,
                           "message": "Window has no measurable peak after baseline subtraction"})
        if (peak_idx < 2) or (peak_idx >= len(frame) - 2):
            issues.append({"severity": "WARN", "code": "PEAK_AT_WINDOW_EDGE",
                           "event_id": win.event_id, "message": "Peak close to integration edge"})
        # Sensitivity is an empirical baseline-window check, not a calibrated uncertainty.
        sensitivity_vals = [_integrate(frame, f, win.baseline_method)["area_mj"] for f in (0.05, 0.10, 0.15)]
        sensitivity_pct = float(100 * (max(sensitivity_vals) - min(sensitivity_vals)) /
                                max(abs(area_mj), 1e-12))
        if sensitivity_pct > 25:
            issues.append({"severity": "FAIL", "code": "BASELINE_UNSTABLE",
                           "event_id": win.event_id,
                           "message": f"Baseline sensitivity {sensitivity_pct:.1f}% exceeds hard limit (25%)"})
        elif sensitivity_pct > 15:
            issues.append({"severity": "WARN", "code": "BASELINE_SENSITIVITY",
                           "event_id": win.event_id,
                           "message": f"Endpoint fraction variation changes area by {sensitivity_pct:.1f}% of nominal area"})
        if is_endo and sample.delta_h0_j_g is not None and not sample.reference_verified:
            issues.append({"severity": "WARN", "code": "REFERENCE_UNVERIFIED",
                           "event_id": win.event_id,
                           "message": "Reference heat of fusion is user-supplied but not verified"})
        curves[win.event_id] = {"frame": frame, "baseline": core["baseline"]}
        events.append({
            "event_id": win.event_id, "sample_id": win.sample_id, "polymer": sample.polymer,
            "segment": win.segment, "phase": win.phase,
            "window_c": [win.start_c, win.end_c],
            "peak_temperature_c": round(peak_temp, 4),
            "peak_corrected_mw_endotherm_up": round(peak_mw, 6),
            "integrated_area_mj_endotherm_up": round(area_mj, 6),
            "enthalpy_j_g": round(area_mj / sample.mass_mg, 6),
            "mass_mg": sample.mass_mg,
            "baseline_endpoint_count": core["endpoint_count"],
            "baseline_sensitivity_pct": round(sensitivity_pct, 4),
            "crystallinity_pct": None,
            "crystallinity_status": "not_applicable" if not is_endo else "pending_qualification",
            "method": win.baseline_method + "; trapezoidal time integration",
        })
    # Enthalpy convention: positive melt, negative crystallization/cold crystallization.
    for event in events:
        if event["phase"] != "melting":
            continue
        sample = by_sample[event["sample_id"]]
        if sample.delta_h0_j_g is None:
            event["crystallinity_status"] = "no_reference_heat_of_fusion"
            continue
        cc = [e for e in events if e["sample_id"] == event["sample_id"] and
              e["segment"] == event["segment"] and e["phase"] == "cold_crystallization"]
        if not cc and sample.cold_crystallization_excluded is not True:
            event["crystallinity_status"] = "cold_crystallization_not_assessed"
            issues.append({"severity":"WARN", "code":"COLD_CRYSTALLIZATION_UNKNOWN",
                           "event_id":event["event_id"], "message":"Crystallinity withheld: cold crystallization not explicitly assessed"})
            continue
        hcc = sum(abs(e["enthalpy_j_g"]) for e in cc)
        value = 100 * (event["enthalpy_j_g"] - hcc) / sample.delta_h0_j_g
        if value < -0.01 or value > 100.01:
            issues.append({"severity": "FAIL", "code": "UNPHYSICAL_CRYSTALLINITY",
                           "event_id": event["event_id"], "message": "Computed crystallinity outside [0,100]%"})
        event["crystallinity_pct"] = round(value, 4)
        event["crystallinity_status"] = ("computed_reference_verified" if sample.reference_verified else
                                         "computed_reference_unverified")
    if config.dataset_type == "synthetic":
        issues.append({"severity": "WARN", "code": "SYNTHETIC_DATA",
                       "event_id": None, "message": "Simulated fixture only; cannot be presented as measured results"})
    qc = {
        "numerical_status": "FAIL" if any(x["severity"] == "FAIL" for x in issues) else
                            ("WARN" if issues else "PASS"),
        "scientific_interpretation_status": "NOT_REVIEWED",
        "document_visual_qa_status": "NOT_REVIEWED",
        "issues": issues,
        "limitations": [
            "No automatic Tg/midpoint detection or calorimeter calibration",
            "No instrument-specific TXT parser or automated cycle segmentation",
            "Baseline sensitivity is not measurement uncertainty",
            "No verification of ΔH0 reference source unless user confirms it",
        ]
    }
    return events, issues, {"qc": qc, "curves": curves}
