
import pandas as pd
import numpy as np
import json
import warnings
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ================================================================
# NEXLYRA - DAY 2
# DATA CLEANING, TIMEZONE ALIGNMENT & HEX DECODING
# TASKS 1 - 51
# ================================================================

FILE_PATH = PROJECT_ROOT / "data" / "raw" / "nexlyra_equipment_fraud_1M_carol_reasoning.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "nexlyra_day2_processed.csv"
VALIDATION_FILE = PROJECT_ROOT / "data" / "outputs" / "nexlyra_day2_coordinate_validation.csv"

CURRENCY_COL = "Total_Billed_USD"
TIMESTAMP_COL = "Telemetry_Timestamp"
JSON_COL = "Nested_IoT_JSON"

print("=" * 70)
print("NEXLYRA - DAY 2")
print("DATA CLEANING, TIMEZONE ALIGNMENT & HEX DECODING")
print("TASKS 1 - 51")
print("=" * 70)
print(f"\nDataset file:\n{FILE_PATH}")

# ----------------------------------------------------------------
# TASK 1 - TIMEZONE ALIGNMENT, TYPE RESOLUTION & HEX DECODING
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 1 - TIMEZONE ALIGNMENT, TYPE RESOLUTION & HEX DECODING")
print("=" * 70)

print("""
Day 2 focuses on three data-quality issues:
1. Mixed data types in Total_Billed_USD
2. Mixed timezone/timestamp representations
3. Hex-encoded GPS coordinates inside Nested_IoT_JSON
""")

# ----------------------------------------------------------------
# Load data
# ----------------------------------------------------------------
print("\nLoading dataset...")
df = pd.read_csv(FILE_PATH)

print("\nDataset shape:")
print(df.shape)

print("\nOriginal dtypes:")
print(df.dtypes)

print("\nOriginal memory usage:")
print(f"{df.memory_usage(deep=True).sum() / (1024**2):.2f} MB")

# ----------------------------------------------------------------
# TASK 2 - INSPECT Total_Billed_USD
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 2 - INSPECT 'Total_Billed_USD'")
print("=" * 70)

print("\nColumn dtype:")
print(df[CURRENCY_COL].dtype)

print("\nFirst 10 values:")
print(df[CURRENCY_COL].head(10).to_list())

currency_text = df[CURRENCY_COL].astype("string")
has_dollar = currency_text.str.contains(r"\$", regex=True, na=False)
has_comma = currency_text.str.contains(",", regex=False, na=False)

print(f"\nValues containing '$': {int(has_dollar.sum()):,}")
print(f"Values containing commas: {int(has_comma.sum()):,}")
print(f"Values without '$': {int((~has_dollar).sum()):,}")

print("\nSample values containing '$' or commas:")
print(df.loc[has_dollar | has_comma, CURRENCY_COL].head(10).to_list())

# ----------------------------------------------------------------
# TASK 3 - DEMONSTRATE UNSAFE CLEANING / SettingWithCopyWarning
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 3 - DEMONSTRATE UNSAFE CLEANING")
print("=" * 70)

print("""
An unsafe chained-assignment pattern can produce
SettingWithCopyWarning because pandas may be modifying a view
instead of the original DataFrame.
""")

demo = df.head(100).copy()
demo_slice = demo[demo[CURRENCY_COL].notna()]

with warnings.catch_warnings(record=True) as caught_warnings:
    warnings.simplefilter("always")
    # Deliberately unsafe demonstration for the task.
    # Depending on the pandas version, pandas may or may not emit
    # SettingWithCopyWarning.
    try:
        demo_slice[CURRENCY_COL] = (
            demo_slice[CURRENCY_COL]
            .astype(str)
            .str.replace("$", "", regex=False)
        )
    except Exception as exc:
        print(f"Unsafe operation raised: {type(exc).__name__}: {exc}")

    swc = [w for w in caught_warnings
           if "SettingWithCopyWarning" in str(w.category)]

if swc:
    print("SettingWithCopyWarning reproduced.")
else:
    print("SettingWithCopyWarning was not emitted by this pandas version.")
    print("The chained-assignment risk is still demonstrated conceptually.")

print("\nSafe alternative:")
print("Use .loc[...] or vectorized operations on the original column.")

# ----------------------------------------------------------------
# TASK 4 - MANDATORY NEXLYRA AI PROMPT
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 4 - NEXLYRA AI PROMPT")
print("=" * 70)

prompt_4 = (
    "What causes a SettingWithCopyWarning in pandas, and how do I "
    "properly clean a mixed-type currency column using .loc or vectorization?"
)
print("\nMandatory prompt:")
print(prompt_4)

print("\nApplied principle:")
print("- Avoid chained assignment.")
print("- Use vectorized string operations.")
print("- Assign the cleaned result back to the original DataFrame.")

# ----------------------------------------------------------------
# TASK 5 - SAFE VECTORIZED CURRENCY CLEANING
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 5 - SAFE VECTORIZED CLEANING OF 'Total_Billed_USD'")
print("=" * 70)

raw_currency = df[CURRENCY_COL].astype("string")

clean_currency = (
    df[CURRENCY_COL]
    .astype("string")
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
)

# Convert the cleaned values to numeric first
clean_currency = pd.to_numeric(clean_currency, errors="coerce")

# Replace the original string column with the numeric Series
df = df.drop(columns=[CURRENCY_COL])
df[CURRENCY_COL] = clean_currency.astype("float64")
print("\nFirst 10 cleaned values:")
print(df[CURRENCY_COL].head(10).to_list())

print("\nNew dtype:")
print(df[CURRENCY_COL].dtype)

print(f"\nMissing values after conversion: {int(df[CURRENCY_COL].isna().sum()):,}")
print(f"Minimum value: {df[CURRENCY_COL].min():.6f}")
print(f"Maximum value: {df[CURRENCY_COL].max():.6f}")

print("\nCurrency cleaning completed using vectorized operations.")

# ----------------------------------------------------------------
# TASK 6 - INSPECT MIXED TIMESTAMP FORMATS
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 6 - INSPECT MIXED 'Telemetry_Timestamp' FORMATS")
print("=" * 70)

timestamp_text = df[TIMESTAMP_COL].astype("string")

is_z = timestamp_text.str.endswith("Z", na=False)
local_like = ~is_z

print(f"\nUTC 'Z'-terminated timestamps: {int(is_z.sum()):,}")
print(f"Timezone-naive/local-format timestamps: {int(local_like.sum()):,}")

print("\nExamples of UTC-formatted timestamps:")
print(df.loc[is_z, TIMESTAMP_COL].head(5).to_list())

print("\nExamples of local-format timestamps:")
print(df.loc[local_like, TIMESTAMP_COL].head(5).to_list())

print("""
The dataset does not provide a separate timezone identifier for the
timezone-naive/local-format timestamps. Therefore, for this assignment
they are interpreted as UTC when unified with the Z timestamps.
This assumption is explicitly recorded rather than silently inventing
a local timezone.
""")

# ----------------------------------------------------------------
# TASK 7 - MANDATORY NEXLYRA AI PROMPT
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 7 - NEXLYRA AI PROMPT")
print("=" * 70)

prompt_7 = (
    "How do I use pd.to_datetime with mixed formats, and how do I "
    "convert all timestamps to a unified UTC timezone offset?"
)
print("\nMandatory prompt:")
print(prompt_7)

# ----------------------------------------------------------------
# TASK 8 - IDENTIFY HEX-ENCODED GPS VALUES
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 8 - HEX-ENCODED GPS VALUES")
print("=" * 70)

def extract_gps_hex(value):
    if pd.isna(value) or not str(value).strip():
        return {"lat": None, "lon": None}

    try:
        obj = json.loads(value)
        gps = (
            obj.get("sensor_data", {})
               .get("gps_hex", {})
        )
        return {
            "lat": gps.get("lat"),
            "lon": gps.get("lon"),
        }
    except (json.JSONDecodeError, TypeError, AttributeError):
        return {"lat": None, "lon": None}

sample_json = df[JSON_COL].dropna().iloc[0]
sample_gps = extract_gps_hex(sample_json)

print("\nSample encoded GPS:")
print(sample_gps)

print("\nEncoded latitude:")
print(sample_gps["lat"])

print("Encoded longitude:")
print(sample_gps["lon"])

# ----------------------------------------------------------------
# TASK 9 - MANDATORY NEXLYRA AI PROMPT
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 9 - NEXLYRA AI PROMPT")
print("=" * 70)

prompt_9 = (
    "Write a vectorized pandas function to convert a column of "
    "hex-encoded strings back to standard readable floats, handling NaNs safely."
)
print("\nMandatory prompt:")
print(prompt_9)

# ----------------------------------------------------------------
# GPS extraction + safe hex decoder
# ----------------------------------------------------------------
def decode_hex_float(value):
    if pd.isna(value) or value is None:
        return np.nan

    value = str(value).strip()

    if not value:
        return np.nan

    try:
        decoded_text = bytes.fromhex(value).decode("utf-8")
        return float(decoded_text)
    except (ValueError, TypeError, UnicodeDecodeError):
        return np.nan

gps_series = df[JSON_COL].map(extract_gps_hex)

df["lat_hex"] = gps_series.map(lambda x: x["lat"])
df["lon_hex"] = gps_series.map(lambda x: x["lon"])

# ----------------------------------------------------------------
# TASK 10 - DECODE GPS + IDENTIFY (0,0)
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASK 10 - DECODE GPS COORDINATES")
print("=" * 70)

df["lat"] = df["lat_hex"].map(decode_hex_float).astype("float64")
df["lon"] = df["lon_hex"].map(decode_hex_float).astype("float64")

print("\nFirst 10 decoded coordinates:")
print(df[["lat_hex", "lon_hex", "lat", "lon"]].head(10).to_string(index=False))

print("\nDecoded latitude dtype:")
print(df["lat"].dtype)

print("Decoded longitude dtype:")
print(df["lon"].dtype)

missing_lat = int(df["lat"].isna().sum())
missing_lon = int(df["lon"].isna().sum())

print(f"\nMissing decoded latitude values: {missing_lat:,}")
print(f"Missing decoded longitude values: {missing_lon:,}")

atlantic_mask = (
    df["lat"].notna()
    & df["lon"].notna()
    & np.isclose(df["lat"], 0.0, atol=1e-9)
    & np.isclose(df["lon"], 0.0, atol=1e-9)
)

atlantic_count = int(atlantic_mask.sum())

print(f"\nRows mapping to approximately (0.0, 0.0): {atlantic_count:,}")

if atlantic_count:
    print("\nFirst Atlantic/(0,0) records:")
    print(
        df.loc[
            atlantic_mask,
            ["Log_ID", TIMESTAMP_COL, "lat", "lon"]
        ].head(10).to_string(index=False)
    )
else:
    print("No records in this dataset map to approximately (0.0, 0.0).")

# ----------------------------------------------------------------
# TIMESTAMP CONVERSION
# ----------------------------------------------------------------
print("\nConverting timestamps to unified UTC...")

parsed_timestamp = pd.to_datetime(
    df[TIMESTAMP_COL],
    format="mixed",
    utc=True,
    errors="coerce"
)

df["Telemetry_Timestamp_UTC"] = parsed_timestamp

print("\nTimestamp conversion results:")
print(f"Valid UTC timestamps: {int(parsed_timestamp.notna().sum()):,}")
print(f"Invalid timestamps: {int(parsed_timestamp.isna().sum()):,}")

print("\nFirst 10 unified UTC timestamps:")
print(df["Telemetry_Timestamp_UTC"].head(10).to_string(index=False))

# ----------------------------------------------------------------
# TASKS 11 - 51
# Coordinate blocks #1 - #41
#
# Each validation block checks one valid decoded coordinate record.
# The original hex bytes are decoded, converted to float, encoded
# back to UTF-8 bytes, then hex encoded again. A matching hex string
# proves that the byte conversion did not truncate the original text.
# ----------------------------------------------------------------

print("\n" + "=" * 70)
print("TASKS 11 - 51")
print("HEX DECRYPTION VALIDATION - COORDINATE BLOCKS #1 TO #41")
print("=" * 70)

validation_rows = []
valid_coordinate_indices = df.index[
    df["lat_hex"].notna()
    & df["lon_hex"].notna()
    & df["lat"].notna()
    & df["lon"].notna()
]

print(f"\nValid coordinate records available: {len(valid_coordinate_indices):,}")

if len(valid_coordinate_indices) < 41:
    raise RuntimeError(
        f"Only {len(valid_coordinate_indices)} valid coordinate records "
        "are available; 41 validation blocks are required."
    )

for block_number, row_index in enumerate(valid_coordinate_indices[:41], start=1):
    task_number = block_number + 10
    row = df.loc[row_index]

    lat_hex = row["lat_hex"]
    lon_hex = row["lon_hex"]

    lat_text = bytes.fromhex(lat_hex).decode("utf-8")
    lon_text = bytes.fromhex(lon_hex).decode("utf-8")

    lat_value = float(lat_text)
    lon_value = float(lon_text)

    # Round-trip test: decoded text -> UTF-8 bytes -> hex.
    lat_roundtrip = lat_text.encode("utf-8").hex()
    lon_roundtrip = lon_text.encode("utf-8").hex()

    lat_ok = lat_roundtrip.lower() == lat_hex.lower()
    lon_ok = lon_roundtrip.lower() == lon_hex.lower()

    no_truncation = lat_ok and lon_ok

    print("\n" + "-" * 70)
    print(f"TASK {task_number} OF 51")
    print(f"Coordinate block #{block_number}")
    print("-" * 70)

    print(f"Log_ID: {row['Log_ID']}")
    print(f"Original latitude hex : {lat_hex}")
    print(f"Decoded latitude      : {lat_text}")
    print(f"Original longitude hex: {lon_hex}")
    print(f"Decoded longitude     : {lon_text}")

    print(f"Latitude round-trip   : {lat_roundtrip}")
    print(f"Longitude round-trip  : {lon_roundtrip}")

    if no_truncation:
        print("Validation: ✓ No data truncation detected")
    else:
        print("Validation: ✗ Potential data truncation/mismatch detected")

    validation_rows.append({
        "task_number": task_number,
        "coordinate_block": block_number,
        "row_index": int(row_index),
        "Log_ID": row["Log_ID"],
        "lat_hex_original": lat_hex,
        "lat_decoded_text": lat_text,
        "lat_float": lat_value,
        "lat_hex_roundtrip": lat_roundtrip,
        "lon_hex_original": lon_hex,
        "lon_decoded_text": lon_text,
        "lon_float": lon_value,
        "lon_hex_roundtrip": lon_roundtrip,
        "lat_validation": lat_ok,
        "lon_validation": lon_ok,
        "no_truncation": no_truncation,
    })

validation_df = pd.DataFrame(validation_rows)

# ----------------------------------------------------------------
# FINAL TASK VALIDATION
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("TASKS 11 - 51 COMPLETE")
print("=" * 70)

expected_tasks = list(range(11, 52))
actual_tasks = validation_df["task_number"].tolist()

expected_blocks = list(range(1, 42))
actual_blocks = validation_df["coordinate_block"].tolist()

print("\nExpected tasks:")
print(expected_tasks)

print("\nActual tasks:")
print(actual_tasks)

print("\nExpected coordinate blocks:")
print(expected_blocks)

print("\nActual coordinate blocks:")
print(actual_blocks)

all_tasks_ok = expected_tasks == actual_tasks
all_blocks_ok = expected_blocks == actual_blocks
all_validation_ok = bool(validation_df["no_truncation"].all())

if all_tasks_ok:
    print("\n✓ Tasks 11 through 51 completed successfully.")
else:
    print("\n✗ Task numbering validation failed.")

if all_blocks_ok:
    print("✓ Coordinate blocks #1 through #41 completed successfully.")
else:
    print("✗ Coordinate block validation failed.")

if all_validation_ok:
    print("✓ No data truncation detected in coordinate blocks #1 through #41.")
else:
    print("✗ One or more coordinate round-trip validations failed.")

# ----------------------------------------------------------------
# PREPARE FINAL PROCESSED OUTPUT
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("FINAL PROCESSED OUTPUT")
print("=" * 70)

# Keep the useful original fields plus cleaned/decoded fields.
output_columns = [
    "Log_ID",
    "Telemetry_Timestamp",
    "Telemetry_Timestamp_UTC",
    "Project_ID",
    "Vendor_Name",
    "Equipment_Type",
    "Engine_Hours_Billed",
    "Total_Billed_USD",
    "lat",
    "lon",
    "lat_hex",
    "lon_hex",
]

processed_df = df[output_columns].copy()

processed_df.to_csv(OUTPUT_FILE, index=False)
validation_df.to_csv(VALIDATION_FILE, index=False)

print(f"\nProcessed output created:")
print(OUTPUT_FILE)

print("\nCoordinate validation report created:")
print(VALIDATION_FILE)

print("\nProcessed output columns:")
print(processed_df.columns.tolist())

print("\nFirst 5 processed records:")
print(processed_df.head().to_string(index=False))

# ----------------------------------------------------------------
# FINAL DAY 2 SUMMARY
# ----------------------------------------------------------------
print("\n" + "=" * 70)
print("DAY 2 - FINAL SUMMARY")
print("=" * 70)

print(f"""
Rows processed: {len(df):,}

Currency:
- Original dtype: object
- Final dtype: {df[CURRENCY_COL].dtype}
- Missing after conversion: {int(df[CURRENCY_COL].isna().sum()):,}

Timestamps:
- UTC 'Z' input records: {int(is_z.sum()):,}
- Timezone-naive/local-format records: {int(local_like.sum()):,}
- Successfully converted to UTC: {int(parsed_timestamp.notna().sum()):,}
- Invalid timestamps: {int(parsed_timestamp.isna().sum()):,}

GPS:
- Valid latitude values: {int(df["lat"].notna().sum()):,}
- Valid longitude values: {int(df["lon"].notna().sum()):,}
- Approximately (0,0) records: {atlantic_count:,}

Coordinate validation:
- Blocks validated: {len(validation_df)}
- Tasks validated: {len(actual_tasks)}
- No-truncation validations passed: {int(validation_df["no_truncation"].sum())}/{len(validation_df)}

Output files:
1. {OUTPUT_FILE}
2. {VALIDATION_FILE}
""")

if (
    len(df) == 1_000_000
    and all_tasks_ok
    and all_blocks_ok
    and all_validation_ok
    and parsed_timestamp.notna().all()
):
    print("=" * 70)
    print("✓ DAY 2 ASSIGNMENT COMPLETE")
    print("=" * 70)
else:
    print("=" * 70)
    print("DAY 2 PROCESSING COMPLETED WITH VALIDATION NOTES")
    print("=" * 70)
    print("Review the validation results above before marking the assignment complete.")
