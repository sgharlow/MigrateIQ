-- Translated from MSSQL to PostgreSQL by MigrateIQ

-- Requires PostGIS extension for geography type
CREATE EXTENSION IF NOT EXISTS postgis;

-- TEMPORAL TABLE NOTE: MSSQL uses native system-versioned temporal tables.
-- PostgreSQL approach: Use temporal_tables extension or implement via triggers.
-- The ValidFrom/ValidTo columns are preserved for manual temporal implementation.
-- Original history table: Application.Cities_Archive

CREATE TABLE application.cities (
    city_id                     INT             NOT NULL DEFAULT nextval('sequences.cityid'),
    city_name                   VARCHAR(50)     NOT NULL,
    state_province_id           INT             NOT NULL,
    location                    geography       NULL,
    latest_recorded_population  BIGINT          NULL,
    last_edited_by              INT             NOT NULL,
    valid_from                  TIMESTAMP       NOT NULL DEFAULT now(),
    valid_to                    TIMESTAMP       NOT NULL DEFAULT '9999-12-31 23:59:59.9999999',
    CONSTRAINT pk_application_cities PRIMARY KEY (city_id),
    CONSTRAINT fk_application_cities_application_people FOREIGN KEY (last_edited_by) REFERENCES application.people (person_id),
    CONSTRAINT fk_application_cities_stateprovinceid_application_stateprovinces FOREIGN KEY (state_province_id) REFERENCES application.state_provinces (state_province_id)
);

CREATE INDEX fk_application_cities_stateprovinceid
    ON application.cities (state_province_id);

COMMENT ON INDEX fk_application_cities_stateprovinceid IS 'Auto-created to support a foreign key';

COMMENT ON TABLE application.cities IS 'Cities that are part of any address (including geographic location)';
COMMENT ON COLUMN application.cities.city_id IS 'Numeric ID used for reference to a city within the database';
COMMENT ON COLUMN application.cities.city_name IS 'Formal name of the city';
COMMENT ON COLUMN application.cities.state_province_id IS 'State or province for this city';
COMMENT ON COLUMN application.cities.location IS 'Geographic location of the city';
COMMENT ON COLUMN application.cities.latest_recorded_population IS 'Latest available population for the City';
