# Technical Problems and Resolutions


## Scope and evidence

This note records conditions demonstrated by the Day 1-5 scripts and their outputs.  In particular, Day 1 documents the risk of a pandas memory failure from whole-column JSON normalization; it does not contain a captured `MemoryError` traceback.

## Large dataset memory pressure

**Cause.** The source CSV has 1,000,000 rows and a nested `Nested_IoT_JSON` column. Loading the full source required a documented 275.63 MB baseline. Applying `pd.json_normalize()` across that column would construct large intermediate Python objects and a wide dataframe, increasing peak memory pressure.

**Resolution.** Day 1 tested normalization on a five-row sample, then processed the source in 100,000-row chunks. JSON was parsed one record at a time and only the required telemetry fields were extracted. The profiling output covers 39 blocks of 25,000 rows: 6.89 MB average chunk memory and 97.50% average reduction from the baseline.

**Why it works.** Each chunk is written before the next is loaded, so memory is bounded by one chunk plus its small extraction structures rather than the entire source plus a fully normalized copy. The Day 6 `DataCleaner` retains this bounded-chunk design.

## Missing nested JSON keys

**Cause.** Some telemetry JSON records lack an `engine` block. Day 1 intentionally demonstrated the resulting `KeyError` from direct dictionary access.

**Resolution.** The existing scripts use `.get()` with safe defaults; the Day 6 `DataCleaner._parse_json()` rejects missing or malformed values and `extract_gps_hex()` returns null components when keys are absent.

**Why it works.** Missing telemetry becomes a null value instead of terminating a 1M-row run. This preserves record counts and keeps the absence visible for later analysis.

## Currency dtype cleaning and chained assignment risk

**Cause.** `Total_Billed_USD` was an object column containing currency strings such as `$3,305.45`. Day 2 demonstrated that chained assignment can be ambiguous (`SettingWithCopyWarning`). The documentation states that the installed pandas version did not actually emit the warning during the demonstration.

**Resolution.** The cleaner converts the original series with pandas `string` operations, removes `$` and commas, then uses `pd.to_numeric(..., errors="coerce").astype("float64")`. It assigns the resulting series directly to the original chunk, never through a filtered view.

**Why it works.** The conversion is vectorized, explicit about invalid values, and has a stable numeric dtype. The Day 2 output recorded zero missing values after conversion.

## Mixed timezone formats

**Cause.** Day 2 found 499,957 Z-terminated UTC values and 500,043 timezone-naive values. The dataset contains no timezone identifier for the naive records, so they cannot be converted from an asserted local zone without inventing evidence.

**Resolution.** The project explicitly interprets naive timestamps as UTC and uses `pd.to_datetime(..., format="mixed", utc=True, errors="coerce")`, storing the normalized result in `Telemetry_Timestamp_UTC`.

**Why it works.** Every timestamp has one timezone-aware representation for temporal comparison and SQL loading. Day 2 recorded 1,000,000 valid UTC timestamps and zero invalid timestamps. The assumption is documented in code and should be revisited only if source-system timezone metadata becomes available.

## Day 3 processing overhead

**Cause.** The original Day 2 processed file intentionally excludes engine RPM and fuel. Day 3 reloads the raw source for those two fields and merges them by `Log_ID`, which is appropriate for the historical task but adds memory pressure.

**Resolution.** The refactored cleaner extracts only the fields required for cleaning within the incoming chunk and does not retain a full raw dataframe alongside a processed dataframe. Legacy Day 3 remains unchanged except for path configuration so the recorded Day 3 result is reproducible.

## Day 4 query timings

**Finding.** The performance log shows a table scan before indexes (249.0693 ms) and use of `idx_equipment_vendor_timestamp` afterward (662.6782 ms in that single recorded run). The plan changed as intended, but the sampled elapsed time did not improve.

**Resolution.** The index definitions and query-plan evidence are retained in `sql/day4_fraud_queries.sql`. No unsupported claim of speed improvement is made; timing should be benchmarked repeatedly on the target environment before treating it as an operational SLA.

## Day 6 production-grade data pipeline

"How do I use Python's logging module to replace print statements for a production-grade data pipeline?" The Day 6 implementation applies the resulting production principles: a named logger, timestamped file and console handlers, `INFO` stage/row-count messages, `ERROR` messages for rejected inputs, `logger.exception()` for processing failures, and no `print()` statements in `python/pipeline/production_pipeline.py`.