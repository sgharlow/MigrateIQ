-- Translated from MSSQL to PostgreSQL by MigrateIQ

CREATE OR REPLACE PROCEDURE website.record_cold_room_temperatures(
    p_sensor_readings website.sensor_data_list[]
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_number_of_readings INT;
    v_counter INT;
    v_cold_room_sensor_number INT;
    v_recorded_when TIMESTAMP;
    v_temperature DECIMAL(18,2);
    v_row_count INT;
    v_reading website.sensor_data_list;
BEGIN
    BEGIN
        v_number_of_readings := array_length(p_sensor_readings, 1);
        v_counter := 1;

        -- note that we cannot use a merge here because multiple readings might exist for each sensor

        WHILE v_counter <= v_number_of_readings LOOP
            v_reading := p_sensor_readings[v_counter];
            v_cold_room_sensor_number := v_reading.cold_room_sensor_number;
            v_recorded_when := v_reading.recorded_when;
            v_temperature := v_reading.temperature;

            UPDATE warehouse.cold_room_temperatures
                SET recorded_when = v_recorded_when,
                    temperature = v_temperature
            WHERE cold_room_sensor_number = v_cold_room_sensor_number;

            GET DIAGNOSTICS v_row_count = ROW_COUNT;

            IF v_row_count = 0 THEN
                INSERT INTO warehouse.cold_room_temperatures
                    (cold_room_sensor_number, recorded_when, temperature)
                VALUES (v_cold_room_sensor_number, v_recorded_when, v_temperature);
            END IF;

            v_counter := v_counter + 1;
        END LOOP;

    EXCEPTION WHEN OTHERS THEN
        RAISE EXCEPTION 'Unable to apply the sensor data';
    END;
END;
$$;
