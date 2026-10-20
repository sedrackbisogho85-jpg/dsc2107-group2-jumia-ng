import os
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

import pandas as pd
import streamlit as st

REQUIRED_COLUMNS = [
    'source_product_id',
    'product_name',
    'brand',
    'current_price',
    'old_price',
    'displayed_discount_percentage',
    'calculated_discount_percentage',
    'rating',
    'review_count',
    'category',
    'product_url',
    'currency',
    'source_site',
    'scraped_at',
    'scrape_date',
]


def find_dataset_path() -> Path:
    """Locate the final combined cleaned CSV using relative search."""
    repo_root = Path.cwd()
    # Primary expected location
    primary = repo_root / 'data' / 'cleaned' / 'jumia_ng_products_2026-10-13_to_2026-10-19_cleaned.csv'
    if primary.exists():
        return primary

    # Fallback search
    candidates = list(repo_root.glob('**/jumia_ng_products_2026-10-13_to_2026-10-19_cleaned.csv'))
    if candidates:
        return candidates[0]
    # Broader fallback
    candidates = list(repo_root.glob('**/*2026-10-13_to_2026-10-19*cleaned*.csv'))
    if candidates:
        return candidates[0]
    raise FileNotFoundError('Final combined cleaned CSV not found.')


def _safe_float(x: Any) -> Optional[float]:
    if pd.isna(x):
        return None
    if x is None or x == '':
        return None
    try:
        # Handle possible commas if any
        s = str(x).strip().replace(',', '')
        # Handle non-numeric chars? but data cleaned
        return float(s)
    except Exception:
        return None


def _safe_int(x: Any) -> Optional[int]:
    f = _safe_float(x)
    if f is None:
        return None
    try:
        return int(f)
    except Exception:
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def load_data() -> Tuple[pd.DataFrame, List[str]]:
    """Load and prepare dataset. Returns (df, warnings)."""
    path = find_dataset_path()
    warnings: List[str] = []

    try:
        df = pd.read_csv(path, encoding='utf-8', dtype=str)
    except UnicodeError:
        df = pd.read_csv(path, encoding='latin-1', dtype=str)

    missing_req = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_req:
        raise ValueError(f'Missing required columns: {missing_req}')

    # Convert numeric columns
    for col in ['current_price', 'old_price', 'displayed_discount_percentage',
                'calculated_discount_percentage', 'rating', 'review_count']:
        if col in df.columns:
            df[col + '_num'] = df[col].apply(_safe_float)

    # Derived
    df['is_discounted'] = df['displayed_discount_percentage_num'].apply(
        lambda v: v is not None and v > 0.0
    ) | df['calculated_discount_percentage_num'].apply(
        lambda v: v is not None and v > 0.0
    )

    # Clean discount percentage for display - prefer displayed
    def _disc(vd, vc):
        if vd is not None and not pd.isna(vd):
            return vd
        if vc is not None and not pd.isna(vc):
            return vc
        return None

    df['discount_pct_num'] = [ _disc(vd, vc) for vd, vc in zip(
        df.get('displayed_discount_percentage_num'), df.get('calculated_discount_percentage_num'))]

    # Ensure proper types
    if 'scrape_date' in df.columns:
        try:
            df['scrape_date_dt'] = pd.to_datetime(df['scrape_date'], errors='coerce')
        except Exception:
            df['scrape_date_dt'] = pd.NaT

    # Normalize brand
    df['brand_clean'] = df['brand'].fillna('').astype(str).str.strip()
    df['brand_clean'] = df['brand_clean'].replace('', 'Unknown')

    # USD is already in CSV; just ensure label consistency
    df['currency_clean'] = df['currency'].fillna('USD').astype(str).str.strip().replace('', 'USD')

    return df, warnings
