# Nexlyra Equipment Fraud Detection

## Executive summary
This project reconciles equipment billing with nested IoT telemetry to identify contradictory operating states. The final rule is:

```text
Engine_Hours_Billed > 20 AND rpm_metric > 5000 AND fuel_lph = 0
```

Applied to one million rows, it flags **51,920 records** associated with **$391,714,327.77 in billed value**. Every flagged record is associated with `Phantom_Leasing`, across **41 discrepancy clusters**.

This is evidence of a billing and telemetry anomaly requiring investigation, not a legal determination that every record is proven fraud.

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

## Charts and dashboard evidence

The equipment visual evidence is delivered in the Power BI export and forensic report because this repository does not contain standalone chart image files:

- [Power BI dashboard PDF](powerbi/Nexlyra_EQUIPMENT_FRAUD_pdf.pdf)
- [Power BI dashboard workbook](powerbi/Nexlyra_EQUIPMENT_FRAUD_pbix.pbix)
- [Forensic audit report](reports/forensic_audit_report/forensic_audit_report.pdf)

## Repository contents
Raw and processed datasets, Python pipeline and scripts, SQL verification, SQLite outputs, Power BI deliverables, logs, charts, and forensic reports.
