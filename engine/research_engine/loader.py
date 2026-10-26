"""CSV validation: no silent column/unit/phase inference."""
import pandas as pd
import numpy as np
from .schema import Config, InputError

COLUMNS = ["sample_id", "segment", "time_s", "temperature_c", "heat_flow_mw"]


def parse_csv(path, config: Config) -> pd.DataFrame:
    try:
        df = pd.read_csv(path, encoding="utf-8-sig")
    except Exception as exc:
        raise InputError(f"Cannot read UTF-8 CSV: {exc}") from exc
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise InputError(f"Missing required CSV columns: {sorted(missing)}")
    df = df[COLUMNS].copy()
    if df.isnull().any().any():
        raise InputError("Missing values detected; repair explicitly before analysis")
    for key in ["time_s", "temperature_c", "heat_flow_mw"]:
        df[key] = pd.to_numeric(df[key], errors="coerce")
        if not np.isfinite(df[key].to_numpy(dtype=float)).all():
            raise InputError(f"Column {key} has nonnumeric or non-finite values")
    for key in ["sample_id", "segment"]:
        if not df[key].map(lambda x: isinstance(x, str) and bool(x.strip())).all():
            raise InputError(f"Invalid values in {key}")
    expected_samples = {s.sample_id for s in config.samples}
    if set(df.sample_id) - expected_samples:
        raise InputError("CSV has sample_id absent from configuration")
    if df.duplicated(["sample_id", "segment", "time_s"]).any():
        raise InputError("Duplicate time_s within a sample/segment")
    for (sid, seg), group in df.groupby(["sample_id", "segment"], sort=False):
        if len(group) < 15:
            raise InputError(f"Too few points in {sid}/{seg}: min 15")
        if not (np.diff(group.time_s.to_numpy(dtype=float)) > 0).all():
            raise InputError(f"Time is not strictly increasing in input order: {sid}/{seg}")
    return df
