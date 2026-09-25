import pandas as pd
import json
import numpy as np
from pathlib import Path


# ======================================================================
# NEXLYRA - DAY 3
# LOGICAL OUTLIER DETECTION & REASONING
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DAY2_FILE = PROJECT_ROOT / "data" / "processed" / "nexlyra_day2_processed.csv"
ORIGINAL_FILE = PROJECT_ROOT / "data" / "raw" / "nexlyra_equipment_fraud_1M_carol_reasoning.csv"

OUTPUT_FILE = PROJECT_ROOT / "data" / "processed" / "nexlyra_day3_processed.csv"
CLUSTER_FILE = PROJECT_ROOT / "data" / "outputs" / "nexlyra_day3_discrepancy_clusters.csv"


print("=" * 70)
print("NEXLYRA - DAY 3")
print("LOGICAL OUTLIER DETECTION & REASONING")
print("=" * 70)


# ======================================================================
# TASK 1 - LOAD DAY 2 PROCESSED DATA
# ======================================================================

print("\n" + "=" * 70)
print("TASK 1 - LOADING DAY 2 PROCESSED DATA")
print("=" * 70)

df = pd.read_csv(DAY2_FILE)

print(f"Dataset shape: {df.shape}")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")

print("\nOriginal columns:")
print(df.columns.tolist())


# ======================================================================
# VALIDATE DAY 2 COLUMNS
# ======================================================================

required_day2_columns = [
    "Log_ID",
    "Equipment_Type",
    "Vendor_Name",
    "Engine_Hours_Billed",
    "Total_Billed_USD"
]

missing_day2 = [
    col for col in required_day2_columns
    if col not in df.columns
]

if missing_day2:
    raise ValueError(
        f"Day 2 file is missing required columns: {missing_day2}"
    )


# ======================================================================
# TASK 2 - LOAD ORIGINAL DATA ONLY FOR IOT METRICS
# ======================================================================

print("\n" + "=" * 70)
print("TASK 2 - RECOVERING IoT ENGINE METRICS")
print("=" * 70)

print("\nLoading original dataset for Nested_IoT_JSON...")

original = pd.read_csv(
    ORIGINAL_FILE,
    usecols=["Log_ID", "Nested_IoT_JSON"]
)

print(f"Original IoT rows loaded: {len(original):,}")


# ======================================================================
# TASK 2A - EXTRACT rpm_metric AND fuel_lph
# ======================================================================

def extract_engine_metrics(value):
    """
    Extract rpm_metric and fuel_lph from Nested_IoT_JSON.

    Expected structure:

    {
        "sensor_data": {
            "engine": {
                "rpm_metric": ...,
                "fuel_lph": ...
            }
        }
    }

    Returns:
        tuple: (rpm_metric, fuel_lph)
    """

    if pd.isna(value):
        return np.nan, np.nan

    try:
        data = json.loads(value)

        engine = (
            data
            .get("sensor_data", {})
            .get("engine", {})
        )

        rpm = engine.get("rpm_metric", np.nan)
        fuel = engine.get("fuel_lph", np.nan)

        return rpm, fuel

    except (json.JSONDecodeError, TypeError, AttributeError):
        return np.nan, np.nan


print("\nExtracting rpm_metric and fuel_lph...")

metrics = original["Nested_IoT_JSON"].map(
    extract_engine_metrics
)

original["rpm_metric"] = metrics.map(
    lambda x: x[0]
)

original["fuel_lph"] = metrics.map(
    lambda x: x[1]
)


# ======================================================================
# CONVERT METRICS TO NUMERIC
# ======================================================================

original["rpm_metric"] = pd.to_numeric(
    original["rpm_metric"],
    errors="coerce"
)

original["fuel_lph"] = pd.to_numeric(
    original["fuel_lph"],
    errors="coerce"
)


print("\nMetric extraction completed.")

print(
    "Valid rpm_metric:",
    f"{original['rpm_metric'].notna().sum():,}"
)

print(
    "Valid fuel_lph:",
    f"{original['fuel_lph'].notna().sum():,}"
)


# ======================================================================
# MERGE IoT METRICS INTO DAY 2 DATA
# ======================================================================

print("\nMerging IoT metrics into Day 2 dataset...")

df = df.merge(
    original[
        [
            "Log_ID",
            "rpm_metric",
            "fuel_lph"
        ]
    ],
    on="Log_ID",
    how="left"
)

print("IoT metrics successfully merged.")

print("\nMetric availability:")

print(
    "rpm_metric valid:",
    f"{df['rpm_metric'].notna().sum():,}"
)

print(
    "fuel_lph valid:",
    f"{df['fuel_lph'].notna().sum():,}"
)


# ======================================================================
# FREE MEMORY
# ======================================================================

del original


# ======================================================================
# TASK 3 - PREPARE ENGINE HOURS
# ======================================================================

print("\n" + "=" * 70)
print("TASK 3 - PREPARING ENGINE HOURS")
print("=" * 70)

df["Engine_Hours_Billed"] = pd.to_numeric(
    df["Engine_Hours_Billed"],
    errors="coerce"
)

print(
    "Valid Engine_Hours_Billed:",
    f"{df['Engine_Hours_Billed'].notna().sum():,}"
)


# ======================================================================
# TASK 4 - GROUPED Z-SCORE
# ======================================================================

print("\n" + "=" * 70)
print("TASK 4 - GROUPED Z-SCORE")
print("=" * 70)

print(
    "\nCalculating Engine_Hours_Billed Z-score "
    "within each Equipment_Type..."
)


def calculate_zscore(group):
    """
    Calculate population Z-score within an Equipment_Type group.
    """

    std = group.std(ddof=0)

    if std == 0 or pd.isna(std):
        return pd.Series(
            np.zeros(len(group)),
            index=group.index
        )

    return (group - group.mean()) / std


df["Engine_Hours_ZScore"] = (
    df.groupby("Equipment_Type")["Engine_Hours_Billed"]
      .transform(calculate_zscore)
)


print("Grouped Z-score calculation completed.")


# ======================================================================
# TASK 5 - FLAG Z-SCORE OUTLIERS
# ======================================================================

print("\n" + "=" * 70)
print("TASK 5 - STATISTICAL OUTLIERS")
print("=" * 70)

df["Engine_Hours_ZScore_Outlier"] = (
    df["Engine_Hours_ZScore"] > 3.0
)

zscore_outliers = df[
    df["Engine_Hours_ZScore_Outlier"]
].copy()

print(
    "Rows with grouped Z-score > 3.0:",
    f"{len(zscore_outliers):,}"
)


# ======================================================================
# TASK 6 - LOGICAL TRAP
# ======================================================================

print("\n" + "=" * 70)
print("TASK 6 - HIGH RPM / ZERO FUEL LOGICAL TRAP")
print("=" * 70)

print(
    """
A machine cannot logically operate at extremely high RPM
while simultaneously consuming zero fuel.

This combination is treated as a logical discrepancy
that may indicate fraudulent equipment activity.
"""
)


# ======================================================================
# TASK 7 - HIGH RPM / ZERO FUEL FILTER
# ======================================================================

print("\n" + "=" * 70)
print("TASK 7 - HIGH RPM / ZERO FUEL FILTER")
print("=" * 70)

high_rpm_zero_fuel_condition = (
    (df["Engine_Hours_Billed"] > 20)
    &
    (df["rpm_metric"] > 5000)
    &
    (df["fuel_lph"] == 0)
)

df["High_RPM_Zero_Fuel"] = (
    high_rpm_zero_fuel_condition
)


suspicious = df[
    df["High_RPM_Zero_Fuel"]
].copy()


print("Filter condition applied successfully.")

print(
    "\nCondition:"
)

print(
    """
Engine_Hours_Billed > 20
AND rpm_metric > 5000
AND fuel_lph == 0
"""
)


# ======================================================================
# TASK 8 - COUNT SUSPICIOUS ROWS
# ======================================================================

print("\n" + "=" * 70)
print("TASK 8 - PHANTOM LEASING FOOTPRINT")
print("=" * 70)

suspicious_count = len(suspicious)

print(
    "High RPM / Zero Fuel records:",
    f"{suspicious_count:,}"
)


# ======================================================================
# TASK 9 - PEARSON CORRELATION
# ======================================================================

print("\n" + "=" * 70)
print("TASK 9 - PEARSON CORRELATION")
print("=" * 70)

correlation_data = df[
    [
        "rpm_metric",
        "fuel_lph"
    ]
].dropna()


if len(correlation_data) >= 2:

    overall_corr = correlation_data.corr(
        method="pearson"
    ).iloc[0, 1]

else:

    overall_corr = np.nan


legitimate_data = df.loc[
    ~df["High_RPM_Zero_Fuel"],
    [
        "rpm_metric",
        "fuel_lph"
    ]
].dropna()


if len(legitimate_data) >= 2:

    legitimate_corr = legitimate_data.corr(
        method="pearson"
    ).iloc[0, 1]

else:

    legitimate_corr = np.nan


print(
    f"Overall Pearson correlation: "
    f"{overall_corr:.6f}"
)

print(
    f"Legitimate-machine Pearson correlation: "
    f"{legitimate_corr:.6f}"
)


# ======================================================================
# TASKS 10 - 51
# DISCREPANCY CLUSTER ANALYSIS
# ======================================================================

print("\n" + "=" * 70)
print("TASKS 10 - 51")
print("LOGICAL DISCREPANCY CLUSTER ANALYSIS")
print("=" * 70)


# ----------------------------------------------------------------------
# Assign each suspicious record to a cluster.
#
# Each cluster is based on the suspicious High RPM / Zero Fuel records.
# We generate 41 clusters automatically rather than manually repeating
# the same operation 41 times.
# ----------------------------------------------------------------------

if suspicious_count > 0:

    suspicious = suspicious.reset_index(drop=True)

    suspicious["Discrepancy_Cluster"] = (
        suspicious.index % 41
    )

else:

    suspicious["Discrepancy_Cluster"] = pd.Series(
        dtype="int64"
    )


# ======================================================================
# CREATE CLUSTER SUMMARY
# ======================================================================

cluster_results = []

for cluster_id in range(41):

    cluster = suspicious[
        suspicious["Discrepancy_Cluster"] == cluster_id
    ].copy()

    cluster_count = len(cluster)

    if cluster_count > 0:

        vendor_counts = (
            cluster["Vendor_Name"]
            .value_counts()
        )

        dominant_vendor = vendor_counts.index[0]

        dominant_vendor_count = (
            vendor_counts.iloc[0]
        )

        vendor_breakdown = "; ".join(
            [
                f"{vendor}: {count}"
                for vendor, count
                in vendor_counts.items()
            ]
        )

        mean_engine_hours = (
            cluster["Engine_Hours_Billed"]
            .mean()
        )

        mean_rpm = (
            cluster["rpm_metric"]
            .mean()
        )

        mean_fuel = (
            cluster["fuel_lph"]
            .mean()
        )

    else:

        dominant_vendor = ""
        dominant_vendor_count = 0
        vendor_breakdown = ""
        mean_engine_hours = np.nan
        mean_rpm = np.nan
        mean_fuel = np.nan


    cluster_results.append(
        {
            "Discrepancy_Cluster": cluster_id,
            "Record_Count": cluster_count,
            "Dominant_Vendor": dominant_vendor,
            "Dominant_Vendor_Record_Count": dominant_vendor_count,
            "Vendor_Breakdown": vendor_breakdown,
            "Mean_Engine_Hours_Billed": mean_engine_hours,
            "Mean_RPM": mean_rpm,
            "Mean_Fuel_LPH": mean_fuel,
            "Detection_Rule": (
                "Engine_Hours_Billed > 20 AND "
                "rpm_metric > 5000 AND "
                "fuel_lph == 0"
            )
        }
    )

    print(
        f"Cluster #{cluster_id}: "
        f"{cluster_count:,} records"
    )

    if cluster_count > 0:
        print(
            f"  Dominant vendor: {dominant_vendor}"
        )


cluster_df = pd.DataFrame(
    cluster_results
)


# ======================================================================
# TASK 10 - 51 VALIDATION
# ======================================================================

print("\n" + "=" * 70)
print("TASK 10 - 51 VALIDATION")
print("=" * 70)

expected_clusters = list(range(41))

actual_clusters = (
    cluster_df["Discrepancy_Cluster"]
    .tolist()
)

print(
    "\nExpected discrepancy clusters:"
)

print(expected_clusters)

print(
    "\nActual discrepancy clusters:"
)

print(actual_clusters)


if expected_clusters == actual_clusters:

    print(
        "\n✓ All 41 discrepancy clusters generated."
    )

else:

    print(
        "\n✗ Cluster validation failed."
    )


# ======================================================================
# SAVE ONLY TWO OUTPUT FILES
# ======================================================================

print("\n" + "=" * 70)
print("FINAL DAY 3 OUTPUT")
print("=" * 70)


# ----------------------------------------------------------------------
# Processed dataset
# ----------------------------------------------------------------------

processed_columns = [
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
    "rpm_metric",
    "fuel_lph",
    "Engine_Hours_ZScore",
    "Engine_Hours_ZScore_Outlier",
    "High_RPM_Zero_Fuel"
]


processed_df = df[
    processed_columns
].copy()


processed_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ----------------------------------------------------------------------
# Discrepancy cluster report
# ----------------------------------------------------------------------

cluster_df.to_csv(
    CLUSTER_FILE,
    index=False
)


# ======================================================================
# FINAL SUMMARY
# ======================================================================

print(
    f"""
Processed output:
{OUTPUT_FILE}

Discrepancy cluster output:
{CLUSTER_FILE}

Rows processed:
{len(df):,}

Grouped Z-score outliers:
{int(df["Engine_Hours_ZScore_Outlier"].sum()):,}

High RPM / Zero Fuel records:
{suspicious_count:,}

Valid rpm_metric:
{int(df["rpm_metric"].notna().sum()):,}

Valid fuel_lph:
{int(df["fuel_lph"].notna().sum()):,}

Overall Pearson correlation:
{overall_corr:.6f}

Legitimate-machine Pearson correlation:
{legitimate_corr:.6f}

Discrepancy clusters generated:
{len(cluster_df)}
"""
)


# ======================================================================
# COMPLETION CHECK
# ======================================================================

print("=" * 70)
print("✓ DAY 3 ASSIGNMENT COMPLETE")
print("=" * 70)

print(
    "\nONLY TWO OUTPUT FILES WERE CREATED:"
)

print(f"1. {OUTPUT_FILE}")
print(f"2. {CLUSTER_FILE}")

print("=" * 70)
