-- Translated from MSSQL to PostgreSQL by MigrateIQ

-- NOTE: MSSQL DECOMPRESS() returns VARBINARY which was cast to NVARCHAR.
-- In PostgreSQL, decompress is not a built-in function.
-- If compression is handled via pg_lz or external tools, adjust accordingly.
-- Below uses convert_from(decompress(...), 'UTF8') as a placeholder;
-- replace decompress() with your actual decompression function.

CREATE VIEW website.vehicle_temperatures
AS
SELECT vt.vehicle_temperature_id,
       vt.vehicle_registration,
       vt.chiller_sensor_number,
       vt.recorded_when,
       vt.temperature,
       CASE WHEN vt.is_compressed <> FALSE
            THEN convert_from(decompress(vt.compressed_sensor_data), 'UTF8')
            ELSE vt.full_sensor_data
       END AS full_sensor_data
FROM warehouse.vehicle_temperatures AS vt;
