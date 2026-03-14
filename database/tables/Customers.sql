-- Translated from MSSQL to PostgreSQL by MigrateIQ

-- Requires PostGIS extension for geography type
CREATE EXTENSION IF NOT EXISTS postgis;

-- TEMPORAL TABLE NOTE: MSSQL uses native system-versioned temporal tables.
-- PostgreSQL approach: Use temporal_tables extension or implement via triggers.
-- The ValidFrom/ValidTo columns are preserved for manual temporal implementation.
-- Original history table: Sales.Customers_Archive

CREATE TABLE sales.customers (
    customer_id                  INT             NOT NULL DEFAULT nextval('sequences.customerid'),
    customer_name                VARCHAR(100)    NOT NULL,
    bill_to_customer_id          INT             NOT NULL,
    customer_category_id         INT             NOT NULL,
    buying_group_id              INT             NULL,
    primary_contact_person_id    INT             NOT NULL,
    alternate_contact_person_id  INT             NULL,
    delivery_method_id           INT             NOT NULL,
    delivery_city_id             INT             NOT NULL,
    postal_city_id               INT             NOT NULL,
    credit_limit                 DECIMAL(18, 2)  NULL,
    account_opened_date          DATE            NOT NULL,
    standard_discount_percentage DECIMAL(18, 3)  NOT NULL,
    is_statement_sent            BOOLEAN         NOT NULL,
    is_on_credit_hold            BOOLEAN         NOT NULL,
    payment_days                 INT             NOT NULL,
    phone_number                 VARCHAR(20)     NOT NULL,
    fax_number                   VARCHAR(20)     NOT NULL,
    delivery_run                 VARCHAR(5)      NULL,
    run_position                 VARCHAR(5)      NULL,
    website_url                  VARCHAR(256)    NOT NULL,
    delivery_address_line1       VARCHAR(60)     NOT NULL,
    delivery_address_line2       VARCHAR(60)     NULL,
    delivery_postal_code         VARCHAR(10)     NOT NULL,
    delivery_location            geography       NULL,
    postal_address_line1         VARCHAR(60)     NOT NULL,
    postal_address_line2         VARCHAR(60)     NULL,
    postal_postal_code           VARCHAR(10)     NOT NULL,
    last_edited_by               INT             NOT NULL,
    valid_from                   TIMESTAMP       NOT NULL DEFAULT now(),
    valid_to                     TIMESTAMP       NOT NULL DEFAULT '9999-12-31 23:59:59.9999999',
    CONSTRAINT pk_sales_customers PRIMARY KEY (customer_id),
    CONSTRAINT fk_sales_customers_alternatecontactpersonid_application_people FOREIGN KEY (alternate_contact_person_id) REFERENCES application.people (person_id),
    CONSTRAINT fk_sales_customers_application_people FOREIGN KEY (last_edited_by) REFERENCES application.people (person_id),
    CONSTRAINT fk_sales_customers_billtocustomerid_sales_customers FOREIGN KEY (bill_to_customer_id) REFERENCES sales.customers (customer_id),
    CONSTRAINT fk_sales_customers_buyinggroupid_sales_buyinggroups FOREIGN KEY (buying_group_id) REFERENCES sales.buying_groups (buying_group_id),
    CONSTRAINT fk_sales_customers_customercategoryid_sales_customercategories FOREIGN KEY (customer_category_id) REFERENCES sales.customer_categories (customer_category_id),
    CONSTRAINT fk_sales_customers_deliverycityid_application_cities FOREIGN KEY (delivery_city_id) REFERENCES application.cities (city_id),
    CONSTRAINT fk_sales_customers_deliverymethodid_application_deliverymethods FOREIGN KEY (delivery_method_id) REFERENCES application.delivery_methods (delivery_method_id),
    CONSTRAINT fk_sales_customers_postalcityid_application_cities FOREIGN KEY (postal_city_id) REFERENCES application.cities (city_id),
    CONSTRAINT fk_sales_customers_primarycontactpersonid_application_people FOREIGN KEY (primary_contact_person_id) REFERENCES application.people (person_id),
    CONSTRAINT uq_sales_customers_customername UNIQUE (customer_name)
);

CREATE INDEX fk_sales_customers_customercategoryid
    ON sales.customers (customer_category_id);

CREATE INDEX fk_sales_customers_buyinggroupid
    ON sales.customers (buying_group_id);

CREATE INDEX fk_sales_customers_primarycontactpersonid
    ON sales.customers (primary_contact_person_id);

CREATE INDEX fk_sales_customers_alternatecontactpersonid
    ON sales.customers (alternate_contact_person_id);

CREATE INDEX fk_sales_customers_deliverymethodid
    ON sales.customers (delivery_method_id);

CREATE INDEX fk_sales_customers_deliverycityid
    ON sales.customers (delivery_city_id);

CREATE INDEX fk_sales_customers_postalcityid
    ON sales.customers (postal_city_id);

CREATE INDEX ix_sales_customers_perf_20160301_06
    ON sales.customers (is_on_credit_hold, customer_id, bill_to_customer_id)
    INCLUDE (primary_contact_person_id);

COMMENT ON INDEX fk_sales_customers_customercategoryid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_sales_customers_buyinggroupid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_sales_customers_primarycontactpersonid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_sales_customers_alternatecontactpersonid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_sales_customers_deliverymethodid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_sales_customers_deliverycityid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX fk_sales_customers_postalcityid IS 'Auto-created to support a foreign key';
COMMENT ON INDEX ix_sales_customers_perf_20160301_06 IS 'Improves performance of order picking and invoicing';

COMMENT ON TABLE sales.customers IS 'Main entity tables for customers (organizations or individuals)';
COMMENT ON COLUMN sales.customers.customer_id IS 'Numeric ID used for reference to a customer within the database';
COMMENT ON COLUMN sales.customers.customer_name IS 'Customer''s full name (usually a trading name)';
COMMENT ON COLUMN sales.customers.bill_to_customer_id IS 'Customer that this is billed to (usually the same customer but can be another parent company)';
COMMENT ON COLUMN sales.customers.customer_category_id IS 'Customer''s category';
COMMENT ON COLUMN sales.customers.buying_group_id IS 'Customer''s buying group (optional)';
COMMENT ON COLUMN sales.customers.primary_contact_person_id IS 'Primary contact';
COMMENT ON COLUMN sales.customers.alternate_contact_person_id IS 'Alternate contact';
COMMENT ON COLUMN sales.customers.delivery_method_id IS 'Standard delivery method for stock items sent to this customer';
COMMENT ON COLUMN sales.customers.delivery_city_id IS 'ID of the delivery city for this address';
COMMENT ON COLUMN sales.customers.postal_city_id IS 'ID of the postal city for this address';
COMMENT ON COLUMN sales.customers.credit_limit IS 'Credit limit for this customer (NULL if unlimited)';
COMMENT ON COLUMN sales.customers.account_opened_date IS 'Date this customer account was opened';
COMMENT ON COLUMN sales.customers.standard_discount_percentage IS 'Standard discount offered to this customer';
COMMENT ON COLUMN sales.customers.is_statement_sent IS 'Is a statement sent to this customer? (Or do they just pay on each invoice?)';
COMMENT ON COLUMN sales.customers.is_on_credit_hold IS 'Is this customer on credit hold? (Prevents further deliveries to this customer)';
COMMENT ON COLUMN sales.customers.payment_days IS 'Number of days for payment of an invoice (ie payment terms)';
COMMENT ON COLUMN sales.customers.phone_number IS 'Phone number';
COMMENT ON COLUMN sales.customers.fax_number IS 'Fax number';
COMMENT ON COLUMN sales.customers.delivery_run IS 'Normal delivery run for this customer';
COMMENT ON COLUMN sales.customers.run_position IS 'Normal position in the delivery run for this customer';
COMMENT ON COLUMN sales.customers.website_url IS 'URL for the website for this customer';
COMMENT ON COLUMN sales.customers.delivery_address_line1 IS 'First delivery address line for the customer';
COMMENT ON COLUMN sales.customers.delivery_address_line2 IS 'Second delivery address line for the customer';
COMMENT ON COLUMN sales.customers.delivery_postal_code IS 'Delivery postal code for the customer';
COMMENT ON COLUMN sales.customers.delivery_location IS 'Geographic location for the customer''s office/warehouse';
COMMENT ON COLUMN sales.customers.postal_address_line1 IS 'First postal address line for the customer';
COMMENT ON COLUMN sales.customers.postal_address_line2 IS 'Second postal address line for the customer';
COMMENT ON COLUMN sales.customers.postal_postal_code IS 'Postal code for the customer when sending by mail';
