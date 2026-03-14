-- Translated from MSSQL to PostgreSQL by MigrateIQ

-- TEMPORAL TABLE NOTE: MSSQL uses native system-versioned temporal tables.
-- PostgreSQL approach: Use temporal_tables extension or implement via triggers.
-- The ValidFrom/ValidTo columns are preserved for manual temporal implementation.
-- Original history table: Application.People_Archive

CREATE TABLE application.people (
    person_id                INT             NOT NULL DEFAULT nextval('sequences.personid'),
    full_name                VARCHAR(50)     NOT NULL,
    preferred_name           VARCHAR(50)     NOT NULL,
    search_name              VARCHAR(101)    GENERATED ALWAYS AS (concat(preferred_name, ' ', full_name)) STORED NOT NULL,
    is_permitted_to_logon    BOOLEAN         NOT NULL,
    logon_name               VARCHAR(256)    NULL,
    is_external_logon_provider BOOLEAN       NOT NULL,
    hashed_password          BYTEA           NULL,
    is_system_user           BOOLEAN         NOT NULL,
    is_employee              BOOLEAN         NOT NULL,
    is_salesperson           BOOLEAN         NOT NULL,
    user_preferences         TEXT            NULL,
    phone_number             VARCHAR(20)     NULL,
    fax_number               VARCHAR(20)     NULL,
    email_address            VARCHAR(256)    NULL,
    photo                    BYTEA           NULL,
    custom_fields            TEXT            NULL,
    -- NOTE: OtherLanguages was a computed column using json_query(CustomFields, '$.OtherLanguages').
    -- In PostgreSQL, use a view or application logic: (custom_fields::jsonb -> 'OtherLanguages')
    -- Cannot use GENERATED ALWAYS AS with jsonb operators on a TEXT column directly.
    last_edited_by           INT             NOT NULL,
    valid_from               TIMESTAMP       NOT NULL DEFAULT now(),
    valid_to                 TIMESTAMP       NOT NULL DEFAULT '9999-12-31 23:59:59.9999999',
    CONSTRAINT pk_application_people PRIMARY KEY (person_id),
    CONSTRAINT fk_application_people_application_people FOREIGN KEY (last_edited_by) REFERENCES application.people (person_id)
);

CREATE INDEX ix_application_people_isemployee
    ON application.people (is_employee);

CREATE INDEX ix_application_people_issalesperson
    ON application.people (is_salesperson);

CREATE INDEX ix_application_people_fullname
    ON application.people (full_name);

CREATE INDEX ix_application_people_perf_20160301_05
    ON application.people (is_permitted_to_logon, person_id)
    INCLUDE (full_name, email_address);

COMMENT ON INDEX ix_application_people_isemployee IS 'Allows quickly locating employees';
COMMENT ON INDEX ix_application_people_issalesperson IS 'Allows quickly locating salespeople';
COMMENT ON INDEX ix_application_people_fullname IS 'Improves performance of name-related queries';
COMMENT ON INDEX ix_application_people_perf_20160301_05 IS 'Improves performance of order picking and invoicing';

COMMENT ON TABLE application.people IS 'People known to the application (staff, customer contacts, supplier contacts)';
COMMENT ON COLUMN application.people.person_id IS 'Numeric ID used for reference to a person within the database';
COMMENT ON COLUMN application.people.full_name IS 'Full name for this person';
COMMENT ON COLUMN application.people.preferred_name IS 'Name that this person prefers to be called';
COMMENT ON COLUMN application.people.search_name IS 'Name to build full text search on (computed column)';
COMMENT ON COLUMN application.people.is_permitted_to_logon IS 'Is this person permitted to log on?';
COMMENT ON COLUMN application.people.logon_name IS 'Person''s system logon name';
COMMENT ON COLUMN application.people.is_external_logon_provider IS 'Is logon token provided by an external system?';
COMMENT ON COLUMN application.people.hashed_password IS 'Hash of password for users without external logon tokens';
COMMENT ON COLUMN application.people.is_system_user IS 'Is the currently permitted to make online access?';
COMMENT ON COLUMN application.people.is_employee IS 'Is this person an employee?';
COMMENT ON COLUMN application.people.is_salesperson IS 'Is this person a staff salesperson?';
COMMENT ON COLUMN application.people.user_preferences IS 'User preferences related to the website (holds JSON data)';
COMMENT ON COLUMN application.people.phone_number IS 'Phone number';
COMMENT ON COLUMN application.people.fax_number IS 'Fax number';
COMMENT ON COLUMN application.people.email_address IS 'Email address for this person';
COMMENT ON COLUMN application.people.photo IS 'Photo of this person';
COMMENT ON COLUMN application.people.custom_fields IS 'Custom fields for employees and salespeople';
