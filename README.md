# Nexlyra Equipment Fraud Detection

## Executive summary
This project reconciles equipment billing with nested IoT telemetry to identify contradictory operating states. The final rule is:

```text
Engine_Hours_Billed > 20 AND rpm_metric > 5000 AND fuel_lph = 0
```

Applied to one million rows, it flags **51,920 records** associated with **$391,714,327.77 in billed value**. Every flagged record is associated with `Phantom_Leasing`, across **41 discrepancy clusters**.

This is evidence of a billing and telemetry anomaly requiring investigation, not a legal determination that every record is proven fraud.

## Problem Statement
A vendor was suspected of spoofing Engine RPM telemetry to simulate maximum workload and justify inflated invoices — but forgot to spoof the accompanying Fuel Flow Rate, creating a physically impossible billing pattern.

## Tech Stack
Excel — Power Query, PivotTables/PivotCharts, Data Validation, VLOOKUP/INDEX-MATCH
Python — Pandas, NumPy, SciPy, Statsmodels, Scikit-learn, Matplotlib, Seaborn
SQL — SQLite (CTEs, window functions, triggers, views, indexing)
Power BI — DAX, Star Schema, Row-Level Security, What-If parameters

## Data
1,000,000 crane/excavator telemetry + billing records with fields: Log_ID, Telemetry_Date, Site_Code, Vendor, Equipment_Type, Billed_Engine_Hours, Billed_Amount_USD, IoT_Telemetry_JSON (Base64-encoded GPS + RPM + fuel).

## Methodology
|Day |	Focus	| Key Work |
|---|---:|---:|
|1 |	Excel & Power Query |	Cleaned a 50K-row subset, built a crane-rate lookup table, flagged extreme overtime, set a 95th-percentile statistical audit threshold |
|2 |Python Data Engineering	| Optimized memory 220.93MB → 87.74MB (-28% initial, -60% after JSON extraction), repaired 99,578 malformed JSON records, extracted RPM/Fuel/GPS fields |
|3 |	Cryptography & Geospatial |	Decoded all 1M Base64 GPS values (0 failures), flagged 83,371 static-GPS records |
|4 |	SQL & Relational Modeling |	Built a fact/dimension model, quarantined 83,281 fraud records, added a negative-fuel data-integrity trigger |
|5 |	Statistical Validation |	Ran a Welch t-test, OLS regression, IQR outlier detection, and Isolation Forest to stress-test the fraud rule |
|6 |	Power BI Reporting |	Star-schema dashboard, RLS by site manager, financial-impact scenario tool |

## Verified findings

| Metric | Result |
|---|---:|
| Processed records | 1,000,000 |
| High-RPM / zero-fuel records | 51,920 (5.192%) |
| Associated billed value | $391,714,327.77 |
| Discrepancy clusters | 41 |
| Dominant vendor | Phantom_Leasing |
| Valid RPM/fuel readings | 832,656 |

The suspicious cluster reports `9,999 RPM` and `0 LPH`. SQLite verification and Power BI reporting reproduce the flagged population.

## Workflow
- Process raw telemetry and billing data in chunks.
- Recover nested RPM, fuel, currency, UTC, and coordinate fields.
- Apply the contradiction rule and vendor/cluster analysis.
- Verify in SQLite with CTEs and indexed queries.
- Report amount, percentage, vendor concentration, and RPM-versus-fuel evidence in Power BI.

The production pipeline uses `DataCleaner`, explicit dtypes, guarded JSON parsing, UTC normalization, structured logging, and overwrite protection.

## Recommended actions
1. Preserve raw data, outputs, SQLite evidence, Power BI files, reports, and logs; record hashes.
2. Reconcile all flagged records to invoices, contracts, serial numbers, dispatch records, and payments.
3. Validate sensor provenance, device identity, GPS feeds, timestamps, and overrides.
4. Alert on high RPM with zero fuel and require independent evidence review.
5. Apply enhanced vendor review to `Phantom_Leasing` under applicable policy.

## Limitations
A high-RPM / zero-fuel record is a risk signal. Confirmed conclusions require invoice, contract, equipment-identity, payment, and source-system evidence.

## Power BI
<img width="1512" height="853" alt="image" src="https://github.com/user-attachments/assets/cd7810fd-e244-49d1-a146-36610bed6d2a" />
<img width="1456" height="856" alt="image" src="https://github.com/user-attachments/assets/c4367dd3-012f-4c89-87b1-3559da26fadc" />
<img width="1447" height="858" alt="image" src="https://github.com/user-attachments/assets/3c752d7d-635a-4349-a5a5-8a596470bf35" />

- [Power BI dashboard PDF](powerbi/Nexlyra_EQUIPMENT_FRAUD_pdf.pdf)
- [Power BI dashboard workbook](powerbi/Nexlyra_EQUIPMENT_FRAUD_pbix.pbix)
- [Forensic audit report](reports/forensic_audit_report/forensic_audit_report.pdf)

## Repository contents
Raw and processed datasets, Python pipeline and scripts, SQL verification, SQLite outputs, Power BI deliverables, logs, charts, and forensic reports.
