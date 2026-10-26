"""Auditable formula registry with validated local executors.

No untrusted expression evaluation or model-generated Python is permitted. An LLM
may *propose* a method ID and input bindings; execution requires schema checks
and (in the research GUI) explicit operator approval.

This registry is independent of the DSC report pipeline. Registering a formula
here does not automatically certify its use for a given experiment.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np

REGISTRY_PATH = Path(__file__).resolve().parents[1] / 'method_registry' / 'catalog.json'


class FormulaError(ValueError):
    """Unsafe, incomplete or out-of-domain formula request."""


def load_registry() -> dict[str, dict]:
    records = json.loads(REGISTRY_PATH.read_text(encoding='utf-8'))
    if not isinstance(records, list):
        raise FormulaError('Registry content must be a list')
    ids = [r.get('id') for r in records]
    if len(ids) != len(set(ids)):
        raise FormulaError('Duplicate method ID')
    return {r['id']: r for r in records}


def public_catalog(experiment: str | None = None) -> list[dict]:
    methods = list(load_registry().values())
    if experiment:
        exp = experiment.strip().upper()
        methods = [m for m in methods if exp in m['experiments']]
    return methods


def _finite_number(args: dict, key: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    obj = args.get(key)
    if isinstance(obj, bool) or not isinstance(obj, (int, float)):
        raise FormulaError(f'{key} must be a numeric scalar')
    v = float(obj)
    if not np.isfinite(v):
        raise FormulaError(f'{key} must be finite')
    if positive and v <= 0:
        raise FormulaError(f'{key} must be > 0')
    if nonnegative and v < 0:
        raise FormulaError(f'{key} must be >= 0')
    return v


def _series(args: dict, key: str, minimum: int = 2) -> np.ndarray:
    arr = args.get(key)
    if not isinstance(arr, list) or len(arr) < minimum:
        raise FormulaError(f'{key} must be an array of {minimum}+ values')
    if any(isinstance(x, bool) for x in arr):
        raise FormulaError(f'{key} contains boolean values')
    try:
        n = np.asarray(arr, dtype=float)
    except (ValueError, TypeError) as e:
        raise FormulaError(f'{key} must contain numeric values') from e
    if n.ndim != 1 or not np.all(np.isfinite(n)):
        raise FormulaError(f'{key} must be a finite 1-D numeric array')
    return n


def _paired(args: dict, x: str, y: str, *, minimum: int = 2):
    xa = _series(args, x, minimum=minimum)
    ya = _series(args, y, minimum=minimum)
    if xa.size != ya.size:
        raise FormulaError('Paired arrays must have equal lengths')
    return xa, ya


def _strict_increasing(x: np.ndarray, name: str):
    if not np.all(np.diff(x) > 0):
        raise FormulaError(f'{name} must be strictly increasing')


def _monotonic(x: np.ndarray, name: str):
    delta = np.diff(x)
    if not (np.all(delta > 0) or np.all(delta < 0)):
        raise FormulaError(f'{name} must be strictly monotonic')


def _result(value: float | dict[str, float], unit: str, interpretation: str, caution: str = '') -> dict:
    if isinstance(value, dict):
        vals = {k: float(v) for k, v in value.items()}
        if not all(np.isfinite(v) for v in vals.values()):
            raise FormulaError('Result contains NaN or infinity')
    else:
        vals = float(value)
        if not np.isfinite(vals):
            raise FormulaError('Result is not finite')
    return {'value': vals, 'unit': unit, 'interpretation': interpretation, 'caution': caution}


def _dsc_enthalpy_time(a: dict) -> dict:
    time_s, heat = _paired(a, 'time_s', 'heat_flow_mw')
    baseline = _series(a, 'baseline_mw')
    if baseline.size != heat.size:
        raise FormulaError('baseline_mw length must match heat_flow_mw')
    _strict_increasing(time_s, 'time_s')
    mass_mg = _finite_number(a, 'sample_mass_mg', positive=True)
    # 1 mW*s = 1 mJ, and 1 mJ/mg = 1 J/g numerically.
    signed = float(np.trapezoid(heat - baseline, time_s) / mass_mg)
    return _result(signed, 'J/g', 'Signed specific DSC transition enthalpy.',
                   'Sign follows raw heat-flow convention; peak window and baseline require review.')


def _dsc_enthalpy_temperature(a: dict) -> dict:
    temp, heat = _paired(a, 'temperature_c', 'heat_flow_mw')
    base = _series(a, 'baseline_mw')
    if base.size != heat.size:
        raise FormulaError('baseline_mw length must match heat_flow_mw')
    _monotonic(temp, 'temperature_c')
    rate = _finite_number(a, 'scan_rate_k_min', positive=True)
    mass = _finite_number(a, 'sample_mass_mg', positive=True)
    # Along acquisition order: dt = |dT| / rate * 60 s/min.
    # Trapezoid with ascending positive cumulative time avoids reversing cooling sign.
    elapsed = np.r_[0.0, np.cumsum(np.abs(np.diff(temp)) / rate * 60.0)]
    signed = float(np.trapezoid(heat - base, elapsed) / mass)
    return _result(signed, 'J/g', 'Signed enthalpy from constant-rate temperature scan.',
                   'Requires genuinely constant scan rate; validate direction and peak baseline.')


def _dsc_crystallinity(a: dict) -> dict:
    hm = _finite_number(a, 'melting_enthalpy_j_g', nonnegative=True)
    hcc = _finite_number(a, 'cold_crystallization_enthalpy_j_g', nonnegative=True)
    h0 = _finite_number(a, 'reference_enthalpy_j_g', positive=True)
    filler = _finite_number(a, 'filler_mass_fraction', nonnegative=True)
    if not filler < 1:
        raise FormulaError('filler_mass_fraction must be < 1')
    if hm < hcc:
        raise FormulaError('melting_enthalpy_j_g is less than cold_crystallization_enthalpy_j_g; review phase/event classification')
    xc = 100.0 * (hm - hcc) / ((1.0 - filler) * h0)
    if xc > 100 + 1e-8:
        raise FormulaError('Calculated Xc >100%: inspect inputs/reference/corrections')
    return _result(xc, '%', 'Estimated initial crystalline mass fraction of polymer.',
                   'H_m and H_cc are positive magnitudes. Reference must suit polymer and conditions; '
                   'filler correction assumes stated polymer mass fraction.')


def _tga_mass_loss(a: dict) -> dict:
    init = _finite_number(a, 'initial_mass_mg', positive=True)
    final = _finite_number(a, 'final_mass_mg', nonnegative=True)
    if final > init:
        raise FormulaError('final_mass_mg exceeds initial_mass_mg: mass gain needs a different model')
    return _result(100.0*(init-final)/init, '%', 'Mass loss relative to declared initial mass.',
                   'Confirm initial mass after any moisture/tare normalization; mass gain is not supported.')


def _tga_t_at_loss(a: dict) -> dict:
    temp, retained = _paired(a, 'temperature_c', 'remaining_mass_percent')
    _strict_increasing(temp, 'temperature_c')
    if np.any((retained < -1e-8) | (retained > 100 + 1e-8)):
        raise FormulaError('remaining_mass_percent should lie in [0,100]')
    loss = _finite_number(a, 'mass_loss_target_percent', positive=True)
    if loss >= 100:
        raise FormulaError('mass_loss_target_percent must be <100')
    threshold = 100.0 - loss
    if retained[0] <= threshold:
        raise FormulaError('Threshold already reached at first data point; onset temperature cannot be inferred')
    crossings = np.flatnonzero(retained <= threshold)
    if crossings.size == 0:
        raise FormulaError('Requested mass loss not reached in measurement range')
    idx = int(crossings[0])
    left_m, right_m = float(retained[idx-1]), float(retained[idx])
    left_t, right_t = float(temp[idx-1]), float(temp[idx])
    frac = (left_m - threshold) / (left_m - right_m)
    found = left_t + frac*(right_t-left_t)
    return _result(found, 'degC', f'Temperature at first {loss:g}% initial mass loss.',
                   'First-crossing interpolation assumes correct normalization. Noise or multiple steps '
                   'may need smoothing and documented method selection.')


def _uv_beer_lambert(a: dict) -> dict:
    absorbance = _finite_number(a, 'absorbance', nonnegative=True)
    e = _finite_number(a, 'epsilon_l_mol_cm', positive=True)
    length = _finite_number(a, 'path_length_cm', positive=True)
    return _result(absorbance/(e*length), 'mol/L', 'Concentration from A = epsilon*l*c.',
                   'Requires a blank-corrected, non-scattering, linear, specified-wavelength system.')


def _ftir_transmittance(a: dict) -> dict:
    fraction = _finite_number(a, 'transmittance_fraction', positive=True)
    if fraction > 1:
        raise FormulaError('Transmittance >1: inspect blank/baseline; this basic formula expects T<=1')
    return _result(-float(np.log10(fraction)), 'dimensionless', 'Absorbance A = -log10(T).',
                   'T must be a fraction in (0,1], not a percent value (e.g. 80% = 0.80).')


def _gpc_from_mass_fractions(a: dict) -> dict:
    masses, fractions = _paired(a,'molar_mass_g_mol','mass_fraction',minimum=2)
    if np.any(masses <= 0) or np.any(fractions < 0):
        raise FormulaError('All molar masses >0, all mass fractions >=0 are required')
    s = float(fractions.sum())
    if not np.isclose(s,1.0,rtol=0,atol=1e-6):
        raise FormulaError('mass_fraction must already sum to 1; do not silently normalize unknown detector weights')
    mn = float(1.0/np.sum(fractions/masses))
    mw = float(np.sum(fractions*masses))
    return _result({'Mn_g_mol':mn,'Mw_g_mol':mw,'dispersity':mw/mn}, 'mixed: g/mol, g/mol, dimensionless',
                   'Distribution moments from genuine mass fractions.',
                   'Do not use raw RI/UV chromatogram areas as mass fractions without detector and calibration validation.')


def _nmr_normalized_ratio(a: dict) -> dict:
    ia = _finite_number(a, 'integral_a', nonnegative=True)
    ib = _finite_number(a, 'integral_b', positive=True)
    na = _finite_number(a, 'protons_a', positive=True)
    nb = _finite_number(a, 'protons_b', positive=True)
    return _result((ia/na)/(ib/nb), 'dimensionless', 'Mole ratio of groups A/B based on resolved 1H signals.',
                   'Requires valid integration, assignments, acquisition conditions and no interference.')


_EXECUTORS = {
    'dsc_enthalpy_time_v1':_dsc_enthalpy_time,
    'dsc_enthalpy_temperature_v1':_dsc_enthalpy_temperature,
    'dsc_crystallinity_v1':_dsc_crystallinity,
    'tga_mass_loss_v1':_tga_mass_loss,
    'tga_t_at_loss_v1':_tga_t_at_loss,
    'uv_beer_lambert_v1':_uv_beer_lambert,
    'ftir_transmittance_v1':_ftir_transmittance,
    'gpc_mass_moments_v1':_gpc_from_mass_fractions,
    'nmr_integral_ratio_v1':_nmr_normalized_ratio,
}


def execute_formula(method_id: str, parameters: dict[str, Any]) -> dict:
    """Execute allowlisted method only, without eval, exec, Python strings or hidden unit conversion."""
    catalog = load_registry()
    if method_id not in catalog:
        raise FormulaError(f'Unknown method: {method_id}')
    item = catalog[method_id]
    if item['status'] != 'tested_executor' or method_id not in _EXECUTORS:
        raise FormulaError(f'Method {method_id} is catalog-only; not executable')
    if not isinstance(parameters, dict):
        raise FormulaError('parameters must be a JSON object')
    # Exact key matching makes stale or hallucinated parameters conspicuous.
    expected = set(item['inputs'])
    if set(parameters) != expected:
        raise FormulaError(f'Input keys mismatch. Expected {sorted(expected)}; received {sorted(parameters)}')
    result = _EXECUTORS[method_id](parameters)
    return {'method_id':method_id, 'method_version':item['version'],
            'status':'CALCULATED_NOT_SCIENTIFICALLY_VALIDATED',
            'assumptions':item['assumptions'], 'result':result,
            'inputs':parameters, 'reference':item['reference']}
