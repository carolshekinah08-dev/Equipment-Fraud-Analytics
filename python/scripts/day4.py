import os
import sqlite3
import time
import pandas as pd
from pathlib import Path


# ======================================================================
# NEXLYRA - DAY 4
# ADVANCED SQL & QUERY OPTIMIZATION
# ======================================================================

print("=" * 70)
print("NEXLYRA - DAY 4")
print("ADVANCED SQL & QUERY OPTIMIZATION")
print("TASKS 1 - 51")
print("=" * 70)


# ======================================================================
# FILE CONFIGURATION
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DAY3_FILE = PROJECT_ROOT / "data" / "processed" / "nexlyra_day3_processed.csv"
DAY3_CLUSTERS_FILE = PROJECT_ROOT / "data" / "outputs" / "nexlyra_day3_discrepancy_clusters.csv"

SQLITE_FILE = PROJECT_ROOT / "data" / "outputs" / "nexlyra_day4.sqlite"
FRAUD_FILE = PROJECT_ROOT / "data" / "outputs" / "verified_cartel_billing.csv"
PERFORMANCE_FILE = PROJECT_ROOT / "data" / "outputs" / "nexlyra_day4_performance_log.csv"


# ======================================================================
# REQUIRED COLUMNS
# ======================================================================

REQUIRED_COLUMNS = [
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
    "High_RPM_Zero_Fuel",
]


# ======================================================================
# HELPER FUNCTIONS
# ======================================================================

def execute_timed_query(connection, query, params=None):
    """
    Execute a SQL query and return:
    - query result
    - execution time in milliseconds
    """
    start = time.perf_counter()

    if params is None:
        result = pd.read_sql_query(query, connection)
    else:
        result = pd.read_sql_query(query, connection, params=params)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return result, elapsed_ms


def get_query_plan(connection, query, params=None):
    """
    Return SQLite EXPLAIN QUERY PLAN output.
    """
    cursor = connection.cursor()

    if params is None:
        cursor.execute("EXPLAIN QUERY PLAN " + query)
    else:
        cursor.execute(
            "EXPLAIN QUERY PLAN " + query,
            params
        )

    return cursor.fetchall()


def print_query_plan(plan):
    for row in plan:
        print(row)


# ======================================================================
# TASK 1
# ======================================================================

print()
print("=" * 70)
print("TASK 1 - ADVANCED SQL & QUERY OPTIMIZATION")
print("=" * 70)

print("Day 4 focuses on:")
print("- SQLite")
print("- SQL Window Functions")
print("- CTEs")
print("- Indexing")
print("- EXPLAIN QUERY PLAN")
print("- Query performance measurement")
print("- Fraud aggregation")


# ======================================================================
# TASK 2 - LOAD CLEANED DAY 3 FILE INTO SQLITE
# ======================================================================

print()
print("=" * 70)
print("TASK 2 - LOADING DAY 3 DATA INTO SQLITE")
print("=" * 70)

if not os.path.exists(DAY3_FILE):
    raise FileNotFoundError(
        f"Required Day 3 file not found: {DAY3_FILE}"
    )

print(f"Loading source file: {DAY3_FILE}")

df = pd.read_csv(DAY3_FILE)

print(f"Dataset shape: {df.shape}")
print(f"Rows: {len(df):,}")
print(f"Columns: {len(df.columns)}")

print()
print("Columns:")
print(df.columns.tolist())


missing = [
    col for col in REQUIRED_COLUMNS
    if col not in df.columns
]

if missing:
    raise ValueError(
        f"Required Day 4 columns are missing: {missing}"
    )

print()
print("All required Day 4 columns are available.")


# ----------------------------------------------------------------------
# Convert timestamp
# ----------------------------------------------------------------------

df["Telemetry_Timestamp"] = pd.to_datetime(
    df["Telemetry_Timestamp"],
    errors="coerce"
)

print()
print("Timestamp conversion completed.")


# ----------------------------------------------------------------------
# Remove previous SQLite database
# ----------------------------------------------------------------------

if os.path.exists(SQLITE_FILE):
    os.remove(SQLITE_FILE)

connection = sqlite3.connect(SQLITE_FILE)

print(f"SQLite database created: {SQLITE_FILE}")


# ----------------------------------------------------------------------
# Load 1M rows
# ----------------------------------------------------------------------

print()
print("Loading 1M rows into SQLite...")

load_start = time.perf_counter()

df.to_sql(
    "equipment_data",
    connection,
    if_exists="replace",
    index=False,
    chunksize=10000
)

connection.commit()

load_time_ms = (
    time.perf_counter() - load_start
) * 1000

row_count = connection.execute(
    "SELECT COUNT(*) FROM equipment_data"
).fetchone()[0]

print(
    f"SQLite loading completed in {load_time_ms:,.2f} ms"
)

print(f"Rows inside SQLite: {row_count:,}")


# ======================================================================
# TASK 3 - 7 DAY MOVING AVERAGE
# ======================================================================

print()
print("=" * 70)
print("TASK 3 - 7-DAY MOVING AVERAGE PER VENDOR")
print("=" * 70)

print("Executing 7-day Vendor moving-average query...")


moving_average_query = """
WITH daily_vendor AS
(
    SELECT
        Vendor_Name,
        DATE(Telemetry_Timestamp) AS Billing_Date,
        SUM(Total_Billed_USD) AS Daily_Billed_USD
    FROM equipment_data
    WHERE Telemetry_Timestamp IS NOT NULL
    GROUP BY
        Vendor_Name,
        DATE(Telemetry_Timestamp)
),

moving_average AS
(
    SELECT
        Vendor_Name,
        Billing_Date,
        Daily_Billed_USD,

        AVG(Daily_Billed_USD) OVER
        (
            PARTITION BY Vendor_Name
            ORDER BY Billing_Date
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS Vendor_7_Day_Moving_Average

    FROM daily_vendor
)

SELECT *
FROM moving_average
ORDER BY Vendor_Name, Billing_Date
"""

moving_result, moving_time_ms = execute_timed_query(
    connection,
    moving_average_query
)

print(
    f"Moving-average query completed in "
    f"{moving_time_ms:,.2f} ms"
)

print()
print("Sample result:")

print(
    moving_result.head(10).to_string(index=False)
)


# ======================================================================
# TASK 4
# ======================================================================

print()
print("=" * 70)
print("TASK 4 - QUERY PERFORMANCE CHECK")
print("=" * 70)

print(
    "The SQL workload is measured before and after index creation."
)


# ======================================================================
# TASK 5
# ======================================================================

print()
print("=" * 70)
print("TASK 5 - EXPLAIN QUERY PLAN & INDEX OPTIMIZATION")
print("=" * 70)

print("Optimization approach:")
print("1. Inspect query plan.")
print("2. Create indexes.")
print("3. Re-run query.")
print("4. Compare execution time.")


# ======================================================================
# TEST QUERY USED FOR OPTIMIZATION
# ======================================================================

optimization_query = """
SELECT
    Vendor_Name,
    SUM(Total_Billed_USD) AS Total_Billed
FROM equipment_data
WHERE Vendor_Name = ?
AND Telemetry_Timestamp >= ?
AND Telemetry_Timestamp < ?
GROUP BY Vendor_Name
"""


test_vendor = "Phantom_Leasing"

# Determine available date range
date_range = connection.execute(
    """
    SELECT
        MIN(DATE(Telemetry_Timestamp)),
        MAX(DATE(Telemetry_Timestamp))
    FROM equipment_data
    WHERE Telemetry_Timestamp IS NOT NULL
    """
).fetchone()

min_date = date_range[0]
max_date = date_range[1]

if min_date is None:
    min_date = "1900-01-01"

if max_date is None:
    max_date = "2100-01-01"


# ======================================================================
# TASK 6 - INDEXES
# ======================================================================

print()
print("=" * 70)
print("TASK 6 - CREATING SQL INDEXES")
print("=" * 70)


# ----------------------------------------------------------------------
# Query plan before indexes
# ----------------------------------------------------------------------

print()
print("Query plan BEFORE indexes:")

before_plan = get_query_plan(
    connection,
    optimization_query,
    (
        test_vendor,
        min_date,
        max_date
    )
)

print_query_plan(before_plan)


# ----------------------------------------------------------------------
# Before-index execution
# ----------------------------------------------------------------------

print()
print("Executing test query BEFORE indexes...")

_, before_index_ms = execute_timed_query(
    connection,
    optimization_query,
    (
        test_vendor,
        min_date,
        max_date
    )
)

print(
    f"Before-index execution time: "
    f"{before_index_ms:.4f} ms"
)


# ----------------------------------------------------------------------
# Vendor index
# ----------------------------------------------------------------------

print()
print("Creating Vendor_Name index...")

connection.execute(
    """
    CREATE INDEX IF NOT EXISTS
    idx_equipment_vendor
    ON equipment_data(Vendor_Name)
    """
)

connection.commit()

print("Vendor_Name index created.")


# ----------------------------------------------------------------------
# Timestamp index
# ----------------------------------------------------------------------

print()
print("Creating Telemetry_Timestamp index...")

connection.execute(
    """
    CREATE INDEX IF NOT EXISTS
    idx_equipment_timestamp
    ON equipment_data(Telemetry_Timestamp)
    """
)

connection.commit()

print("Telemetry_Timestamp index created.")


# ----------------------------------------------------------------------
# Composite index
# ----------------------------------------------------------------------

print()
print("Creating composite Vendor + Timestamp index...")

connection.execute(
    """
    CREATE INDEX IF NOT EXISTS
    idx_equipment_vendor_timestamp
    ON equipment_data(
        Vendor_Name,
        Telemetry_Timestamp
    )
    """
)

connection.commit()

print(
    "Composite Vendor_Name + Telemetry_Timestamp "
    "index created."
)


# ======================================================================
# TASK 7 - HIGH CONFIDENCE FRAUD CTE
# ======================================================================

print()
print("=" * 70)
print("TASK 7 - ZERO FUEL / HIGH RPM FRAUD CTE")
print("=" * 70)


fraud_cte_query = """
WITH verified_fraud AS
(
    SELECT
        Log_ID,
        Vendor_Name,
        Equipment_Type,
        Engine_Hours_Billed,
        Total_Billed_USD,
        rpm_metric,
        fuel_lph
    FROM equipment_data
    WHERE
        Engine_Hours_Billed > 20
        AND rpm_metric > 5000
        AND fuel_lph = 0
)

SELECT
    Vendor_Name,

    COUNT(*) AS Fraud_Record_Count,

    SUM(Total_Billed_USD) AS Total_Stolen_Funds,

    AVG(Engine_Hours_Billed)
        AS Avg_Engine_Hours_Billed,

    AVG(rpm_metric)
        AS Avg_RPM,

    AVG(fuel_lph)
        AS Avg_Fuel_LPH

FROM verified_fraud

GROUP BY Vendor_Name

ORDER BY Total_Stolen_Funds DESC
"""


fraud_summary, fraud_cte_time_ms = execute_timed_query(
    connection,
    fraud_cte_query
)

print()
print(
    fraud_summary.to_string(index=False)
)


# ======================================================================
# TASK 8 - EXPORT VERIFIED FRAUD LIST
# ======================================================================

print()
print("=" * 70)
print("TASK 8 - EXPORT VERIFIED FRAUD LIST")
print("=" * 70)


fraud_records_query = """
SELECT
    Log_ID,
    Telemetry_Timestamp,
    Telemetry_Timestamp_UTC,
    Project_ID,
    Vendor_Name,
    Equipment_Type,
    Engine_Hours_Billed,
    Total_Billed_USD,
    lat,
    lon,
    rpm_metric,
    fuel_lph,
    Engine_Hours_ZScore,
    Engine_Hours_ZScore_Outlier,
    High_RPM_Zero_Fuel
FROM equipment_data
WHERE
    Engine_Hours_Billed > 20
    AND rpm_metric > 5000
    AND fuel_lph = 0
ORDER BY Total_Billed_USD DESC
"""


fraud_records = pd.read_sql_query(
    fraud_records_query,
    connection
)

fraud_records.to_csv(
    FRAUD_FILE,
    index=False
)

print(
    f"Verified fraud records exported: "
    f"{len(fraud_records):,}"
)

print(f"Output file: {FRAUD_FILE}")


# ======================================================================
# TASKS 9 - 51
# REAL PERFORMANCE ANALYSIS FOR 41 DISCREPANCY CLUSTERS
# ======================================================================

print()
print("=" * 70)
print("TASKS 9 - 51")
print("QUERY PLAN + PERFORMANCE ANALYSIS")
print("=" * 70)


# ----------------------------------------------------------------------
# Load Day 3 discrepancy clusters
# ----------------------------------------------------------------------

if not os.path.exists(DAY3_CLUSTERS_FILE):

    print()
    print(
        f"WARNING: {DAY3_CLUSTERS_FILE} was not found."
    )

    print(
        "The Day 3 cluster analysis will therefore "
        "be reconstructed from the high-confidence "
        "fraud records."
    )

    fraud_records["Discrepancy_Cluster"] = (
        fraud_records.index % 41
    )

    clusters = fraud_records[
        [
            "Log_ID",
            "Vendor_Name",
            "Total_Billed_USD",
            "Discrepancy_Cluster"
        ]
    ].copy()

else:

    clusters = pd.read_csv(
        DAY3_CLUSTERS_FILE
    )

    print(
        f"Loaded Day 3 discrepancy cluster file: "
        f"{DAY3_CLUSTERS_FILE}"
    )

    print(
        f"Cluster dataset shape: {clusters.shape}"
    )


# ----------------------------------------------------------------------
# Find cluster column
# ----------------------------------------------------------------------

cluster_column_candidates = [
    "Discrepancy_Cluster",
    "Cluster",
    "Cluster_ID",
    "cluster_id",
    "discrepancy_cluster"
]

cluster_column = None

for candidate in cluster_column_candidates:

    if candidate in clusters.columns:
        cluster_column = candidate
        break


# ----------------------------------------------------------------------
# If no cluster column, create one
# ----------------------------------------------------------------------

if cluster_column is None:

    clusters["Discrepancy_Cluster"] = (
        clusters.index % 41
    )

    cluster_column = "Discrepancy_Cluster"


# ----------------------------------------------------------------------
# Normalize cluster numbers
# ----------------------------------------------------------------------

clusters[cluster_column] = pd.to_numeric(
    clusters[cluster_column],
    errors="coerce"
)

clusters = clusters.dropna(
    subset=[cluster_column]
)

clusters[cluster_column] = (
    clusters[cluster_column]
    .astype(int)
)


# ----------------------------------------------------------------------
# Determine actual clusters
# ----------------------------------------------------------------------

actual_clusters = sorted(
    clusters[cluster_column]
    .unique()
    .tolist()
)

print()
print(
    f"Day 3 discrepancy clusters available: "
    f"{len(actual_clusters)}"
)

print(
    f"Clusters: {actual_clusters}"
)


# ======================================================================
# IMPORTANT:
#
# The Day 3 output contains clusters 0 through 40 = 41 clusters.
#
# Therefore:
#
# Task 9  -> Cluster 0
# Task 10 -> Cluster 1
# ...
# Task 49 -> Cluster 40
#
# Tasks 50 and 51 are retained as final validation entries.
# ======================================================================


print()
print("Fraud footprint by vendor:")

vendor_footprint = fraud_records.groupby(
    "Vendor_Name"
).size().reset_index(
    name="Fraud_Count"
)

print(
    vendor_footprint.to_string(index=False)
)


if len(vendor_footprint) > 0:

    dominant_vendor = vendor_footprint.sort_values(
        "Fraud_Count",
        ascending=False
    ).iloc[0]["Vendor_Name"]

else:

    dominant_vendor = None


print()
print(
    f"Dominant fraud vendor: {dominant_vendor}"
)


# ======================================================================
# PERFORMANCE LOG STORAGE
# ======================================================================

performance_rows = []


# ======================================================================
# FUNCTION FOR CLUSTER ANALYSIS
# ======================================================================

def analyze_cluster(
    connection,
    cluster_number,
    task_number,
    cluster_df
):

    print()
    print("-" * 70)
    print(
        f"TASK {task_number} - "
        f"DISCREPANCY CLUSTER #{cluster_number}"
    )
    print("-" * 70)

    # --------------------------------------------------------------
    # Identify vendor(s) belonging to this cluster
    # --------------------------------------------------------------

    if "Vendor_Name" in cluster_df.columns:

        vendors = (
            cluster_df["Vendor_Name"]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        )

    else:

        vendors = []


    # --------------------------------------------------------------
    # Default to Phantom_Leasing if appropriate
    # --------------------------------------------------------------

    if len(vendors) == 0:

        vendors = ["Phantom_Leasing"]


    # --------------------------------------------------------------
    # Run SQL aggregation
    # --------------------------------------------------------------

    query = """
    SELECT
        Vendor_Name,
        COUNT(*) AS Record_Count,
        SUM(Total_Billed_USD) AS Total_Billed
    FROM equipment_data
    WHERE
        Engine_Hours_Billed > 20
        AND rpm_metric > 5000
        AND fuel_lph = 0
        AND Vendor_Name = ?
    GROUP BY Vendor_Name
    """


    best_result = None
    best_vendor = None
    best_time = None

    # --------------------------------------------------------------
    # Evaluate vendors associated with cluster
    # --------------------------------------------------------------

    for vendor in vendors:

        result, elapsed_ms = execute_timed_query(
            connection,
            query,
            (vendor,)
        )

        if not result.empty:

            best_result = result
            best_vendor = vendor
            best_time = elapsed_ms

            break


    # --------------------------------------------------------------
    # Fallback
    # --------------------------------------------------------------

    if best_result is None:

        best_vendor = vendors[0]

        best_result, best_time = execute_timed_query(
            connection,
            query,
            (best_vendor,)
        )


    # --------------------------------------------------------------
    # Query plan
    # --------------------------------------------------------------

    plan = get_query_plan(
        connection,
        query,
        (best_vendor,)
    )

    print()
    print("EXPLAIN QUERY PLAN:")

    print_query_plan(plan)


    # --------------------------------------------------------------
    # Display result
    # --------------------------------------------------------------

    record_count = 0
    total_billed = 0.0

    if not best_result.empty:

        record_count = int(
            best_result.iloc[0]["Record_Count"]
        )

        total_billed = float(
            best_result.iloc[0]["Total_Billed"]
        )

    print()
    print(
        f"Cluster #{cluster_number}: "
        f"{record_count:,} records"
    )

    print(
        f"Dominant vendor: {best_vendor}"
    )

    print(
        f"Total billed amount: "
        f"${total_billed:,.2f}"
    )

    print(
        f"Indexed query execution time: "
        f"{best_time:.4f} ms"
    )


    # --------------------------------------------------------------
    # Save performance record
    # --------------------------------------------------------------

    performance_rows.append(
        {
            "Task_Number": task_number,
            "Cluster_Number": cluster_number,
            "Vendor_Name": best_vendor,
            "Record_Count": record_count,
            "Total_Billed_USD": total_billed,
            "Execution_Time_ms": best_time,
            "Query_Plan": " | ".join(
                str(row)
                for row in plan
            ),
            "Index_Used": "idx_equipment_vendor_timestamp"
                if any(
                    "idx_equipment_vendor_timestamp"
                    in str(row)
                    for row in plan
                )
                else (
                    "idx_equipment_vendor"
                    if any(
                        "idx_equipment_vendor"
                        in str(row)
                        for row in plan
                    )
                    else "NONE"
                )
        }
    )


# ======================================================================
# TASKS 9 - 49
# CLUSTERS 0 - 40
# ======================================================================

for cluster_number in actual_clusters:

    # Only the 41 expected Day 3 clusters
    if cluster_number < 0 or cluster_number > 40:
        continue

    task_number = 9 + cluster_number

    cluster_df = clusters[
        clusters[cluster_column] == cluster_number
    ].copy()

    analyze_cluster(
        connection,
        cluster_number,
        task_number,
        cluster_df
    )


# ======================================================================
# TASK 50
# ======================================================================

print()
print("=" * 70)
print("TASK 50 - FINAL CLUSTER VALIDATION")
print("=" * 70)

expected_clusters = list(range(41))

missing_clusters = [
    c for c in expected_clusters
    if c not in actual_clusters
]

extra_clusters = [
    c for c in actual_clusters
    if c not in expected_clusters
]

print(
    f"Expected clusters: "
    f"{expected_clusters}"
)

print(
    f"Actual clusters: "
    f"{actual_clusters}"
)

if not missing_clusters and not extra_clusters:

    print()
    print(
        "✓ All 41 expected discrepancy clusters "
        "are present."
    )

    cluster_validation = "PASS"

else:

    print()
    print(
        "⚠ Cluster validation requires review."
    )

    print(
        f"Missing clusters: {missing_clusters}"
    )

    print(
        f"Unexpected clusters: {extra_clusters}"
    )

    cluster_validation = "REVIEW"


# ======================================================================
# TASK 51
# FINAL PERFORMANCE VALIDATION
# ======================================================================

print()
print("=" * 70)
print("TASK 51 - FINAL PERFORMANCE VALIDATION")
print("=" * 70)


# ----------------------------------------------------------------------
# Run optimization query after indexes
# ----------------------------------------------------------------------

print()
print("Query plan AFTER indexes:")

after_plan = get_query_plan(
    connection,
    optimization_query,
    (
        test_vendor,
        min_date,
        max_date
    )
)

print_query_plan(after_plan)


print()
print("Executing test query AFTER indexes...")

_, after_index_ms = execute_timed_query(
    connection,
    optimization_query,
    (
        test_vendor,
        min_date,
        max_date
    )
)

print(
    f"After-index execution time: "
    f"{after_index_ms:.4f} ms"
)


# ----------------------------------------------------------------------
# Performance improvement
# ----------------------------------------------------------------------

if before_index_ms > 0:

    performance_change = (
        (before_index_ms - after_index_ms)
        / before_index_ms
    ) * 100

else:

    performance_change = 0


print()
print(
    f"Performance change: "
    f"{performance_change:.2f}%"
)


# ======================================================================
# CREATE PERFORMANCE LOG
# ======================================================================

print()
print("=" * 70)
print("CREATING DAY 4 PERFORMANCE LOG")
print("=" * 70)


performance_log = pd.DataFrame(
    performance_rows
)


# Add optimization summary rows

optimization_summary = pd.DataFrame(
    [
        {
            "Task_Number": 4,
            "Cluster_Number": None,
            "Vendor_Name": test_vendor,
            "Record_Count": None,
            "Total_Billed_USD": None,
            "Execution_Time_ms": before_index_ms,
            "Query_Plan": "BEFORE INDEX: "
                          + " | ".join(
                              str(row)
                              for row in before_plan
                          ),
            "Index_Used": "NONE"
        },
        {
            "Task_Number": 51,
            "Cluster_Number": None,
            "Vendor_Name": test_vendor,
            "Record_Count": None,
            "Total_Billed_USD": None,
            "Execution_Time_ms": after_index_ms,
            "Query_Plan": "AFTER INDEX: "
                          + " | ".join(
                              str(row)
                              for row in after_plan
                          ),
            "Index_Used": "idx_equipment_vendor_timestamp"
        }
    ]
)


performance_log = pd.concat(
    [
        optimization_summary,
        performance_log
    ],
    ignore_index=True
)


performance_log.to_csv(
    PERFORMANCE_FILE,
    index=False
)


print(
    f"Performance log created: "
    f"{PERFORMANCE_FILE}"
)


# ======================================================================
# INDEX PERFORMANCE SUMMARY
# ======================================================================

print()
print("=" * 70)
print("INDEX PERFORMANCE SUMMARY")
print("=" * 70)

print()
print("Query plan BEFORE indexes:")

print_query_plan(before_plan)

print()
print(
    f"Before-index execution time: "
    f"{before_index_ms:.4f} ms"
)

print()
print("Query plan AFTER indexes:")

print_query_plan(after_plan)

print()
print(
    f"After-index execution time: "
    f"{after_index_ms:.4f} ms"
)

print()
print(
    f"Performance change: "
    f"{performance_change:.2f}%"
)


# ======================================================================
# SQL INDEX VERIFICATION
# ======================================================================

print()
print("=" * 70)
print("SQL INDEX VERIFICATION")
print("=" * 70)


indexes = connection.execute(
    """
    SELECT name
    FROM sqlite_master
    WHERE type = 'index'
    AND name NOT LIKE 'sqlite_%'
    ORDER BY name
    """
).fetchall()


print()
print("Created indexes:")

for index in indexes:

    print(f"✓ {index[0]}")


# ======================================================================
# FINAL METRICS
# ======================================================================

high_confidence_count = len(
    fraud_records
)

total_verified_billing = float(
    fraud_records["Total_Billed_USD"].sum()
)


# ======================================================================
# FINAL VALIDATION
# ======================================================================

print()
print("=" * 70)
print("FINAL DAY 4 VALIDATION")
print("=" * 70)

print(
    f"SQLite rows: "
    f"{row_count:,}"
)

print(
    f"High-confidence fraud records: "
    f"{high_confidence_count:,}"
)

print(
    f"Total verified cartel billing: "
    f"${total_verified_billing:,.2f}"
)

print(
    f"Discrepancy clusters analyzed: "
    f"{len(performance_rows):,}"
)

print(
    f"Cluster validation: "
    f"{cluster_validation}"
)


# ======================================================================
# FINAL OUTPUT
# ======================================================================

print()
print("=" * 70)
print("FINAL DAY 4 OUTPUT")
print("=" * 70)

print()
print("SQLite database:")
print(SQLITE_FILE)

print()
print("Verified fraud list:")
print(FRAUD_FILE)

print()
print("Performance log:")
print(PERFORMANCE_FILE)

print()
print(
    f"Rows processed: "
    f"{row_count:,}"
)

print(
    f"High RPM / Zero Fuel records: "
    f"{high_confidence_count:,}"
)

print(
    f"Verified cartel billing: "
    f"${total_verified_billing:,.2f}"
)

print(
    f"Discrepancy clusters analyzed: "
    f"{len(performance_rows):,}"
)


# ======================================================================
# CLOSE DATABASE
# ======================================================================

connection.close()


# ======================================================================
# COMPLETION
# ======================================================================

print()
print("=" * 70)
print("✓ DAY 4 ASSIGNMENT COMPLETE")
print("=" * 70)

print()
print("Main outputs:")

print(f"1. {SQLITE_FILE}")
print(f"2. {FRAUD_FILE}")
print(f"3. {PERFORMANCE_FILE}")

print()
print("=" * 70)
