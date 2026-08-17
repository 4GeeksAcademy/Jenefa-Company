"""
Safe snippet for basic pandas cleaning. Copy and adapt for your dataset.
Run: python pandas_clean.py  (ensure pandas is installed)
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("pandas is not installed.", file=sys.stderr)
    raise SystemExit(1)

INPUT_PATH = Path("data.csv")

if not INPUT_PATH.is_file():
    print("Input file is missing or is not a regular file.", file=sys.stderr)
    raise SystemExit(1)

try:
    df = pd.read_csv(INPUT_PATH)
except OSError:
    print("Unable to read the input file.", file=sys.stderr)
    raise SystemExit(1)
except (UnicodeDecodeError, ValueError):
    print("The file could not be parsed as CSV.", file=sys.stderr)
    raise SystemExit(1)

print("df_shape", df.shape)
print("df_dtypes", df.dtypes)

# Drop fully null columns
df = df.dropna(axis=1, how="all")
print("df_shape_after_drop_all_null_cols", df.shape)

# Fill or drop nulls in key columns (customise columns)
# df = df.dropna(subset=["required_col"])
# df["optional_col"] = df["optional_col"].fillna(0)

# Normalise column names (optional)
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
print("df_columns", list(df.columns))

# Deduplicate (optional)
before = len(df)
df = df.drop_duplicates()
print("rows_dropped_duplicates", before - len(df))

# Sample output
print("df_head", df.head())
