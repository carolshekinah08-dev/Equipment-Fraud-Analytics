# Nexlyra Equipment Fraud Detection

## Purpose

This project investigates equipment-billing risk by reconciling invoice-related engine hours with nested IoT telemetry. The Day 6 delivery adds a logged OOP cleaning pipeline, forensic reporting, technical-resolution documentation, and an organized project structure while retaining the original Days 1-5 work.

## Forensic finding

**The Cartel Forgot to Spoof the Fuel Data.** The documented rule `Engine_Hours_Billed > 20 AND rpm_metric > 5000 AND fuel_lph = 0` identifies 51,920 high-confidence fraud indicators (5.192% of the 1,000,000 rows). All are associated with `Phantom_Leasing`, with $391,714,327.77 in associated billing. The Power BI matrix documented `Phantom_Leasing` at 40.84% fraudulent billing. These are investigation findings, not a legal conclusion of fraud.

## Dataset and approach

- Raw source: 1,000,000 equipment telemetry and billing records, including nested JSON, stored in `data/raw/`.
- Day 1: chunked JSON extraction and memory profiling.
- Day 2: vectorized currency conversion, explicit UTC normalization, and hex GPS decoding.
- Day 3: grouped Z-score assessment plus the high-RPM/zero-fuel logical rule and vendor clustering.
- Day 4: SQLite fraud verification, CTE analysis, and index/query-plan review.
- Day 5: Power BI DAX, the RPM-vs-fuel scatter plot, and a vendor fraud-percentage matrix.
- Day 6: `DataCleaner`, structured logging, final reporting, and delivery organization.

## Run the production pipeline

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

The pipeline intentionally refuses to replace an existing processed output unless `--overwrite` is supplied:

```powershell
python python/pipeline/production_pipeline.py --overwrite
```

It reads the raw CSV in 100,000-row chunks, logs pipeline start/loading/row-level chunk stages/errors/completion to `logs/nexlyra_pipeline.log`, and writes the historical Day 2-compatible output to `data/processed/nexlyra_day2_processed.csv`. A compact execution summary is written to `data/outputs/day6_pipeline_summary.json`.

The original educational Day 1-4 scripts are retained under `python/scripts/` and now resolve their inputs and outputs from the project root. Their narrative `print()` calls remain intentionally as historical task evidence; the Day 6 production pipeline uses `logging` rather than prints.

## Important deliverables

- `python/pipeline/production_pipeline.py` - logged OOP pipeline and `DataCleaner` class.
- `sql/day4_fraud_queries.sql` - retained fraud-rule and indexing SQL.
- `data/outputs/verified_cartel_billing.csv` - Day 4 verified high-confidence population.
- `reports/forensic_audit_report/forensic_audit_report.pdf` - final three-page audit report.
- `reports/documentation/technical_problems_and_resolutions.md` - evidence-backed technical history.
- `reports/documentation/day1_to_day5_working_notes.pdf` - supplied Day 1-5 notes preserved in the project.

## Folder structure

```text
Project 3/
├── data/
│   ├── raw/                 # original 1M-row input
│   ├── processed/           # Day 1-3 processed datasets
│   └── outputs/             # validation, clusters, SQLite, fraud evidence
├── python/
│   ├── pipeline/            # Day 6 production code
│   ├── scripts/             # preserved Day 1-4 scripts
│   └── utils/
├── sql/
├── powerbi/
│   └── pdf/                 # no Power BI PDF export was provided
├── reports/
│   ├── forensic_audit_report/
│   └── documentation/
├── logs/
├── Nexlyra_EQUIPMENT_FRAUD_pbix.pbix
├── requirements.txt
└── README.md
```


