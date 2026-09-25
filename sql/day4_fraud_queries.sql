-- Core forensic rule used to create data/outputs/verified_cartel_billing.csv
SELECT
    Log_ID,
    Vendor_Name,
    Equipment_Type,
    Engine_Hours_Billed,
    Total_Billed_USD,
    rpm_metric,
    fuel_lph
FROM equipment_data
WHERE Engine_Hours_Billed > 20
  AND rpm_metric > 5000
  AND fuel_lph = 0;

-- Vendor-level billing used for the indexed performance check.
SELECT
    Vendor_Name,
    SUM(Total_Billed_USD) AS Total_Billed
FROM equipment_data
WHERE Vendor_Name = :vendor_name
  AND Telemetry_Timestamp >= :start_date
  AND Telemetry_Timestamp < :end_date
GROUP BY Vendor_Name;

CREATE INDEX IF NOT EXISTS idx_equipment_vendor
    ON equipment_data(Vendor_Name);
CREATE INDEX IF NOT EXISTS idx_equipment_timestamp
    ON equipment_data(Telemetry_Timestamp);
CREATE INDEX IF NOT EXISTS idx_equipment_vendor_timestamp
    ON equipment_data(Vendor_Name, Telemetry_Timestamp);
