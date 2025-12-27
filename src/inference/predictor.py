from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import importlib.util

import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from src.analysis.python_analyzer import PythonCodeAnalyzer


DEFAULT_MODEL_PATH = Path("models/xgboost_tuned.pkl")
DEFAULT_TRAINING_RAW_DATASET = Path("data/raw/dataset.csv")
DEFAULT_TRAINING_PROCESSED_DATASET = Path("data/processed/dataset_processed.csv")


_ENGINEERING_DROP_COLS: Tuple[str, ...] = (
    "abbreviation_density",
    "attribute_mutations_outside_init",
    "maintainability_score",
    "max_lines_per_class",
    "mean_lines_per_class",
    "vcs_available",
    "y_ShotgunSurgery",
    "smells",
    "commit_bursts",
    "lines_deleted",
    "coupled_file_changes",
    "god_class_proxies",
    "indentation_irregularity",
    "pep8_examples",
    "vcs_top_coupled",
    "cross_file_call_edges",
)


@dataclass(frozen=True)
class PredictionResult:
    per_file: pd.DataFrame
    summary: Dict[str, Any]


def _require_xgboost_if_needed(model_path: Path) -> None:
    """Provide a friendly message if the pickle requires xgboost."""
    # The artifact name strongly suggests xgboost; joblib will fail with ImportError
    # if xgboost isn't installed. We pre-check to make the error actionable.
    if "xgboost" in model_path.name.lower() and importlib.util.find_spec("xgboost") is None:
        raise RuntimeError(
            "The saved model appears to be an XGBoost model, but `xgboost` is not installed. "
            "Install it with: `pip install xgboost` (inside your .venv), then retry."
        )


def _load_model(model_path: Path):
    _require_xgboost_if_needed(model_path)
    try:
        return joblib.load(model_path)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Failed to load model artifact at {model_path}: {e}") from e


def _load_feature_schema(processed_dataset_path: Path) -> Tuple[List[str], List[str]]:
    """Returns (feature_cols, target_cols) based on dataset_processed.csv header."""
    if not processed_dataset_path.exists():
        raise FileNotFoundError(
            f"Missing processed dataset at {processed_dataset_path}. "
            "This file is used as the feature schema for inference."
        )

    cols = list(pd.read_csv(processed_dataset_path, nrows=0).columns)
    target_cols = [c for c in cols if c.startswith("y_")]
    feature_cols = [c for c in cols if c not in target_cols and c != "file_path"]

    if not feature_cols:
        raise RuntimeError(
            f"Could not infer feature columns from {processed_dataset_path}; got empty feature list."
        )

    return feature_cols, target_cols


def _fit_scaler_from_training(training_raw_dataset_path: Path, feature_cols: List[str]) -> Tuple[MinMaxScaler, List[str]]:
    """Fits a MinMaxScaler using the same logic as src/preprocessing/engineering.py.

    Note: the project does not persist the scaler, so we re-fit from the training CSV.
    """
    if not training_raw_dataset_path.exists():
        raise FileNotFoundError(
            f"Missing training dataset at {training_raw_dataset_path}. "
            "It is required to re-fit the MinMaxScaler used during training."
        )

    df = pd.read_csv(training_raw_dataset_path, low_memory=False)

    for col in ["unit_test_presence", "vcs_available"]:
        if col in df.columns:
            # training script casts these to int
            df[col] = df[col].astype(int)

    df = df.drop(columns=[c for c in _ENGINEERING_DROP_COLS if c in df.columns], errors="ignore")

    # we only scale columns that are part of the inference feature set
    df = df[[c for c in df.columns if c in (set(feature_cols) | {"file_path"})]]

    # coerce booleans/objects to numeric where possible
    for c in df.columns:
        if c == "file_path":
            continue
        if df[c].dtype == bool:
            df[c] = df[c].astype(int)
        if df[c].dtype == object:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    numeric_cols = [c for c in df.columns if c != "file_path"]

    df[numeric_cols] = df[numeric_cols].fillna(0)

    scaler = MinMaxScaler()
    scaler.fit(df[numeric_cols])

    return scaler, numeric_cols


def analyze_run_directory(run_dir: Path) -> pd.DataFrame:
    """Analyze Python files under run_dir and return a DataFrame of numerical summaries."""
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    records: List[Dict[str, Any]] = []

    for fp in sorted(run_dir.rglob("*.py")):
        try:
            metrics = PythonCodeAnalyzer(str(fp)).analyze()
            summary = metrics.get("numerical_summary", {})
            if not isinstance(summary, dict) or not summary:
                continue

            # Normalize file_path to be relative to the run dir for display.
            summary = dict(summary)
            try:
                summary["file_path"] = str(fp.relative_to(run_dir))
            except Exception:  # noqa: BLE001
                summary["file_path"] = str(fp)

            records.append(summary)
        except Exception:
            # Skip files that fail parsing/analysis; caller gets counts from result shape.
            continue

    return pd.DataFrame(records)


def transform_features(
    raw_features: pd.DataFrame,
    feature_cols: List[str],
    scaler: MinMaxScaler,
    scaler_numeric_cols: List[str],
) -> pd.DataFrame:
    """Align columns + apply scaling to match the training representation."""
    df = raw_features.copy()

    # drop columns that engineering drops, if present
    df = df.drop(columns=[c for c in _ENGINEERING_DROP_COLS if c in df.columns], errors="ignore")

    # ensure required features exist
    for c in feature_cols:
        if c not in df.columns:
            df[c] = 0

    # keep only the model feature columns
    df = df[feature_cols]

    # type normalization
    for c in df.columns:
        if df[c].dtype == bool:
            df[c] = df[c].astype(int)
        if df[c].dtype == object:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.fillna(0)

    # Scale numeric columns using training-fitted scaler.
    # IMPORTANT: MinMaxScaler requires the same column order as it was fitted with.
    cols_to_scale = [c for c in scaler_numeric_cols if c in df.columns]
    if cols_to_scale:
        df[cols_to_scale] = scaler.transform(df[cols_to_scale])

    return df


def predict_any_smell(
    run_dir: Path = Path("run"),
    model_path: Path = DEFAULT_MODEL_PATH,
    training_raw_dataset_path: Path = DEFAULT_TRAINING_RAW_DATASET,
    training_processed_dataset_path: Path = DEFAULT_TRAINING_PROCESSED_DATASET,
    threshold: float = 0.5,
) -> PredictionResult:
    """End-to-end: analyze run/ -> preprocess -> predict using tuned XGBoost model.

    Returns per-file predictions and a small summary for the GUI.
    """
    feature_cols, _target_cols = _load_feature_schema(training_processed_dataset_path)
    scaler, scaler_numeric_cols = _fit_scaler_from_training(training_raw_dataset_path, feature_cols)

    raw = analyze_run_directory(run_dir)
    if raw.empty:
        return PredictionResult(
            per_file=pd.DataFrame(columns=["file_path", "pred_proba", "pred_label"]),
            summary={
                "files_analyzed": 0,
                "files_predicted_smelly": 0,
                "mean_pred_proba": None,
            },
        )

    model_features = transform_features(raw, feature_cols, scaler, scaler_numeric_cols)
    model = _load_model(model_path)

    # Predict probabilities when available.
    pred_proba: Optional[np.ndarray]
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(model_features)
        # binary classifier: proba[:, 1]
        pred_proba = proba[:, 1] if getattr(proba, "ndim", 1) == 2 and proba.shape[1] >= 2 else proba
    else:
        pred_proba = None

    if pred_proba is None:
        preds = model.predict(model_features)
        pred_label = (np.asarray(preds).reshape(-1) > 0).astype(int)
        pred_proba_out = np.full(shape=(len(pred_label),), fill_value=np.nan)
    else:
        pred_proba_out = np.asarray(pred_proba).reshape(-1)
        pred_label = (pred_proba_out >= threshold).astype(int)

    out = pd.DataFrame(
        {
            "file_path": raw.get("file_path", pd.Series(["(unknown)"] * len(raw))).astype(str),
            "pred_proba": pred_proba_out,
            "pred_label": pred_label,
        }
    ).sort_values(["pred_label", "pred_proba"], ascending=[False, False], kind="mergesort")

    smelly_count = int(out["pred_label"].sum()) if not out.empty else 0
    mean_proba = float(np.nanmean(out["pred_proba"].to_numpy())) if not out.empty else None

    return PredictionResult(
        per_file=out,
        summary={
            "files_analyzed": int(len(out)),
            "files_predicted_smelly": smelly_count,
            "mean_pred_proba": None if np.isnan(mean_proba) else mean_proba,
            "threshold": threshold,
        },
    )
