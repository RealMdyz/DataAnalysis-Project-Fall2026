"""Temporal train / validation / test split, defined once for the whole project.

The boundaries live in configs/config.yaml (section `split`) so that every
notebook and every model in phases 2-5 uses exactly the same split.
"""

from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config():
    with open(ROOT / "configs" / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def assign_split(dates, cfg=None):
    """Label each date as 'train', 'validation', 'test' or 'out_of_range'.

    `dates` is a pandas Series of timestamps (review times). A review is out of
    range when it falls before window.start or after window.end.
    """
    cfg = cfg or load_config()
    start = pd.Timestamp(cfg["window"]["start"])
    end = pd.Timestamp(cfg["window"]["end"]) + pd.Timedelta(days=1)  # end date is inclusive
    val_start = pd.Timestamp(cfg["split"]["validation_start"])
    test_start = pd.Timestamp(cfg["split"]["test_start"])

    labels = pd.Series("out_of_range", index=dates.index)
    labels[(dates >= start) & (dates < val_start)] = "train"
    labels[(dates >= val_start) & (dates < test_start)] = "validation"
    labels[(dates >= test_start) & (dates < end)] = "test"
    return labels
