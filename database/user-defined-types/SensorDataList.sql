-- Translated from MSSQL to PostgreSQL by MigrateIQ

-- NOTE: MSSQL table types with MEMORY_OPTIMIZED = ON have no PostgreSQL equivalent.
-- In PostgreSQL, composite types do not support IDENTITY columns or constraints.
-- The IDENTITY(1,1) on SensorDataListID has been removed.
-- Consider using a temporary table with GENERATED ALWAYS AS IDENTITY if auto-increment is needed.

CREATE TYPE website.sensor_data_list AS (
    sensor_data_list_id     INT,
    cold_room_sensor_number INT,
    recorded_when           TIMESTAMP,
    temperature             DECIMAL(18, 2)
);
