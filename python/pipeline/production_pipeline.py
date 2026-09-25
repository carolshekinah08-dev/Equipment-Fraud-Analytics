"""Memory-aware Nexlyra cleaning pipeline with structured operational logging."""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA = PROJECT_ROOT / "data" / "raw" / "nexlyra_equipment_fraud_1M_carol_reasoning.csv"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "processed" / "nexlyra_day2_processed.csv"
SUMMARY_OUTPUT = PROJECT_ROOT / "data" / "outputs" / "day6_pipeline_summary.json"
LOG_FILE = PROJECT_ROOT / "logs" / "nexlyra_pipeline.log"


@dataclass(frozen=True)
class PipelineConfig:
    input_path: Path
    output_path: Path
    chunk_size: int = 100_000


class DataCleaner:
    """Clean source telemetry in bounded chunks without full-dataframe copies."""

    required_columns = {
        "Log_ID", "Telemetry_Timestamp", "Project_ID", "Vendor_Name",
        "Equipment_Type", "Engine_Hours_Billed", "Total_Billed_USD", "Nested_IoT_JSON",
    }
    output_columns = [
        "Log_ID", "Telemetry_Timestamp", "Telemetry_Timestamp_UTC", "Project_ID",
        "Vendor_Name", "Equipment_Type", "Engine_Hours_Billed", "Total_Billed_USD",
        "lat", "lon", "lat_hex", "lon_hex",
    ]

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    @staticmethod
    def _parse_json(value: Any) -> dict[str, Any]:
        if pd.isna(value) or not str(value).strip():
            return {}
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except (JSONDecodeError, TypeError, AttributeError):
            return {}

    @classmethod
    def extract_gps_hex(cls, value: Any) -> tuple[Any, Any]:
        sensor_data = cls._parse_json(value).get("sensor_data", {})
        gps = sensor_data.get("gps_hex", {}) if isinstance(sensor_data, dict) else {}
        return gps.get("lat"), gps.get("lon")

    @staticmethod
    def decode_hex_float(value: Any) -> float:
        if pd.isna(value) or value is None:
            return np.nan
        try:
            return float(bytes.fromhex(str(value).strip()).decode("utf-8"))
        except (ValueError, TypeError, UnicodeDecodeError):
            return np.nan

    @staticmethod
    def clean_currency(values: pd.Series) -> pd.Series:
        cleaned = values.astype("string").str.replace("$", "", regex=False).str.replace(",", "", regex=False)
        return pd.to_numeric(cleaned, errors="coerce").astype("float64")

    @staticmethod
    def normalize_timestamps(values: pd.Series) -> pd.Series:
        # Naive timestamps are documented historical inputs and are interpreted as UTC.
        return pd.to_datetime(values, format="mixed", utc=True, errors="coerce")

    def clean_chunk(self, chunk: pd.DataFrame) -> pd.DataFrame:
        missing = self.required_columns.difference(chunk.columns)
        if missing:
            raise ValueError(f"Input is missing required columns: {sorted(missing)}")

        chunk["Total_Billed_USD"] = self.clean_currency(chunk["Total_Billed_USD"])
        chunk["Telemetry_Timestamp_UTC"] = self.normalize_timestamps(chunk["Telemetry_Timestamp"])
        gps = chunk["Nested_IoT_JSON"].map(self.extract_gps_hex)
        chunk["lat_hex"] = gps.map(lambda pair: pair[0]).astype("string")
        chunk["lon_hex"] = gps.map(lambda pair: pair[1]).astype("string")
        chunk["lat"] = chunk["lat_hex"].map(self.decode_hex_float).astype("float64")
        chunk["lon"] = chunk["lon_hex"].map(self.decode_hex_float).astype("float64")
        return chunk.loc[:, self.output_columns].copy()


def configure_logging() -> logging.Logger:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.FileHandler(LOG_FILE, encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )
    return logging.getLogger("nexlyra.pipeline")


def run_pipeline(config: PipelineConfig, *, overwrite: bool = False) -> dict[str, int]:
    logger = configure_logging()
    logger.info("Pipeline start. input=%s output=%s chunk_size=%s", config.input_path, config.output_path, config.chunk_size)
    if not config.input_path.is_file():
        logger.error("Input file does not exist: %s", config.input_path)
        raise FileNotFoundError(config.input_path)
    if config.output_path.exists() and not overwrite:
        logger.error("Refusing to overwrite existing output without --overwrite: %s", config.output_path)
        raise FileExistsError(config.output_path)

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    total_rows = invalid_timestamps = invalid_currency = 0
    first_chunk = True
    try:
        logger.info("Loading source data in chunks")
        for number, chunk in enumerate(pd.read_csv(config.input_path, chunksize=config.chunk_size), start=1):
            logger.info("Cleaning chunk %s with %s rows", number, len(chunk))
            cleaned = DataCleaner(logger).clean_chunk(chunk)
            invalid_timestamps += int(cleaned["Telemetry_Timestamp_UTC"].isna().sum())
            invalid_currency += int(cleaned["Total_Billed_USD"].isna().sum())
            cleaned.to_csv(config.output_path, mode="w" if first_chunk else "a", header=first_chunk, index=False)
            first_chunk = False
            total_rows += len(cleaned)
        summary = {"rows_processed": total_rows, "invalid_timestamps": invalid_timestamps, "invalid_currency": invalid_currency}
        SUMMARY_OUTPUT.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        logger.info("Pipeline completed successfully. rows=%s invalid_timestamps=%s invalid_currency=%s", total_rows, invalid_timestamps, invalid_currency)
        return summary
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        logger.exception("Pipeline failed: %s", exc)
        raise


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean Nexlyra telemetry with bounded memory use.")
    parser.add_argument("--input", type=Path, default=RAW_DATA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--chunk-size", type=int, default=100_000)
    parser.add_argument("--overwrite", action="store_true", help="Allow replacement of the output file.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    try:
        run_pipeline(PipelineConfig(args.input, args.output, args.chunk_size), overwrite=args.overwrite)
    except Exception:
        raise SystemExit(1)
