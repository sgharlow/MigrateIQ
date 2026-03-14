-- Translated from MSSQL to PostgreSQL by MigrateIQ

-- NOTE: MSSQL table types with MEMORY_OPTIMIZED = ON have no PostgreSQL equivalent.
-- In PostgreSQL, composite types cannot have constraints or indexes.
-- Consider using a temporary table if PRIMARY KEY behavior is needed.

CREATE TYPE website.order_list AS (
    order_reference              INT,
    customer_id                  INT,
    contact_person_id            INT,
    expected_delivery_date       DATE,
    customer_purchase_order_number VARCHAR(20),
    is_undersupply_backordered   BOOLEAN,
    comments                     TEXT,
    delivery_instructions        TEXT
);
